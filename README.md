# ⚖️ Equilense AI — Fairness & Bias Inspection Platform
 

> **An enterprise-grade AI auditing system for detecting hidden bias in datasets and machine learning models before deployment.**

---

## 📌 Project Overview

**Equilense AI** is a fairness inspection platform designed to help organizations **audit datasets and machine learning models for discrimination, imbalance, and harmful bias**.

As AI systems increasingly influence critical decisions in **hiring, lending, insurance, education, and healthcare**, it becomes essential to ensure that these systems are **fair, transparent, and accountable**.

This project provides a **clear, accessible, and production-oriented solution** to inspect both:

- **Datasets (Layer 1)** → to identify bias before training
- **Machine Learning Models (Layer 2)** → to detect unfair predictions after training

The platform generates **structured fairness metrics, subgroup analysis, risk scoring, findings, and downloadable reports**, helping teams identify and mitigate fairness issues before deployment.

---

# 🚨 Problem Statement

Modern machine learning systems are often trained on **historical human decisions**.

That means if past decisions were biased, the model can silently learn patterns that reproduce and even amplify discrimination.

### Real-world examples of this risk:
- A **loan approval model** may unfairly reject certain communities
- A **hiring algorithm** may favor one gender over another
- A **healthcare prediction system** may underperform for vulnerable groups
- A **student scoring system** may disadvantage certain backgrounds

These failures are often **not visible through accuracy alone**.

A model can be:
- **highly accurate**
- **technically correct**
- and still **deeply unfair**

### The challenge:
Most teams lack an easy, explainable, and practical way to audit fairness before production.

### This project solves that by:
- detecting **bias in datasets**
- auditing **fairness in trained models**
- generating **interpretable risk signals**
- producing **actionable findings and reports**

---

# 🎯 Objective

Build a clear and accessible solution to thoroughly inspect:

1. **Datasets** for hidden unfairness or imbalance  
2. **Machine Learning Models** for discriminatory behavior across sensitive groups

### Core Goal
Enable organizations to:

- **Measure** fairness
- **Detect** harmful bias
- **Flag** high-risk patterns
- **Understand** subgroup-level behavior
- **Mitigate** unfairness before deployment

---

# ✨ Key Features

## ✅ Layer 1 — Dataset Fairness Audit
Audit raw CSV datasets before training to detect potential fairness risks.

### Capabilities:
- Sensitive attribute distribution analysis
- Class balance inspection
- Representation gap analysis
- Missing value detection
- Protected-group comparison
- Fairness risk summary
- Bias flags & recommendations
- JSON / PDF report generation

---

## ✅ Layer 2 — Model Fairness Audit
Audit trained machine learning models against evaluation data.

### Capabilities:
- Upload and inspect trained ML models
- Run predictions on evaluation datasets
- Evaluate subgroup fairness across sensitive attributes
- Measure prediction disparities
- Detect fairness failures beyond raw accuracy
- Generate risk scores and findings
- Produce downloadable audit reports

### Supported model formats:
- `.joblib`
- `.pkl`
- `.onnx`

---

> Production-prototype: AI fairness auditing, bias detection, and explainability reporting.

## Stack
- **Backend**: FastAPI + Python 3.11
- **Database**: PostgreSQL + SQLAlchemy + Alembic
- **Queue**: Celery + Redis
- **Reports**: ReportLab (PDF) + JSON
- **Auth**: JWT (OAuth2 password flow)
- **Frontend**: Vanilla HTML/CSS/JS (no build step required)
- **Charts**: Chart.js 4
- **Infra**: Docker Compose

---

## Quickstart — Demo (no Docker needed)

```bash
# 1. Install Python deps
pip install pandas numpy reportlab

# 2. Run the demo — generates PDF + JSON reports
python demo.py

# 3. Open the frontend
open frontend/index.html
```

Reports are written to `./demo_output/hackathon-demo/`:
- `report.pdf` — polished multi-page PDF audit report
- `report.json` — structured JSON for API consumption

---

## Quickstart — Full Stack (Docker)

```bash
cp backend/.env.example backend/.env
docker-compose -f infra/docker/docker-compose.yml up --build
```

- API docs: http://localhost:8000/docs
- Frontend: open `frontend/index.html` in your browser

---

## Project Structure

