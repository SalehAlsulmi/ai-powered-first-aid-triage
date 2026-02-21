import os
import re
from unittest import result
from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib

app = Flask(__name__)
CORS(app)

# -----------------------------
# Load Local ML Models (joblib)
# -----------------------------
MODEL_FIELDS = ["breathing", "conscious", "bleeding", "dizziness", "vomiting", "chest_pain", "pain_level"]
MODELS = {}
MODEL_LOAD_ERRORS = []

def load_models():
    global MODELS, MODEL_LOAD_ERRORS
    MODELS = {}
    MODEL_LOAD_ERRORS = []

    for field in MODEL_FIELDS:
        path = os.path.join("models", f"{field}.joblib")
        if not os.path.exists(path):
            MODEL_LOAD_ERRORS.append(f"Missing model file: {path}")
            continue
        try:
            MODELS[field] = joblib.load(path)
        except Exception as e:
            MODEL_LOAD_ERRORS.append(f"Failed to load {path}: {e}")

load_models()

# -----------------------------
# Rule-based Triage
# -----------------------------
def triage(data: dict):
    breathing = data.get("breathing")
    conscious = data.get("conscious")
    bleeding = data.get("bleeding")
    chest_pain = data.get("chest_pain", "no")
    age = int(data.get("age", 0) or 0)

    pain_level = data.get("pain_level", "none")
    vomiting = data.get("vomiting", "no")
    dizziness = data.get("dizziness", "no")

    notes = []
    red_reasons = []

    # 🔴 RED FLAGS
    if breathing in ["no", "abnormal"]:
        red_reasons.append("مشكلة في التنفس.")
    if conscious == "no":
        red_reasons.append("فاقد للوعي.")
    if bleeding == "severe":
        red_reasons.append("نزيف شديد.")
    if chest_pain == "yes":
        red_reasons.append("ألم صدر شديد.")

    if red_reasons:
        steps = ["اتصل بالطوارئ فورًا."]

        if breathing in ["no", "abnormal"]:
            steps.append("إذا لا يتنفس: ابدأ CPR إذا كنت تعرف الطريقة واطلب المساعدة.")

        if bleeding == "severe":
            steps.append("اضغط بقوة على مكان النزيف بقطعة نظيفة ولا ترفع يدك.")

        steps.append("لا تعطه أكل أو شرب. راقب التنفس والوعي حتى وصول الإسعاف.")

        return "🔴 طارئ جدًا", True, steps, red_reasons

    # 🟡 / 🟢 SCORE
    score = 0

    if bleeding == "mild":
        score += 1
        notes.append("نزيف بسيط.")

    if age and (age < 5 or age > 65):
        score += 1
        notes.append("فئة عمرية حساسة.")

    if pain_level == "moderate":
        score += 1
        notes.append("ألم متوسط.")
    elif pain_level == "severe":
        score += 2
        notes.append("ألم شديد.")

    if vomiting == "yes":
        score += 1
        notes.append("قيء.")

    if dizziness == "yes":
        score += 1
        notes.append("دوخة.")

    if score >= 3:
        steps = ["يوصى بمراجعة طوارئ أو عيادة خلال ساعات."]

        if bleeding == "mild":
            steps.append("نظف الجرح بالماء وغطّه بضماد نظيف.")

        if pain_level in ["moderate", "severe"]:
            steps.append("حاول إراحة المصاب وتجنب الحركة الزائدة.")

        if vomiting == "yes":
            steps.append("أعطه سوائل بكميات قليلة إذا كان واعيًا.")

        steps.append("إذا تدهورت الحالة ← اتصل بالطوارئ.")

        return "🟡 متوسط", False, steps, notes

    steps = ["إسعاف منزلي ومتابعة."]

    if bleeding == "mild":
        steps.append("نظف الجرح بالماء وغطّه بضماد نظيف.")

    if pain_level == "mild":
        steps.append("يمكن إعطاء مسكن خفيف عند الحاجة إذا لا يوجد مانع طبي.")

    if dizziness == "yes":
        steps.append("اجعل المصاب يجلس أو يستلقي حتى تزول الدوخة.")

    steps.append("إذا ظهرت أعراض جديدة أو زادت الحالة سوءًا ← راجع طوارئ.")

    return "🟢 بسيط", False, steps, notes


