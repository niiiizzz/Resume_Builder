"""
ATS (Applicant Tracking System) Score Engine — 3-Layer Hybrid Model.

Layer 1: Exact Keyword Match (40%) — lemmatized, n-gram aware
Layer 2: TF-IDF Cosine Similarity (40%) — sklearn vectorizer
Layer 3: Semantic Similarity (20%) — keyword-group vector cosine

Produces scores calibrated to realistic ATS ranges:
  75–85 = strong alignment
  60–74 = moderate
  45–59 = weak
  <45   = poor
"""

import re
import math
import logging
from collections import Counter

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Stopwords (lightweight — no NLTK data download required for these)
# ---------------------------------------------------------------------------
_STOPWORDS = frozenset({
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "shall", "can", "need", "must",
    "not", "no", "nor", "so", "if", "then", "than", "too", "very",
    "just", "about", "above", "after", "again", "all", "also", "am",
    "any", "as", "because", "before", "between", "both", "during",
    "each", "few", "further", "get", "got", "he", "her", "here", "him",
    "his", "how", "i", "into", "it", "its", "let", "me", "more", "most",
    "my", "new", "now", "of", "only", "other", "our", "out", "over",
    "own", "per", "re", "same", "she", "some", "still", "such", "that",
    "their", "them", "there", "these", "they", "this", "those", "through",
    "under", "up", "upon", "us", "use", "using", "we", "what", "when",
    "where", "which", "while", "who", "whom", "why", "with", "you",
    "your", "able", "etc", "eg", "ie", "role", "work", "working",
    "looking", "including", "within", "across", "based", "well",
    "strong", "good", "great", "like", "make", "take", "help",
})

# ---------------------------------------------------------------------------
# Lemmatizer (lazy-loaded)
# ---------------------------------------------------------------------------
_lemmatizer = None


def _get_lemmatizer():
    """Lazy-load NLTK WordNetLemmatizer, with graceful fallback."""
    global _lemmatizer
    if _lemmatizer is not None:
        return _lemmatizer
    try:
        import nltk
        # Ensure resources are available (silent if already present)
        for resource in ["wordnet", "omw-1.4"]:
            try:
                nltk.data.find(f"corpora/{resource}")
            except LookupError:
                nltk.download(resource, quiet=True)
        from nltk.stem import WordNetLemmatizer
        _lemmatizer = WordNetLemmatizer()
    except Exception as e:
        logger.warning("NLTK lemmatizer unavailable, using identity: %s", e)
        # Fallback: no-op lemmatizer
        class _Identity:
            def lemmatize(self, w, pos="n"):
                return w
        _lemmatizer = _Identity()
    return _lemmatizer


# ---------------------------------------------------------------------------
# Tokenization helpers
# ---------------------------------------------------------------------------

def _tokenize(text: str) -> list[str]:
    """Lowercase, extract alphanumeric tokens, remove stopwords."""
    text = text.lower()
    tokens = re.findall(r"[a-z][a-z0-9#+.]*", text)
    return [t for t in tokens if t not in _STOPWORDS and len(t) >= 2]


def _lemmatize_tokens(tokens: list[str]) -> list[str]:
    """Lemmatize a list of tokens (noun + verb forms)."""
    lem = _get_lemmatizer()
    result = []
    for t in tokens:
        # Try noun then verb lemmatization, pick shortest (most reduced)
        n_form = lem.lemmatize(t, pos="n")
        v_form = lem.lemmatize(t, pos="v")
        result.append(min(n_form, v_form, key=len))
    return result


def _extract_ngrams(tokens: list[str], n: int = 2) -> set[str]:
    """Extract n-gram phrases from a token list."""
    ngrams = set()
    for i in range(len(tokens) - n + 1):
        ngrams.add(" ".join(tokens[i:i + n]))
    return ngrams


def extract_keywords(text: str, include_bigrams: bool = True) -> set[str]:
    """
    Extract meaningful keywords from text.
    Returns lemmatized unigrams + optional bigrams.
    """
    raw_tokens = _tokenize(text)
    lemmatized = _lemmatize_tokens(raw_tokens)
    keywords = set(lemmatized)
    if include_bigrams and len(lemmatized) >= 2:
        keywords |= _extract_ngrams(lemmatized, 2)
    return keywords


