from pathlib import Path
import re
import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors

# ================= PATHLAR =================
BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "1.csv"  # kerak bo'lsa: "AiDATA.csv"
MODEL_DIR = BASE_DIR / "models"
MODEL_DIR.mkdir(exist_ok=True)

# ================= 1. DATASETNI YUKLASH =================
df = pd.read_csv(CSV_PATH, sep=";", encoding="utf-8-sig", engine="python")
df.columns = [c.strip() for c in df.columns]
df = df.fillna("")

# ================= 2. KERAKLI USTUNLARNI TEKSHIRISH =================
required_cols = [
    "Kasb",
    "Ish haqi",
    "Joylashuv",
    "Ish turi",
    "Bandlik turi",
    "Telefon",
    "Link",
]

missing = [c for c in required_cols if c not in df.columns]
if missing:
    raise ValueError(f"CSV ichida kerakli ustunlar yo'q: {missing}")

# ================= 3. USTUNLARNI TOZALASH =================
df["Link"] = df["Link"].astype(str).str.strip()
df["Kasb"] = df["Kasb"].astype(str).str.strip()
df["Joylashuv"] = df["Joylashuv"].astype(str).str.strip()
df["Ish haqi"] = df["Ish haqi"].astype(str).str.strip()
df["Ish turi"] = df["Ish turi"].astype(str).str.strip()
df["Bandlik turi"] = df["Bandlik turi"].astype(str).str.strip()
df["Telefon"] = df["Telefon"].astype(str).str.strip()

# ================= 4. DUPLICATE LARNI O'CHIRISH =================
df = df.drop_duplicates(
    subset=["Kasb", "Joylashuv", "Ish haqi", "Ish turi", "Bandlik turi", "Link"],
    keep="first",
).reset_index(drop=True)


# ================= 5. ISH HAQIDAN RAQAM AJRATISH =================
def extract_salary(text):
    if not text or str(text).strip() == "":
        return np.nan
    nums = re.findall(r"\d+", str(text).replace(" ", "").replace(",", ""))
    return int(nums[0]) if nums else np.nan


df["salary_num"] = df["Ish haqi"].apply(extract_salary)

# ================= 6. MATN USTUNLARINI BIRLASHTIRISH =================
df["combined_text"] = (
    (
        df["Kasb"].astype(str)
        + " "
        + df["Joylashuv"].astype(str)
        + " "
        + df["Ish turi"].astype(str)
        + " "
        + df["Bandlik turi"].astype(str)
    )
    .str.lower()
    .str.replace(r"\s+", " ", regex=True)
    .str.strip()
)

# ================= 7. TF-IDF VEKTORLASH =================
tfidf = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
tfidf_matrix = tfidf.fit_transform(df["combined_text"])

# ================= 8. NEAREST NEIGHBORS MODEL =================
nn_model = NearestNeighbors(
    n_neighbors=min(10, len(df)), metric="cosine", algorithm="brute"
)
nn_model.fit(tfidf_matrix)

# ================= 9. SAQLASH =================
joblib.dump(nn_model, MODEL_DIR / "nn_model.pkl")
joblib.dump(tfidf, MODEL_DIR / "tfidf.pkl")
joblib.dump(df, MODEL_DIR / "jobs_df.pkl")

print("✅ Model muvaffaqiyatli o'qitildi va saqlandi!")
print(f"Jami ish e'lonlari: {len(df)}")
print(f"Vektor o'lchami: {tfidf_matrix.shape}")
