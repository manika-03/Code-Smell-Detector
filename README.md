<h1 align="center" style="color: #4a90e2; font-size: 2.5em;">
  🧠 Code Smell Detector
</h1>

<p align="center" style="font-size: 1.2em; color: #555;">
  <strong>A full-stack ML web application that analyzes Python code for code smells, classifies severity, and provides actionable fix recommendations.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi" alt="FastAPI">
  <img src="https://img.shields.io/badge/scikit--learn-%23F7931E.svg?style=for-the-badge&logo=scikit-learn&logoColor=white" alt="scikit-learn">
  <img src="https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white" alt="HTML5">
  <img src="https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black" alt="JavaScript">
</p>

## 📋 Table of Contents

- [Introduction](#-introduction)
- [Features](#-features)
- [Project Structure](#-project-structure)
- [Prerequisites](#-prerequisites)
- [Setup & Run](#-setup--run)
- [Detected Code Smells](#-detected-code-smells)
- [API Reference](#-api-reference)
- [ML Pipeline](#-ml-pipeline)
- [Tech Stack](#-tech-stack)

## 🌟 Introduction

**Code Smell Detector** is an intelligent tool designed to help developers write cleaner, more maintainable Python code. By combining static code analysis with machine learning, it automatically detects poor coding patterns (code smells), assesses their severity (LOW, MEDIUM, HIGH), and offers specific refactoring recommendations. Developed as part of **IILM University · BTP2CSE333**.

## ✨ Features

- **Real-time Code Analysis**: Instantly parses and examines your Python code.
- **Machine Learning Classification**: Uses a trained Random Forest / XGBoost model to classify the severity of detected smells with high accuracy.
- **Actionable Recommendations**: Doesn't just point out flaws—it tells you exactly how to fix them.
- **10 Advanced Static Metrics**: Analyzes everything from cyclomatic complexity and nesting depth to duplicate code ratios.
- **Beautiful Interface**: A modern, single-page frontend that's intuitive and visually engaging.

## 📂 Project Structure

```text
code-smell-detector/
├── frontend/
│   └── index.html          ← Single-file SPA (HTML + CSS + JS)
├── backend/
│   ├── main.py             ← FastAPI server
│   ├── extractor.py        ← 10 static metric extractors (ast + radon)
│   ├── analyzer.py         ← Smell detection, severity, recommendations
│   ├── train_model.py      ← ML training script (run once)
│   ├── requirements.txt    ← Python dependencies
│   ├── data/
│   │   └── synthetic_metrics.csv   ← Training samples
│   └── model/
│       ├── classifier.pkl          ← Trained model
│       ├── label_encoder.pkl       ← LOW/MED/HIGH encoder
│       └── features.pkl            ← Selected feature names
```

## ⚙️ Prerequisites

Before you begin, ensure you have met the following requirements:
- **Python**: Version `3.10` or higher
- **Package Manager**: `pip`
- **Web Browser**: Chrome, Firefox, Edge, or Safari

## 🚀 Setup & Run

Follow these steps to get the project running locally on your machine.

### 1. Install Dependencies

Navigate to the backend directory and install the required Python packages:

```bash
cd backend
pip install -r requirements.txt
```

### 2. Train the ML Model (One-Time Setup)

To use the advanced ML capabilities, train the model first:

```bash
cd backend
python train_model.py
```

*What this does:*
- Generates 12,000 synthetic training samples.
- Applies SMOTE for class balancing and runs RFE for feature selection.
- Trains using GridSearchCV over Random Forest and XGBoost.
- Expected output ends with: `✅  Training complete!`

*(Note: If skipped, the system falls back to a reliable rule-based classifier).*

### 3. Start the Backend Server

Launch the FastAPI application:

```bash
cd backend
uvicorn main:app --reload --port 8000
```
You should see: `INFO: Uvicorn running on http://127.0.0.1:8000`

### 4. Launch the Frontend

Open the `frontend/index.html` file directly in your browser. 
- You can simply double-click the file, drag it into a browser tab, or use **Live Server** in VS Code.
- *Pro Tip:* Use **Ctrl + Enter** inside the code editor to quickly trigger an analysis!

## 🕵️‍♂️ Detected Code Smells

The system actively monitors your code for the following common structural issues:

| 🚨 Smell | 📈 Detection Rule |
| :--- | :--- |
| **Long Method** | `avg_function_length > 30` lines |
| **Large Class** | `num_functions > 15` |
| **Duplicate Code** | `duplicate_ratio > 25%` |
| **High Complexity** | `cyclomatic_complexity > 10` |
| **Long Parameter List**| `avg_params > 4` |
| **God Class** | Single class dominates `> 60%` of functions |

## 🔌 API Reference

### `POST /analyze`
Analyzes a Python code snippet.

**Request Body:**
```json
{
  "code": "def my_function(a, b, c, d, e):\n    ..."
}
```

**Successful Response:**
```json
{
  "severity": "HIGH",
  "smells": ["Long Method", "High Complexity"],
  "metrics": {
    "loc": 312,
    "cyclomatic_complexity": 18.4,
    "num_functions": 24,
    "avg_function_length": 42.1,
    "max_function_length": 98,
    "num_classes": 2,
    "duplicate_ratio": 0.31,
    "max_nesting_depth": 6,
    "comment_ratio": 0.08,
    "avg_params": 3.2
  },
  "recommendations": [
    "Break this function into smaller, single-purpose methods.",
    "Replace deeply nested conditionals with guard clauses."
  ],
  "model_used": "ml_classifier",
  "parse_error": false
}
```

### `GET /health`
Returns the status of the backend server.
```json
{ "status": "ok", "model_loaded": true, "version": "1.0.0" }
```

*For an interactive API experience, visit **[http://localhost:8000/docs](http://localhost:8000/docs)***

## 🧠 ML Pipeline

The project utilizes a robust machine learning workflow:
1. **Synthetic Dataset**: 12k rows generated
2. **Stratified Split**: 80/20 train-test split
3. **SMOTE**: Oversampling to balance minority classes
4. **RFE Feature Selection**: Drops noisy attributes (uses top 8 of 10)
5. **GridSearchCV**: Compares RandomForest vs. XGBoost
6. **Best Model Selection**: Exports top scorer (by F1-weighted) to `classifier.pkl`

## 💻 Tech Stack

| Domain | Technologies |
| :--- | :--- |
| **Frontend** | HTML5, CSS3, Vanilla JS |
| **Backend** | FastAPI, Uvicorn, Pydantic v2 |
| **Machine Learning**| scikit-learn, XGBoost, imbalanced-learn |
| **Code Analysis** | `ast` (Standard Library), `radon` |
| **Data processing** | pandas, numpy |

---
<p align="center">
  <i>Built with ❤️ by IILM University Students</i>
</p>
