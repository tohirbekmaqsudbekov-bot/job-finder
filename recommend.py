import pandas as pd
import joblib
import numpy as np

from backend import app


def recommend_jobs(
    query, location=None, job_type=None, employment_type=None, min_salary=None, top_n=5
):
    """
    query: Foydalanuvchi so'zi (masalan: "python dasturchi")
    location: Joylashuv (masalan: "toshkent")
    job_type: Ish turi (masalan: "doimiy", "masofaviy")
    employment_type: Bandlik turi (masalan: "to'liq stavka")
    min_salary: Minimal ish haqi (son, masalan: 5000000)
    """
    # Modellarni yuklash
    nn_model = joblib.load("models/nn_model.pkl")
    tfidf = joblib.load("models/tfidf.pkl")
    df = joblib.load("models/jobs_df.pkl")

    # So'rov matnini tayyorlash
    query_parts = [str(query).lower()]
    if location:
        query_parts.append(str(location).lower())
    if job_type:
        query_parts.append(str(job_type).lower())
    if employment_type:
        query_parts.append(str(employment_type).lower())

    query_text = " ".join(query_parts)

    # Vektorlash va eng yaqinini topish
    query_vec = tfidf.transform([query_text])
    distances, indices = nn_model.kneighbors(query_vec, n_neighbors=50)

    # Natijalarni DataFrame shaklida olish
    results = df.iloc[indices[0]].copy()
    # Cosine distance → similarity (1 - distance)
    results["moslik_foizi"] = (1 - distances[0]) * 100

    # FILTRLASH (foydalanuvchi istaklariga qarab)
    if location:
        results = results[
            results["Joylashuv"].str.contains(str(location).lower(), na=False)
        ]
    if job_type:
        results = results[
            results["Ish turi"].str.contains(str(job_type).lower(), na=False)
        ]
    if employment_type:
        results = results[
            results["Bandlik turi"].str.contains(str(employment_type).lower(), na=False)
        ]
    if min_salary:
        results = results[results["salary_num"] >= min_salary]

    # Agar filtrlar natijani bo'sh qilsa, hech bo'lmasa eng yaqinlarni qaytarish
    if len(results) == 0:
        results = df.iloc[indices[0]].copy()
        results["moslik_foizi"] = (1 - distances[0]) * 100

    # Kerakli ustunlarni tanlash
    output = results.head(top_n)[
        [
            "Kasb",
            "Ish haqi",
            "Joylashuv",
            "Ish turi",
            "Bandlik turi",
            "Telefon",
            "Link",
            "moslik_foizi",
        ]
    ]

    return output


# === TEST ===
if __name__ == "__main__":
    print("\n🔍 1-test: Python dasturchi Toshkentda\n")
    print(recommend_jobs(query="python dasturchi", location="toshkent", top_n=3))

    print("\n🔍 2-test: Buxgalter, to'liq stavka\n")
    print(recommend_jobs(query="buxgalter", employment_type="to'liq stavka", top_n=3))


@app.route("/recommend", methods=["POST"])
def recommend():
    print("✅ /recommend route hit bo'ldi")
    ...
