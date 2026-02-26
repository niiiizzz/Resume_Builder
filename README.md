# 🚀 AI Resume & Portfolio Builder with ATS Optimization

An AI-powered SaaS web application that helps students and job seekers generate, optimize, and analyze resumes using intelligent automation.

Built with **Streamlit + SQLAlchemy + Generative AI**.

---

## ✨ What It Does

🔹 Generate ATS-friendly resumes  
🔹 Optimize resumes based on job descriptions  
🔹 Analyze ATS score using a hybrid scoring model  
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
- Actionable improvement suggestions  

---

## 🛠 Tech Stack

- **Frontend & Backend:** Streamlit  
- **Database (Default):** SQLite (`resume_builder.db`)  
- **Optional Database:** PostgreSQL (via `DATABASE_URL`)  
- **ORM:** SQLAlchemy  
- **AI Integration:** LLM API (via environment variables)  
- **Text Processing:** scikit-learn + NLP preprocessing  

---

## 🗄 Database Configuration

By default, the application uses:

SQLite → `resume_builder.db`

To use PostgreSQL (or any SQLAlchemy-compatible database), set an environment variable:

```bash
export DATABASE_URL=postgresql://user:password@host:port/dbname
```

The app automatically switches to the provided database.

---

## 🔐 Security Features

- Password hashing  
- Environment-based API key management  
- ORM-based SQL injection protection  
- Secure session management  

---

## 📦 Key Features

✔ Authentication system  
✔ Resume version storage  
✔ JD-based optimization  
✔ ATS analysis history  
✔ PDF upload & text extraction  
✔ Download as PDF/DOCX  

---

## 🚀 Why This Project?

Traditional resume builders are static and generic.

This system dynamically:
- Personalizes content  
- Aligns resumes with job roles  
- Improves ATS compatibility  
- Enhances job application success  

---

## 📌 Status

Production-ready SaaS MVP  
Modular architecture  
Clean separation of concerns  

---

⭐ If you found this project interesting, feel free to star the repository!