# ---------------------------------------------------------------------------
# Layer 1: Exact Keyword Match (with partial-match bonus)
# ---------------------------------------------------------------------------

def _compute_keyword_score(resume_text: str, jd_text: str) -> dict:
    """
    Compute keyword overlap with lemmatization and partial-match support.
    Returns score (0-100) and matched/missing keyword lists.
    """
    jd_tokens = _lemmatize_tokens(_tokenize(jd_text))
    resume_tokens = _lemmatize_tokens(_tokenize(resume_text))

    jd_unigrams = set(jd_tokens)
    resume_unigrams = set(resume_tokens)

    # Bigram matching for compound terms
    jd_bigrams = _extract_ngrams(jd_tokens, 2) if len(jd_tokens) >= 2 else set()
    resume_bigrams = _extract_ngrams(resume_tokens, 2) if len(resume_tokens) >= 2 else set()

    # Unigram match
    matched_uni = jd_unigrams & resume_unigrams
    missing_uni = jd_unigrams - resume_unigrams

    # Bigram match
    matched_bi = jd_bigrams & resume_bigrams

    # Partial match: check if any missing unigram appears as a substring in resume
    partial_matches = set()
    resume_text_lower = resume_text.lower()
    for kw in list(missing_uni):
        if len(kw) >= 4 and kw in resume_text_lower:
            partial_matches.add(kw)
            missing_uni.discard(kw)

    if not jd_unigrams:
        return {"score": 0.0, "matched": [], "missing": [], "partial": []}

    # Weighted score: full match = 1.0, partial = 0.6, bigram bonus = 0.2
    full_credit = len(matched_uni) * 1.0
    partial_credit = len(partial_matches) * 0.6
    bigram_bonus = min(len(matched_bi) * 0.2, len(jd_unigrams) * 0.15)
    total_possible = len(jd_unigrams)

    score = min(((full_credit + partial_credit + bigram_bonus) / total_possible) * 100, 100.0)

    return {
        "score": round(score, 1),
        "matched": sorted(matched_uni | partial_matches),
        "missing": sorted(missing_uni),
        "partial": sorted(partial_matches),
    }


# ---------------------------------------------------------------------------
# Layer 2: TF-IDF Cosine Similarity
# ---------------------------------------------------------------------------

def _compute_tfidf_score(resume_text: str, jd_text: str) -> float:
    """Compute cosine similarity between two texts using TF-IDF. Returns 0-100."""
    try:
        vectorizer = TfidfVectorizer(
            stop_words="english",
            max_features=5000,
            ngram_range=(1, 2),
            sublinear_tf=True,
        )
        tfidf_matrix = vectorizer.fit_transform([resume_text, jd_text])
        sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        return round(float(sim) * 100, 1)
    except Exception:
        return 0.0


# ---------------------------------------------------------------------------
# Layer 3: Semantic Similarity (lightweight keyword-group cosine)
# ---------------------------------------------------------------------------

def _compute_semantic_score(resume_text: str, jd_text: str) -> float:
    """
    Lightweight semantic similarity using TF-IDF with character n-grams.
    Captures sub-word similarity without requiring a heavy embedding model.
    Returns 0-100.
    """
    try:
        vectorizer = TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(3, 5),
            max_features=8000,
            sublinear_tf=True,
        )
        matrix = vectorizer.fit_transform([resume_text, jd_text])
        sim = cosine_similarity(matrix[0:1], matrix[1:2])[0][0]
        return round(float(sim) * 100, 1)
    except Exception:
        return 0.0


# ---------------------------------------------------------------------------
# Score calibration
# ---------------------------------------------------------------------------

def _calibrate_score(raw_score: float) -> float:
    """
    Apply sigmoid-based calibration so realistic resumes score in the 65-85 range.
    Raw scores tend to cluster in 30-50; this spreads them into a human-interpretable range.
    """
    # Sigmoid centered at 45, stretched to map [20-70] → [40-90]
    k = 0.08  # steepness
    midpoint = 45.0
    # Logistic scaling
    calibrated = 100.0 / (1.0 + math.exp(-k * (raw_score - midpoint)))
    # Blend: 70% calibrated + 30% raw to maintain differentiation
    blended = (0.7 * calibrated) + (0.3 * raw_score)
    return min(round(blended, 1), 99.0)


