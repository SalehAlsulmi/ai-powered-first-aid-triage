import os
import joblib
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

os.makedirs("models", exist_ok=True)

TRAIN = {
    "breathing": [
        # from bigger set
        ("يتنفس طبيعي", "yes"),
        ("تنفسه طبيعي", "yes"),
        ("يتنفس عادي", "yes"),
        ("التنفس طبيعي", "yes"),
        ("يتنفس", "yes"),
        ("لا يتنفس", "no"),
        ("ما يتنفس", "no"),
        ("انقطاع تنفس", "no"),
        ("صعوبة تنفس", "abnormal"),
        ("ضيق تنفس", "abnormal"),
        ("يتنفس بصعوبة", "abnormal"),
        ("تنفس غير طبيعي", "abnormal"),
        ("التنفس غير طبيعي", "abnormal"),
        ("يتنفس بسرعة", "abnormal"),
        ("تنفسه سريع", "abnormal"),
        ("يكتم", "abnormal"),
        ("مخنوق", "abnormal"),
        ("ينهج", "abnormal"),
        ("ما يقدر يتنفس", "no"),
        ("وقف تنفسه", "no"),
        ("يتنفس بصعوبة وكأنه يختنق", "abnormal"),
        ("تنفسه سريع ومتعب", "abnormal"),
        ("ما يقدر يتنفس زين", "abnormal"),
        ("يتنفس طبيعي الحمدلله", "yes"),
    ],

    "conscious": [
        # from bigger set
        ("واعي", "yes"),
        ("يرد علينا", "yes"),
        ("يتكلم", "yes"),
        ("يتجاوب", "yes"),
        ("فاقد وعي", "no"),
        ("اغمى عليه", "no"),
        ("مغمي عليه", "no"),
        ("ما يرد", "no"),
        ("غير واعي", "no"),
        ("ما يحس", "no"),
        ("غايب عن الوعي", "no"),
        ("ما يستجيب", "no"),
        ("يرد بصعوبة", "yes"),
        ("فاتح عيونه", "yes"),
        ("يتكلم طبيعي", "yes"),
        ("اغمى عليه فجأة", "no"),
        ("ما يستجيب إذا ناديناه", "no"),
        ("واعي ويتكلم طبيعي", "yes"),
        ("يرد علينا ويتجاوب", "yes"),
    ],

    "bleeding": [
        # none (bigger set)
        ("طاح", "none"),
        ("وقع", "none"),
        ("دوخة", "none"),
        ("الم بسيط", "none"),
        ("الم متوسط", "none"),
        ("بدون دم", "none"),
        ("ما فيه دم", "none"),
        ("لا يوجد نزيف", "none"),
        ("ما فيه نزيف", "none"),
        ("بدون نزيف", "none"),
        ("ما فيه دم ولا نزيف", "none"),

        # mild/severe examples mixed in bigger set
        ("يده فيها جرح وينزف شوي", "mild"),
        ("فيه دم خفيف ينقط", "mild"),
        ("نزيف قوي وما يوقف", "severe"),
        ("دم كثير مرة", "severe"),

        # mild (bigger set)
        ("نزيف بسيط", "mild"),
        ("دم بسيط", "mild"),
        ("جرح ينزف شوي", "mild"),
        ("دم خفيف", "mild"),
        ("ينزف شوي", "mild"),
        ("جرح صغير وينزف", "mild"),
        ("نقطة دم", "mild"),
        ("فيه دم بسيط", "mild"),
        ("جرح مفتوح بسيط", "mild"),

        # ✅ added from smaller set
        ("نزف خفيف", "mild"),

        # severe (bigger set)
        ("نزيف شديد", "severe"),
        ("دم كثير", "severe"),
        ("النزيف ما يوقف", "severe"),
        ("ينزف بقوة", "severe"),
    ],

    "dizziness": [
        # from bigger set
        ("دوخة", "yes"),
        ("دوار", "yes"),
        ("يدوخ", "yes"),
        ("يحس بدوخة", "yes"),
        ("ما فيه دوخة", "no"),
        ("بدون دوخة", "no"),
        ("ما يحس بدوخة", "no"),
        ("حاس بدوخة", "yes"),
        ("راسـه يلف", "yes"),
        ("يحس بدوران", "yes"),
        ("ما يقدر يوقف من الدوخة", "yes"),
        ("يتلخبط", "yes"),
        ("بدون دوار", "no"),
        ("حاس بدوخة قوية", "yes"),
        ("راسـه يلف وما يقدر يوقف", "yes"),
        ("يحس بدوار بعد ما قام", "yes"),
        ("ما فيه دوخة أبداً", "no"),
    ],

    "vomiting": [
        # from bigger set
        ("قيء", "yes"),
        ("استفراغ", "yes"),
        ("يتقيأ", "yes"),
        ("تقيؤ", "yes"),
        ("ما فيه قيء", "no"),
        ("بدون استفراغ", "no"),
        ("ما يتقيأ", "no"),
        ("يتقيأ من الصباح", "yes"),
        ("رجع كل اللي أكله", "yes"),
        ("صار له ساعتين يستفرغ", "yes"),
        ("ما فيه استفراغ", "no"),
        ("ما رجع ولا مرة", "no"),

        # ✅ added gulf words + negations from smaller set
        ("تطريش", "yes"),
        ("يطرش", "yes"),
        ("طرش", "yes"),
        ("طرّش", "yes"),
        ("ترجيع", "yes"),
        ("يرجع", "yes"),
        ("ما يطرش", "no"),
        ("بدون طرش", "no"),
        ("ما يرجع", "no"),
    ],

    "chest_pain": [
        # from bigger set
        ("ألم صدر شديد", "yes"),
        ("الم بالصدر", "yes"),
        ("وجع صدر", "yes"),
        ("ضيق صدر", "yes"),
        ("ما فيه ألم صدر", "no"),
        ("بدون ألم صدر", "no"),
        ("يحس بألم قوي بالصدر", "yes"),
        ("ضيق صدر مع ألم", "yes"),
        ("بدون ضيق صدر", "no"),
    ],

    "pain_level": [
        # from bigger set
        ("بدون ألم", "none"),
        ("ما فيه ألم", "none"),
        ("الم خفيف", "mild"),
        ("الم بسيط", "mild"),
        ("الم متوسط", "moderate"),
        ("يوجعه", "moderate"),
        ("الم شديد", "severe"),
        ("يوجعه مرة", "severe"),
        ("يوجعه مره", "severe"),
        ("يوجعه مرة وما يقدر يتحرك", "severe"),
        ("الألم متوسط ويزيد مع الحركة", "moderate"),
        ("ألم خفيف بس مزعج", "mild"),
    ],
}

# -----------------------------
# De-duplicate pairs safely
# (keeps first occurrence order)
# -----------------------------
def dedupe_pairs(pairs):
    seen = set()
    out = []
    for text, label in pairs:
        key = (text.strip(), label.strip())
        if key in seen:
            continue
        seen.add(key)
        out.append((text, label))
    return out

for k in list(TRAIN.keys()):
    TRAIN[k] = dedupe_pairs(TRAIN[k])

# -----------------------------
# Train + Save
# -----------------------------
def train_field(pairs):
    X = [t for t, y in pairs]
    y = [y for t, y in pairs]
    return Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2))),
        ("clf", LogisticRegression(max_iter=2000))
    ]).fit(X, y)

for field, pairs in TRAIN.items():
    model = train_field(pairs)
    joblib.dump(model, f"models/{field}.joblib")

print("✅ Done: merged models saved in ./models/")