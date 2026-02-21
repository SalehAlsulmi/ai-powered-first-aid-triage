# AI-Powered First Aid Support System 🚑🤖

An AI-powered system designed to assist in emergency case assessment and first aid decision-making using Machine Learning models.

This project was developed as a **team project during a hackathon**, focusing on applying Artificial Intelligence to support real-world emergency response scenarios.

---

## 💡 Project Overview

The goal of this system is to support individuals during emergency situations by:

- Collecting symptoms through a simple user interface
- Processing data using trained Machine Learning models
- Predicting risk or severity levels
- Providing suggested first aid actions

This system is designed as a supportive tool and does not replace professional medical services.

---

## 🧠 How It Works

1. The user inputs symptoms (e.g., bleeding, breathing issues, chest pain, etc.)
2. The backend processes the inputs
3. Trained ML models analyze the case
4. The system returns:
   - Risk level assessment
   - Recommended next steps

---

## 🛠️ Technologies Used

- Python (Flask)
- Scikit-learn
- Joblib
- NumPy
- HTML / CSS / JavaScript

---

## 📂 Project Structure

```
smart-ai-first-aid-system/
│
├── README.md
├── requirements.txt
├── app.py
├── train_models.py
│
├── models/
│   ├── bleeding.joblib
│   ├── breathing.joblib
│   ├── chest_pain.joblib
│   ├── conscious.joblib
│   ├── dizziness.joblib
│   ├── pain_level.joblib
│   └── vomiting.joblib
│
├── frontend/
│   ├── index.html
│   ├── styles.css
│   └── app.js
```
---

## 🚀 How to Run the Project

### 1️⃣ Install dependencies

pip install -r requirements.txt

### 2️⃣ Run the backend

python app.py

### 3️⃣ Open the frontend
Open the `index.html` file inside the `frontend` folder in your browser.

---

## 👥 Hackathon Team Project

This system was built collaboratively during a hackathon as a team effort to create an AI-based solution for emergency first aid support.

---

## ⚠️ Disclaimer

This project is developed for educational and hackathon purposes only.  
It does not replace professional medical advice or emergency services.
