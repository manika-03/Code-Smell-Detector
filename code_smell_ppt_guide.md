# Code Smell Detector — PPT Guide
### IILM University · BTP2CSE333

> **Note to presenter:** You don't need to memorize technical details.
> Just understand the flow and explain it simply. This doc gives you everything slide by slide.

---

## Slide 1 — What's the Project About?

**Title:** Code Smell Detector

**What to say:**
- Writing code is one thing. Writing *good* code is another.
- Sometimes code works fine but is still badly written — too long, too complicated, or full of repeated lines.
- We call those problems **"code smells"** — they're not bugs, but they make code hard to read and maintain.
- Our project is a **web app** where you paste any Python code, click a button, and it instantly tells you:
  - What's wrong with the code
  - How bad the problem is (Low / Medium / High severity)
  - And what you should do to fix it

---

## Slide 2 — Why Does This Matter?

**What to say:**
- In real software teams, bad code piles up over time — this is called **"technical debt"**
- Detecting code smells early saves time and prevents bugs down the line
- Normally, developers have to manually review code which is slow and subjective
- Our tool **automates** that review using Machine Learning — making it faster and more consistent

**Key point to highlight:**
> It's like a spell-checker, but for code quality — not spelling.

---

## Slide 3 — What Does the App Do? (Demo Flow)

**What to say:**
1. User opens the app in a browser
2. Pastes their Python code into a text box
3. Clicks **"Check for Code Smell"**
4. The app sends the code to our backend server
5. The backend analyzes it using ML and rules
6. The result appears on screen showing:
   - GREEN = LOW / YELLOW = MEDIUM / RED = HIGH severity
   - List of detected smells (e.g., "Long Method", "High Complexity")
   - Metrics like number of functions, lines of code, etc.
   - Specific recommendations to fix each smell

---

## Slide 4 — What Code Smells Do We Detect?

**What to say:**
We detect **7 types of code smells**:

| Smell Name | What It Means (Simple) |
|---|---|
| **Long Method** | A function that does too much — over 20 lines |
| **Large Class** | A class with too many functions (5+) |
| **God Class** | One class that handles EVERYTHING (7+ functions) |
| **High Complexity** | Too many if/else, loops — hard to follow |
| **Long Parameter List** | A function that takes too many inputs (4+) |
| **Duplicate Code** | Same lines copy-pasted in multiple places |
| **Deep Nesting** | if inside for inside while — 3+ levels deep |

---

## Slide 5 — Project Structure (Two Parts)

**What to say:**
The project is split into two parts that talk to each other:

```
+---------------------------------------+
|             FRONTEND                  |
|   (What the user sees in browser)     |
|                                       |
|   HTML + CSS + JavaScript             |
|   Single file: index.html             |
+------------------+--------------------+
                   |  sends code via API
                   v
+---------------------------------------+
|              BACKEND                  |
|   (Python server doing the analysis)  |
|                                       |
|   FastAPI + ML Model                  |
|   Running on port 8000                |
+---------------------------------------+
```

---

## Slide 6 — How We Built the Frontend

**What to say:**
- The entire frontend is a **single HTML file** — no big frameworks like React needed
- It uses **HTML** for structure, **CSS** for styling, and **JavaScript** for logic
- The design is dark-themed with a glassmorphism look (blurry glass-effect cards, floating blobs in background)

**Key features of the UI:**
- A code editor text area where users paste their Python code
- A "Check for Code Smell" button
- A results section showing severity, smells, metrics, and fix recommendations
- Color-coded severity: Green = LOW, Yellow = MEDIUM, Red = HIGH
- Smooth animations throughout

**How does it talk to the backend?**
- When you click the button, JavaScript sends the code to the backend using something called a **fetch API call**
- This is just a standard way for browsers to send and receive data from a server
- It waits for the response and then displays everything on screen automatically

---

## Slide 7 — How We Built the Backend

**What to say:**
The backend is built in **Python** using a popular framework called **FastAPI**.

Every time someone submits code, it goes through **4 steps**:

### Step 1 — Extract Metrics
- We parse the Python code using Python's built-in **AST** (Abstract Syntax Tree)
- Think of AST as breaking the code into a tree structure so we can measure things inside it
- We extract **10 measurements** from the code:
  - Lines of code, number of functions, number of classes
  - Average function length, maximum nesting depth
  - How many parameters functions take on average
  - Percentage of duplicate lines
  - How complex the logic is (measured using a library called **Radon**)
  - Ratio of comment lines to total lines

### Step 2 — Detect Smells
- We compare each metric against fixed thresholds
- Example: if average function length is greater than 20 lines → flag as "Long Method"
- Each rule is checked and all triggered smells are collected into a list

### Step 3 — Classify Severity
- This is where **Machine Learning** comes in
- The 10 metrics are passed into a trained ML model
- The model predicts whether the code is LOW / MEDIUM / HIGH severity

### Step 4 — Generate Recommendations
- For each detected smell, a specific tip is returned
- Example: For "Long Method" → "Break this into smaller functions (aim for under 20 lines each)"

---