```
Unbiased-ai/
├── demo.py                              ← Run this first — full pipeline demo
├── frontend/
│   ├── index.html                       ← Interactive dashboard (open in browser)
│   └── src/
│       ├── styles.css                   ← All styles
│       └── app.js                       ← All interactivity + Chart.js logic
├── backend/
│   ├── requirements.txt
│   └── app/
│       ├── main.py                      ← FastAPI entrypoint
│       ├── core/config.py               ← Env-based settings
│       ├── core/security.py             ← JWT auth helpers
│       ├── db/models/models.py          ← All 8 SQLAlchemy ORM tables
│       ├── services/audit/
│       │   └── fairness_engine.py       ← Bias detection (6 checks)
│       ├── services/report/
│       │   └── report_generator.py      ← PDF + JSON report generation
│       └── workers/audit_worker.py      ← Celery async audit jobs
├── infra/docker/
│   ├── docker-compose.yml
│   └── Dockerfile.api
└── README.md
```

---

## API Endpoints (V1)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/auth/register` | Register user |
| POST | `/api/v1/auth/login` | Get JWT token |
| POST | `/api/v1/projects` | Create project |
| POST | `/api/v1/datasets/upload` | Upload dataset CSV |
| POST | `/api/v1/audit/run` | Trigger bias audit |
| GET  | `/api/v1/audit/{id}/status` | Poll job status |
| GET  | `/api/v1/reports/{id}/json` | Download JSON report |
| GET  | `/api/v1/reports/{id}/pdf` | Download PDF report |

---


## 📊 Performance + Fairness Metrics
The platform combines **traditional ML evaluation** with **fairness diagnostics**.

### Model Performance Metrics
- Accuracy
- Precision
- Recall
- F1 Score
- ROC-AUC (when probability is available)

### Fairness Metrics
- Demographic Parity Difference
- Disparate Impact
- Equal Opportunity Difference
- Equalized Odds Difference
- False Positive Rate Difference
- False Negative Rate Difference

---

## 📁 Report Generation
Automatically generates:
- **JSON reports** (machine-readable)
- **PDF reports** (stakeholder-friendly)

These reports are designed for:
- technical review
- internal governance
- hackathon demos
- portfolio presentation
- compliance-oriented discussions

---

# 🏗️ End-to-End Architecture

## System Layers

This platform is intentionally designed as a **multi-layer AI inspection system**.

---

## 🔹 Layer 1 — Dataset Inspection Layer

### Purpose
Inspect raw tabular datasets **before training** to detect fairness and bias risks.

### Input
- CSV dataset

### Output
- Dataset audit summary
- subgroup distribution analysis
- fairness indicators
- report files

### Why it matters
If the **training data is biased**, the model will likely learn biased patterns.

This layer helps answer:

- Is one group underrepresented?
- Are labels distributed unfairly?
- Is the dataset structurally risky?

---

## 🔹 Layer 2 — Model Inspection Layer

### Purpose
Inspect a trained machine learning model **after training** using evaluation data.

### Input
- Trained model file (`.joblib`, `.pkl`, `.onnx`)
- Evaluation CSV
- Target column
- Sensitive columns
- Positive label

### Output
- Global model performance
- Fairness metrics
- Subgroup performance
- Bias findings
- Risk score
- Reports

### Why it matters
A model can perform well overall but still treat groups differently.

This layer helps answer:

- Does the model predict unfairly across groups?
- Which subgroup is most affected?
- Is the model safe to deploy?

---


# 🧠 High-Level Architecture

```text
                ┌───────────────────────────────┐
                │         Frontend UI           │
                │   HTML / CSS / JavaScript     │
                └──────────────┬────────────────┘
                               │
                               ▼
                ┌───────────────────────────────┐
                │         FastAPI Backend       │
                │    API Layer + Validation     │
                └──────────────┬────────────────┘
                               │
              ┌────────────────┴────────────────┐
              ▼                                 ▼
┌───────────────────────────┐      ┌───────────────────────────┐
│   Layer 1: Dataset Audit  │      │   Layer 2: Model Audit    │
│   CSV Bias Inspection     │      │ Model + Eval Data Audit    │
└──────────────┬────────────┘      └──────────────┬────────────┘
               │                                  │
               ▼                                  ▼
┌───────────────────────────┐      ┌───────────────────────────┐
│  Fairness Analysis Engine │      │ Inference + Fairness Eval │
│ Distribution / Bias Rules │      │ Metrics / Group Analysis  │
└──────────────┬────────────┘      └──────────────┬────────────┘
               │                                  │
               └──────────────┬───────────────────┘
                              ▼
                ┌───────────────────────────────┐
                │      Reporting Layer          │
                │    JSON + PDF Report Output   │
                └───────────────────────────────┘