# ---------------------------------------------------------------------------
# Category analysis (formatting, quantification, role targeting)
# ---------------------------------------------------------------------------

def _analyze_categories(resume_text: str, jd_text: str, keyword_result: dict) -> dict:
    """Generate detailed category-level analysis."""
    categories = {}

    # 1. Keyword Optimization
    kw_score = keyword_result["score"]
    categories["keyword_optimization"] = {
        "score": min(round(kw_score * 1.1, 1), 100.0),  # slight boost for display
        "label": "Keyword Optimization",
        "status": "strong" if kw_score >= 65 else "moderate" if kw_score >= 40 else "weak",
    }

    # 2. Formatting Analysis
    fmt_score = 50.0
    lines = resume_text.strip().split("\n")
    has_sections = sum(1 for l in lines if l.strip().startswith("#") or l.strip().isupper()) >= 3
    has_bullets = sum(1 for l in lines if l.strip().startswith(("-", "•", "*"))) >= 3
    has_contact = bool(re.search(r"[\w.-]+@[\w.-]+", resume_text))
    has_links = bool(re.search(r"https?://|linkedin\.com|github\.com", resume_text, re.I))

    if has_sections:
        fmt_score += 15
    if has_bullets:
        fmt_score += 15
    if has_contact:
        fmt_score += 10
    if has_links:
        fmt_score += 10

    categories["formatting"] = {
        "score": min(round(fmt_score, 1), 100.0),
        "label": "Formatting & Structure",
        "status": "strong" if fmt_score >= 70 else "moderate" if fmt_score >= 50 else "weak",
    }

    # 3. Quantification
    quant_score = 40.0
    numbers = re.findall(r"\d+[%+]?", resume_text)
    quant_count = len(numbers)
    if quant_count >= 8:
        quant_score = 90
    elif quant_count >= 5:
        quant_score = 75
    elif quant_count >= 3:
        quant_score = 60
    elif quant_count >= 1:
        quant_score = 50

    # Check for action verbs
    action_verbs = {"led", "built", "developed", "managed", "designed", "implemented",
                    "created", "improved", "increased", "reduced", "achieved", "delivered",
                    "launched", "optimized", "automated", "architected", "scaled", "drove",
                    "spearheaded", "orchestrated", "mentored", "streamlined"}
    resume_lower = resume_text.lower()
    found_verbs = sum(1 for v in action_verbs if v in resume_lower)
    if found_verbs >= 5:
        quant_score = min(quant_score + 10, 100)

    categories["quantification"] = {
        "score": round(quant_score, 1),
        "label": "Quantification & Impact",
        "status": "strong" if quant_score >= 70 else "moderate" if quant_score >= 50 else "weak",
    }

    # 4. Role Targeting
    jd_tokens_set = set(_lemmatize_tokens(_tokenize(jd_text)))
    # Check role-specific terms in first ~500 chars of resume (summary area)
    summary_area = resume_text[:500].lower()
    summary_tokens = set(_lemmatize_tokens(_tokenize(summary_area)))
    role_overlap = len(jd_tokens_set & summary_tokens) / max(len(jd_tokens_set), 1)
    role_score = min(round(role_overlap * 100 * 1.5, 1), 100.0)

    categories["role_targeting"] = {
        "score": role_score,
        "label": "Role Targeting",
        "status": "strong" if role_score >= 60 else "moderate" if role_score >= 35 else "weak",
    }

    return categories


# ---------------------------------------------------------------------------
# Suggestions generator
# ---------------------------------------------------------------------------