# -----------------------------
# Utility: normalize text + keyword guards
# -----------------------------
def norm_text(s: str) -> str:
    s = (s or "").lower()
    s = s.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    s = re.sub(r"[^\w\u0600-\u06FF\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


KEYWORDS = {
    "bleeding": ["نزيف","ينزف","نزف","دم","جرح","مجرح","قطع","دم كثير","دم خفيف","ينقط دم","ينزف شوي"],
    "vomiting": ["قيء", "استفراغ", "يتقيأ","تقيؤ", "يرجع", "ترجيع", "طرش", "تطريش", "طرّش", "يطرش", "يطرّش", "يطـرش"],
    "dizziness": ["دوخه", "دوار", "يدوخ", "دوخة"],
    "chest_pain": ["صدر", "الم صدر", "الم بالصدر", "وجع صدر", "ضيق صدر"],
}

BREATH_BAD = ["ما يتنفس", "لا يتنفس", "انقطاع تنفس", "اختناق", "صعوبه تنفس", "ضيق تنفس", "تنفس بصعوبه"]
BREATH_GOOD = ["يتنفس طبيعي", "تنفسه طبيعي", "يتنفس عادي", "يتنفس"]
CONSC_NO = ["فاقد وعي", "مغمي عليه", "اغمى عليه", "ما يرد", "غير واعي"]
CONSC_YES = ["واعي", "يرد", "يتكلم", "يتجاوب"]

def keyword_guard_defaults(t: str):
    out = {}
    if not any(k in t for k in KEYWORDS["bleeding"]):
        out["bleeding"] = "none"
    if not any(k in t for k in KEYWORDS["vomiting"]):
        out["vomiting"] = "no"
    if not any(k in t for k in KEYWORDS["dizziness"]):
        out["dizziness"] = "no"
    if not any(k in t for k in KEYWORDS["chest_pain"]):
        out["chest_pain"] = "no"
    return out

def direct_keyword_rules(t: str):
    out = {}

    # breathing
    if any(k in t for k in BREATH_BAD):
        if ("صعوبه" in t) or ("ضيق" in t) or ("بصعوبه" in t):
            out["breathing"] = "abnormal"
        elif ("لا يتنفس" in t) or ("ما يتنفس" in t) or ("انقطاع" in t):
            out["breathing"] = "no"
        else:
            out["breathing"] = "abnormal"
    elif any(k in t for k in BREATH_GOOD):
        out["breathing"] = "yes"

    # conscious
    if any(k in t for k in CONSC_NO):
        out["conscious"] = "no"
    elif any(k in t for k in CONSC_YES):
        out["conscious"] = "yes"

    # pain level
    if ("الم شديد" in t) or ("يوجعه مره" in t) or ("يوجعه مرة" in t):
        out["pain_level"] = "severe"
    elif "الم متوسط" in t:
        out["pain_level"] = "moderate"
    elif ("الم بسيط" in t) or ("الم خفيف" in t):
        out["pain_level"] = "mild"
    elif ("بدون الم" in t) or ("ما فيه الم" in t):
        out["pain_level"] = "none"

    return out

def extract_age(t: str):
    """
    يلتقط:
    - عمره 22
    - عمرها 5 سنوات
    - 22 سنة
    """
    patterns = [
        r"(?:عمره|عمرها|العمر)\s*(\d{1,3})",
        r"(\d{1,3})\s*(?:سنه|سنة|سنوات)"
    ]
    for pat in patterns:
        m = re.search(pat, t)
        if m:
            try:
                age = int(m.group(1))
                if 0 < age < 120:
                    return age
            except:
                pass
    return None


# -----------------------------
# API Routes
# -----------------------------
@app.post("/triage")
def triage_api():
    data = request.get_json(silent=True) or {}
    level, call_now, steps, notes = triage(data)

    summary = {
        "age": data.get("age"),
        "breathing": data.get("breathing"),
        "conscious": data.get("conscious"),
        "bleeding": data.get("bleeding"),
        "notes": notes
    }

    return jsonify({
        "level": level,
        "call_now": call_now,
        "steps": steps,
        "summary": summary,
        "disclaimer": "هذا تقييم أولي وليس تشخيصًا طبيًا."
    })

@app.post("/ai/extract_local")
def ai_extract_local():
    body = request.get_json(silent=True) or {}
    text = norm_text(body.get("text", ""))

    # 1) strong keyword rules first
    out = {}
    out.update(direct_keyword_rules(text))

    # 2) run ML for remaining fields
    # set defaults for fields not mentioned (guard)
    out.update(keyword_guard_defaults(text))

    # age extraction
    age = extract_age(text)
    if age is not None:
        out["age"] = age

    for field in MODEL_FIELDS:
        if field in out:
            continue
        model = MODELS.get(field)
        if not model:
            continue
        try:
            pred = model.predict([text])[0]
            out[field] = pred
        except:
            pass

    return jsonify(out)

@app.get("/health")
def health():
    return jsonify({
        "status": "ok",
        "models_loaded": len(MODELS),
        "models_expected": len(MODEL_FIELDS),
        "model_errors": MODEL_LOAD_ERRORS
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)