## Slide 8 — The AI / ML Part (Simple Explanation)

**What to say:**
We trained a **Machine Learning classifier** to automatically judge how severe the code smells are.

### How did we train it?

**1. Created a training dataset**
- We generated **12,000 fake code samples** with different combinations of metrics
- Each sample was labeled LOW / MEDIUM / HIGH based on scoring rules we wrote
- Since no real labeled dataset existed for this, we created a **synthetic dataset** ourselves

**2. Balanced the data using SMOTE**
- Some severity categories had way more samples than others
- SMOTE (Synthetic Minority Oversampling Technique) creates extra artificial examples in underrepresented categories
- This prevents the model from being biased toward the majority group
- Simple analogy: if you have 100 HIGH examples and only 20 LOW examples, SMOTE creates extra LOW examples until things are balanced

**3. Picked the best features using RFE**
- Out of 10 metrics, we used Recursive Feature Elimination (RFE) to automatically identify the **8 most useful ones**
- It's like asking: "Which measurements actually help predict severity?" — and letting the algorithm answer that

**4. Trained two models and compared them:**
- **Random Forest** — A group of many decision trees that vote together on the final answer
- **XGBoost** — A more advanced model that builds trees one by one, each one correcting mistakes from the last
- We tested both using a score called **F1-score** and kept the one that performed better

**5. Saved the model**
- The winning model is saved to disk as a `.pkl` file
- Every time the backend starts, it loads this file automatically

**Built-in safety net:**
- If the ML model fails to load for any reason, the system switches to a pure rule-based approach automatically
- This means the app always works — with or without the ML model

---

## Slide 9 — Tech Stack Summary

**What to say:**
Here's a quick table of everything we used:

| Part | Technology | What It Does |
|---|---|---|
| **Frontend** | HTML, CSS, JavaScript | The visual web interface |
| **Backend** | FastAPI (Python) | Receives code and runs analysis |
| **ML Models** | Random Forest, XGBoost | Classifies severity: LOW / MEDIUM / HIGH |
| **Data Handling** | Pandas, NumPy | Generates and processes training data |
| **Code Parsing** | AST (Python built-in) | Reads and understands code structure |
| **Complexity Score** | Radon | Measures how complex the code logic is |
| **Class Balancing** | SMOTE (imbalanced-learn) | Balances training data across severity levels |
| **Model Saving** | Joblib | Saves and loads the trained ML model |
| **API Server** | Uvicorn | Runs the Python backend locally |

---

## Slide 10 — Full System Flow

```
User pastes Python code in the browser
         |
         v
JavaScript sends it to backend  (POST /analyze)
         |
         v
Backend receives the code
         |
         |---> Step 1: Parse code with AST + Radon → 10 metrics extracted
         |
         |---> Step 2: Compare metrics to thresholds → list of smells found
         |
         |---> Step 3: Feed metrics to ML model → LOW / MEDIUM / HIGH
         |
         |---> Step 4: Match smells to fix recommendations
         |
         v
Send result back to browser (as JSON data)
         |
         v
Frontend shows: severity badge + smell tags + metric cards + fix tips
```

---

## Slide 11 — What Makes It Smart?

**What to say:**
The system uses **two layers** working together to give reliable results:

**Layer 1 — Rule-based engine**
- Fixed rules like "if nesting depth is greater than 3 → flag as Deep Nesting"
- Always runs, always consistent, easy to audit
- Acts as the *minimum* — the result can never be lower than what this says

**Layer 2 — ML model**
- Trained on 12,000 examples to recognize patterns across all metrics together
- Can catch combinations that individual rules might miss
- It can push severity *higher* than the rules, but never *lower*

This design is called a **safety floor** — the rules are the floor, and ML builds on top of it.

---

## Slide 12 — Challenges We Faced

**What to say (just pick a couple to mention):**

- **No real dataset available** — We had to design and generate our own synthetic training data from scratch
- **ML was too lenient early on** — The model would say LOW even when rules clearly said HIGH; fixed by making rule-based score a hard minimum
- **Frontend and backend on different ports** — Browsers block this by default for security; we had to configure CORS (Cross-Origin Resource Sharing) to allow communication between them
- **Backend not running = confusing error** — We added a clear, human-readable error message: "Cannot reach the backend. Make sure uvicorn is running on port 8000."

---

## Slide 13 — Conclusion

**What to say:**
- We built a **complete, working web application** that combines code analysis and machine learning
- It analyzes Python code in real time and gives useful, actionable feedback — no manual review needed
- The system is reliable (falls back to rules if ML fails), smart (ML adds intelligence on top), and easy to use (clean browser-based UI)
- Similar real-world tools include **SonarQube** and **CodeClimate** — our project is a simplified but genuinely functional version of that idea

**Future scope (optional to mention):**
- Support more programming languages — currently Python only
- Connect to GitHub to analyze entire repositories at once
- Detect more types of code smells
- Use generative AI to not just detect issues but also suggest how to rewrite the problematic code

---

*Prepared for IILM University  ·  BTP2CSE333  ·  Code Smell Detector Project*
