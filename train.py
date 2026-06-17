import pandas as pd
import numpy as np
import re
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors

# 1. Datasetni yuklash
df = pd.read_csv("data/ish_elonlari.csv")

# 2. Tozalash
df = df.fillna("")


# Ish haqidan faqat raqamni ajratib olish (agar '5 000 000' yoki '5000000' bo'lsa)
def extract_salary(text):
    if not text or text == "":
        return np.nan
    # Barcha bo'sh joy va vergullarni olib tashlab, raqamlarni topish
    nums = re.findall(
        r"\d+", str(text).replace(" ", "").replace(",", "").replace(".", "")
    )
    if nums:
        # Agar katta son bo'lsa (masalan 5000000), shunday qaytaradi
        return int(nums[0])
    return np.nan


df["salary_num"] = df["Ish haqi"].apply(extract_salary)

# Matn ustunlarini birlashtirish uchun tozalash
for col in ["Kasb", "Joylashuv", "Ish turi", "Bandlik turi"]:
    df[col] = df[col].astype(str).str.lower()

# 3. Asosiy matn ustunini yaratish (Kasb + Joylashuv + Ish turi + Bandlik turi)
df["combined_text"] = (
    df["Kasb"] + " " + df["Joylashuv"] + " " + df["Ish turi"] + " " + df["Bandlik turi"]
)

# 4. TF-IDF vektorizatsiya
tfidf = TfidfVectorizer(
    max_features=5000,
    ngram_range=(1, 2),  # 1 va 2 so'zli kombinatsiyalar
    min_df=1,  # Kamida 1 marta uchragan so'zlar
    stop_words=None,  # O'zbek tiliga mos stop-wordlar kerak bo'lsa, ro'yxat qo'shasiz
)

tfidf_matrix = tfidf.fit_transform(df["combined_text"])

# 5. NearestNeighbors modeli (Cosine o'xshashligi bo'yicha)
nn_model = NearestNeighbors(
    n_neighbors=20,  # Har doim 20 ta yaqinini topamiz, keyin filtrlaymiz
    metric="cosine",
    algorithm="brute",
)
nn_model.fit(tfidf_matrix)

# 6. Saqlash
joblib.dump(nn_model, "models/nn_model.pkl")
joblib.dump(tfidf, "models/tfidf.pkl")
joblib.dump(df, "models/jobs_df.pkl")

print("✅ Model muvaffaqiyatli o'qitildi va saqlandi!")
print(f"Jami ish e'lonlari: {len(df)}")
print(f"Vektor o'lchami: {tfidf_matrix.shape}")
