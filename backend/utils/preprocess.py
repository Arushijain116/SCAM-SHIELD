# backend/utils/preprocess.py
import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# one-time downloads (safe to call; cached after first run)
nltk.download('stopwords')
nltk.download('wordnet')

stop_words = set(stopwords.words("english"))
lemmatizer = WordNetLemmatizer()

def clean_text(text: str) -> str:
    if not text:
        return ""

    text = text.lower()

    # normalize URLs, numbers
    text = re.sub(r"http\S+|www\S+", " url ", text)
    text = re.sub(r"\d+", " num ", text)

    # keep letters
    text = re.sub(r"[^a-z\s]", " ", text)

    tokens = text.split()

    tokens = [
        lemmatizer.lemmatize(w)
        for w in tokens
        if w not in stop_words and len(w) > 2
    ]

    return " ".join(tokens)