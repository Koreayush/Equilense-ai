# 🚀 EquiLens AI — Unbiased AI Decision Auditor

> **Detect. Explain. Fix Bias in AI Models — Automatically.**

---

## 🧠 What is EquiLens AI?

**EquiLens AI** is a full-stack system that audits machine learning models for **bias, fairness, and reliability**.

It helps you answer critical questions like:

* Is my model biased against certain groups?
* Are predictions fair across demographics?
* What should I fix to improve fairness?

---

## Dashboard
![image alt](https://github.com/Koreayush/Equilense_AI/blob/42ad0badd4042fd5e377431365c29c126169aed3/Dashboard.png)

## ⚡ Key Features

### 🔍 Layer 1 — Data Fairness Audit

* Detect bias in raw datasets
* Analyze subgroup distributions
* Identify risky features

### 🤖 Layer 2 — Model Fairness Audit

* Works with `.pkl`, `.joblib`, `.onnx` models
* Evaluates:

  * Accuracy & performance
  * Subgroup performance
  * Bias metrics:

    * Demographic Parity
    * Equal Opportunity
    * Equalized Odds
    * FPR / FNR gaps

## Features 


### 📊 Smart Reporting

* Generates:

  * JSON reports (machine-readable)
  * PDF reports (human-friendly)
* Chart-ready outputs for dashboards

### ⚙️ Async Processing (Celery)

* Background job execution
* Scalable architecture

---

## 🏗️ System Architecture

```
Frontend (Nginx)
       ↓
FastAPI Backend (API Layer)
       ↓
Celery Worker (Async Tasks)
       ↓
Redis (Queue + Cache)
       ↓
PostgreSQL (Storage)
```

---

🐳 One-Click Demo 

🚀 Run Entire System

```bash
git clone https://github.com/Koreayush/Equilense_AI.git
cd Equilense_AI
bash run-demo.sh
bash run-demo.sh
```


## 🐳 One-Command Setup (Docker)

### 🔥 Run the entire system:

```bash
docker-compose up --build
```

---

## 🌐 Access the App

| Service     | URL                        |
| ----------- | -------------------------- |
| Frontend    | http://localhost:3000      |
| Backend API | http://localhost:8000      |
| API Docs    | http://localhost:8000/docs |

---

## 📂 Project Structure

```
unbiased-ai/
│
├── backend/          # FastAPI + Celery
├── frontend/         # Static UI (Nginx)
├── infra/docker/     # Docker setup
├── demo_output/      # Generated reports (ignored in prod)
│
└── docker-compose.yml
```

---

## 🧪 How to Use

### 1. Upload Dataset

* Run fairness audit on CSV

### 2. Upload Model + Data

* Perform full model audit

### 3. Get Results

* Bias insights
* Fairness metrics
* Recommendations

---

## 📈 Example Outputs

* ✔ Bias Detection Summary
* ✔ Subgroup Performance Table
* ✔ Fairness Scorecard
* ✔ Actionable Recommendations

---

## 💡 Why This Matters

AI systems can unintentionally:

* Discriminate
* Reinforce inequality
* Produce unfair outcomes

**EquiLens AI ensures your models are trustworthy and responsible.**

---

## 🛠️ Tech Stack

* **Backend:** FastAPI, Celery
* **Frontend:** HTML, JS, Nginx
* **Queue:** Redis
* **Database:** PostgreSQL
* **Containerization:** Docker

---

## 🚀 Future Improvements

* Real-time dashboards
* Model explainability (SHAP/LIME)
* Bias mitigation suggestions
* SaaS deployment

---

## 👨‍💻 Team

Built with ⚡ for hackathons & real-world AI fairness challenges.

---

## 🏆 Demo Ready

Run this and you're ready to present:

```bash
docker-compose up --build
```

Then open:
👉 http://localhost:3000

---

## 🔥 Final Note

> “Don’t just build AI models. Build **fair** AI models.”

---
