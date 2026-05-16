# backend/model/train_model.py
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
import pickle
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

from utils.preprocess import clean_text

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
dataset_path = os.path.join(BASE_DIR, "..", "dataset", "scams.csv")

df = pd.read_csv(dataset_path)
df["text"] = df["text"].astype(str).apply(clean_text)

X_train, X_test, y_train, y_test = train_test_split(
    df["text"], df["label"],
    test_size=0.2, random_state=42, stratify=df["label"]
)

# 🔥 Pipeline (vectorizer + model)
pipe = Pipeline([
    ("tfidf", TfidfVectorizer(
        ngram_range=(1,2),
        max_features=8000,
        min_df=2,
        stop_words="english"
    )),
    ("clf", LogisticRegression(
        max_iter=2000,
        class_weight="balanced"
    ))
])

pipe.fit(X_train, y_train)

# 🔍 Evaluate
y_pred = pipe.predict(X_test)
y_prob = pipe.predict_proba(X_test)

print("\n✅ Accuracy:", accuracy_score(y_test, y_pred))
print("\n📊 Report:\n", classification_report(y_test, y_pred))
print("\n🧮 Confusion Matrix:\n", confusion_matrix(y_test, y_pred))

# 🎯 Calibrate a better threshold for "scam"
# we pick threshold that maximizes F1 for scam class
labels = list(pipe.classes_)
scam_idx = labels.index("scam")

best_thr, best_f1 = 0.5, 0.0
for thr in np.linspace(0.3, 0.8, 26):
    preds = ["scam" if p[scam_idx] >= thr else "safe" for p in y_prob]
    # simple F1 for scam
    tp = sum((preds[i]=="scam" and y_test.iloc[i]=="scam") for i in range(len(preds)))
    fp = sum((preds[i]=="scam" and y_test.iloc[i]=="safe") for i in range(len(preds)))
    fn = sum((preds[i]=="safe" and y_test.iloc[i]=="scam") for i in range(len(preds)))
    precision = tp / (tp + fp + 1e-9)
    recall = tp / (tp + fn + 1e-9)
    f1 = 2 * precision * recall / (precision + recall + 1e-9)
    if f1 > best_f1:
        best_f1, best_thr = f1, thr

print(f"\n🎯 Best threshold for 'scam': {best_thr:.2f} (F1={best_f1:.3f})")

# 💾 Save artifacts
pickle.dump(pipe, open(os.path.join(BASE_DIR, "pipeline.pkl"), "wb"))
with open(os.path.join(BASE_DIR, "threshold.txt"), "w") as f:
    f.write(str(best_thr))

print("\n🚀 Pipeline + threshold saved!")