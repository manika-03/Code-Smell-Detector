# Code Smell Detector — Project Explained
### IILM University · BTP2CSE333

---

## What Is This Project?

A web app that analyzes Python code and tells you how badly written it is — not if it's broken, but if it's messy, overly complex, or hard to maintain. These problems are called **code smells**.

You paste code → click a button → get back:
- A **severity rating** (LOW / MEDIUM / HIGH)
- A **list of smells** found in the code
- **Fix suggestions** for each smell

> Think of it like a spell-checker, but for code quality.

---

## What Are Code Smells? (7 types we detect)

| Smell | What it means |
|---|---|
| **Long Method** | Function is too long (20+ lines) |
| **Large Class** | Class has too many functions (5+) |
| **God Class** | One class controls everything (7+ functions) |
| **High Complexity** | Too many if/else and loops — hard to follow |
| **Long Parameter List** | Function takes too many inputs (4+) |
| **Duplicate Code** | Same lines repeated in multiple places |
| **Deep Nesting** | if inside for inside while — 3+ levels deep |

---

## Project Structure

The project has two parts that talk to each other:

**Frontend** (`index.html`) — runs in the browser, what the user sees
**Backend** (`main.py`) — Python server running at `localhost:8000`, does the actual analysis

The frontend sends code → backend analyzes it → sends results back → frontend displays them.

---

## Frontend — How We Built It

- Built as a **single HTML file** using plain HTML, CSS, and JavaScript (no React or frameworks)
- **Design:** Dark theme, glassmorphism cards (frosted glass look), animated floating background blobs, smooth slide-in animations
- **Colors:** Green = LOW, Yellow = MEDIUM, Red = HIGH
- **How it talks to the backend:** JavaScript uses a `fetch()` call — a built-in browser tool — to send the code and receive results
- If the backend isn't running, a clear red error message appears instead of crashing
- Bonus: `Ctrl + Enter` also triggers analysis (keyboard shortcut)

---

## Backend — How We Built It

Built in **Python** using **FastAPI**. Every time code is submitted, it runs through **4 steps**:

### Step 1 — Extract 10 Metrics (`extractor.py`)
The code is parsed using Python's built-in **AST (Abstract Syntax Tree)** — it reads the code structure like a tree and lets us count things precisely.

The 10 metrics extracted:

| Metric | What it measures |
|---|---|
| LOC | Total non-blank lines |
| Cyclomatic Complexity | Number of decision paths (via **Radon** library) |
| Num Functions | How many functions exist |
| Avg Function Length | Average lines per function |
| Max Function Length | Longest single function |
| Num Classes | How many classes exist |
| Duplicate Ratio | % of lines that appear more than once |
| Max Nesting Depth | How deeply nested the code is |
| Comment Ratio | % of lines that are comments |
| Avg Parameters | Average inputs per function |

### Step 2 — Detect Smells (`analyzer.py`)
Each metric is compared to a threshold. If it crosses the threshold, that smell is flagged.
Example: `avg_function_length > 20` → flag "Long Method"
All triggered smells are collected into a list.

### Step 3 — Classify Severity (ML + Rules)
Two systems run in parallel:
- **Rule-based:** Each smell has a weight (God Class = 3pts, etc.). Bonus points for extreme values. Score ≥ 4 = HIGH, 1–3 = MEDIUM, 0 = LOW.
- **ML model:** The 10 metrics are fed into a trained classifier → predicts LOW / MEDIUM / HIGH.

Final result = whichever is **higher**. The ML can raise severity but never lower it. The rules act as a **safety floor**.

### Step 4 — Generate Recommendations (`analyzer.py`)
Each smell maps to a specific, actionable fix tip.
Example: "Long Method" → *"Break into smaller functions, target ≤ 20 lines each."*

---

## The ML / AI Part

We trained a **classification model** to predict severity from the 10 metrics.

### Pipeline:

**1. Dataset** — No real labeled dataset existed, so we **generated 12,000 synthetic code samples**, each labeled LOW/MEDIUM/HIGH using our rules. This is called a synthetic dataset — a valid and common approach when real labeled data is unavailable.

**2. SMOTE** — The dataset had too many LOW samples and fewer HIGH ones. **SMOTE** (Synthetic Minority Oversampling Technique) creates extra artificial examples of minority classes to balance the training data. Prevents the model from being biased toward LOW.

**3. RFE (Feature Selection)** — Out of 10 metrics, **Recursive Feature Elimination** automatically picked the **8 most useful ones**. Fewer features = less noise = better model.

**4. Two Models Trained and Compared:**
- **Random Forest** — Many decision trees that vote together. Reliable and handles tabular data well.
- **XGBoost** — Trees built sequentially, each correcting the last. Usually more accurate.
- Both were tuned using **GridSearchCV** (tests many parameter combos automatically).
- The one with the better **F1-score** (balanced accuracy metric) was kept.

**5. Model saved** as `classifier.pkl` using Joblib. Loaded at server startup every time.

**Fallback:** If the model file is missing or fails, the system automatically uses rules only. The app never breaks.

---

## Challenges We Faced

- **No real dataset** → Built a synthetic one using our own scoring rules
- **ML was too lenient** → Fixed by making rule-based score a hard minimum (safety floor)
- **CORS error** → Browser blocks requests between different origins by default; configured FastAPI to allow it
- **Backend must be started manually** → Added a clear error message in the UI when it's not running

---

## Tech Stack — Quick Summary

| Layer | Tool |
|---|---|
| Frontend | HTML, CSS, JavaScript |
| Backend | FastAPI + Uvicorn (Python) |
| Code Parsing | AST (built-in) + Radon |
| ML Models | Random Forest, XGBoost |
| Data | NumPy, Pandas (synthetic dataset) |
| Balancing | SMOTE (imbalanced-learn) |
| Model Storage | Joblib |
| Input Validation | Pydantic |

---

## Quick Q&A (if someone asks)

**Q: Why only Python?**
AST is Python-specific. Other languages need their own parsers.

**Q: Isn't synthetic data fake?**
It's a valid technique used widely in ML research when real labeled data doesn't exist.

**Q: Why train two models?**
You can't predict which performs better beforehand — train both, compare, keep the best.

**Q: What's F1-score?**
A balanced accuracy metric. Works well when class sizes are unequal. Closer to 1.0 = better.

**Q: What does the ML model actually learn?**
It learns which *combinations* of metrics indicate bad code — things that individual rules might miss by looking at metrics one at a time.

---

## In One Line

> We built a full-stack web app that parses Python code, extracts 10 metrics, runs 7 smell detection rules, and uses a trained ML classifier (backed by 12,000 synthetic samples, SMOTE, RFE, and GridSearch) to rate code quality as LOW / MEDIUM / HIGH — with fix recommendations returned for each detected issue.

---