def _generate_suggestions(keyword_result: dict, tfidf_score: float,
                          semantic_score: float, categories: dict) -> list[str]:
    """Generate actionable, intelligent improvement suggestions."""
    suggestions = []
    kw = keyword_result

    # Keyword suggestions
    if kw["score"] < 40:
        suggestions.append(
            "⚠️ **Low keyword match.** Your resume is missing many critical JD keywords. "
            "Use the JD Optimizer to align your resume with the target role."
        )
    elif kw["score"] < 65:
        suggestions.append(
            "💡 **Moderate keyword match.** Consider adding the missing keywords naturally "
            "into your skills and experience sections."
        )
    else:
        suggestions.append("✅ **Strong keyword alignment** with the job description.")

    # TF-IDF / semantic suggestions
    if tfidf_score < 30:
        suggestions.append(
            "📝 **Low content similarity.** Try mirroring the language, terminology, "
            "and phrasing used in the job description."
        )

    if semantic_score < 40:
        suggestions.append(
            "🔤 **Low semantic similarity.** Your resume uses different vocabulary than the JD. "
            "Rephrase bullets using the same terms the employer uses."
        )

    # Category-specific suggestions
    cat = categories
    if cat["formatting"]["score"] < 60:
        suggestions.append(
            "📋 **Improve formatting.** Add clear section headers (Education, Experience, Skills), "
            "use bullet points, and include contact information."
        )

    if cat["quantification"]["score"] < 60:
        suggestions.append(
            "📊 **Add quantified achievements.** Use numbers, percentages, and metrics to "
            "demonstrate impact (e.g., 'Increased revenue by 25%')."
        )

    if cat["role_targeting"]["score"] < 50:
        suggestions.append(
            "🎯 **Improve role targeting.** Your professional summary should directly reference "
            "the target role and its key requirements."
        )

    # Missing keywords
    if kw["missing"]:
        top_missing = kw["missing"][:10]
        suggestions.append(
            f"🔑 **Top missing keywords to add:** {', '.join(top_missing)}"
        )

    # Positive reinforcement
    if kw["score"] >= 65 and tfidf_score >= 50:
        suggestions.append("🎯 **Your resume is well-optimized for this role!**")

    return suggestions


# ---------------------------------------------------------------------------
# Main public API
# ---------------------------------------------------------------------------

def compute_ats_score(resume_text: str, jd_text: str) -> dict:
    """
    Compute a 3-layer hybrid ATS score.

    Returns:
        {
            "score": float (0-100, calibrated),
            "exact_match_score": float (0-100),
            "tfidf_score": float (0-100),
            "semantic_score": float (0-100),
            "matched_keywords": list[str],
            "missing_keywords": list[str],
            "suggestions": list[str],
            "categories": dict,
            "tfidf_similarity": float (0-1, legacy compat),
            "keyword_overlap_pct": float (0-100, legacy compat),
        }
    """
    if not resume_text.strip() or not jd_text.strip():
        return {
            "score": 0.0,
            "exact_match_score": 0.0,
            "tfidf_score": 0.0,
            "semantic_score": 0.0,
            "matched_keywords": [],
            "missing_keywords": [],
            "suggestions": ["Provide both a resume and job description for analysis."],
            "categories": {},
            "tfidf_similarity": 0.0,
            "keyword_overlap_pct": 0.0,
        }

    # Layer 1: Exact keyword match (40%)
    kw_result = _compute_keyword_score(resume_text, jd_text)
    exact_score = kw_result["score"]

    # Layer 2: TF-IDF cosine similarity (40%)
    tfidf_score = _compute_tfidf_score(resume_text, jd_text)

    # Layer 3: Semantic similarity (20%)
    semantic_score = _compute_semantic_score(resume_text, jd_text)

    # Composite raw score
    raw_composite = (exact_score * 0.4) + (tfidf_score * 0.4) + (semantic_score * 0.2)

    # Calibrate to realistic range
    final_score = _calibrate_score(raw_composite)

    # Category breakdown
    categories = _analyze_categories(resume_text, jd_text, kw_result)

    # Suggestions
    suggestions = _generate_suggestions(kw_result, tfidf_score, semantic_score, categories)

    return {
        "score": final_score,
        "exact_match_score": exact_score,
        "tfidf_score": tfidf_score,
        "semantic_score": semantic_score,
        "matched_keywords": kw_result["matched"],
        "missing_keywords": kw_result["missing"],
        "suggestions": suggestions,
        "categories": categories,
        # Legacy compatibility keys
        "tfidf_similarity": round(tfidf_score / 100, 4),
        "keyword_overlap_pct": exact_score,
    }
