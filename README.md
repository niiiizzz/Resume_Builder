# 🚀 AI Resume & Portfolio Builder with ATS Optimization

An AI-powered SaaS web application that helps students and job seekers generate, optimize, and analyze resumes using intelligent automation.

Built with **Streamlit + SQLAlchemy + Generative AI**.

---

## ✨ What It Does

🔹 Generate ATS-friendly resumes  
🔹 Optimize resume based on job description  
🔹 Analyze ATS score (Hybrid scoring model)  
🔹 Generate professional cover letters  
🔹 Extract text from PDF uploads  
🔹 Save and manage resume history  

---

## 🧠 Intelligent ATS Engine

The ATS scoring system uses a hybrid approach:

- Keyword Matching  
- TF-IDF Cosine Similarity  
- Semantic Similarity  

It provides:
- Compatibility score  
- Missing keyword detection  
- Improvement suggestions  

---

## 🛠 Tech Stack

- **Frontend & Backend:** Streamlit  
- **Database (Default):** SQLite (`resume_builder.db`)  
- **Optional DB:** PostgreSQL (via `DATABASE_URL`)  
- **ORM:** SQLAlchemy  
- **AI Integration:** LLM API (via environment variables)  
- **Text Processing:** scikit-learn, NLP preprocessing  

---

## 🗄 Database Configuration

By default, the app uses:
