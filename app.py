from pathlib import Path
from flask import Flask, request, jsonify
import joblib
import os
import sys
import pandas as pd
import re
import requests
from flask_cors import CORS  # Qo'shildi

app = Flask(__name__)
CORS(app)

BASE_DIR = Path(__file__).resolve().parent

def load_env_file(path: Path):
    if not path.exists():
        return
    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value

load_env_file(BASE_DIR / '.env')
OPENAI_API_KEY = (
    os.environ.get('OPENAI_API_KEY', '')
    or os.environ.get('VITE_GROQ_API_KEY', '')
    or os.environ.get('VITE_GROK_API_KEY', '')
    or os.environ.get('GROK_API_KEY', '')
    or os.environ.get('OPENAI_KEY', '')
)
OPENAI_MODEL = os.environ.get('OPENAI_MODEL', 'gpt-3.5-turbo')


def get_openai_model() -> str:
    if OPENAI_API_KEY.lower().startswith('gsk_'):
        return os.environ.get('OPENAI_MODEL', 'grok-1.0')
    return OPENAI_MODEL


def call_openai_api(payload: dict, timeout: int = 30) -> str:
    if not OPENAI_API_KEY:
        return ''

    model = payload.get('model', '').lower()
    endpoint = 'https://api.openai.com/v1/chat/completions'
    payload_body = payload.copy()

    if model.startswith('grok') or OPENAI_API_KEY.lower().startswith('gsk_'):
        endpoint = 'https://api.openai.com/v1/responses'
        if 'messages' in payload_body:
            messages = payload_body.pop('messages')
            payload_body['input'] = [
                {'role': msg.get('role'), 'content': msg.get('content')}
                for msg in messages
            ]

    headers = {
        'Authorization': f'Bearer {OPENAI_API_KEY}',
        'Content-Type': 'application/json',
    }

    try:
        response = requests.post(endpoint, headers=headers, json=payload_body, timeout=timeout)
        response.raise_for_status()
        result = response.json()

        if endpoint.endswith('/responses'):
            output = result.get('output') or []
            if isinstance(output, list) and output:
                first_output = output[0]
                content = first_output.get('content')
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and item.get('type') == 'output_text':
                            text = item.get('text', '')
                            if text:
                                return text.strip()
                        if isinstance(item, str) and item.strip():
                            return item.strip()
                if isinstance(content, str) and content.strip():
                    return content.strip()
            choices = result.get('choices', [])
            if choices and isinstance(choices, list):
                first_choice = choices[0]
                if isinstance(first_choice, dict):
                    message = first_choice.get('message')
                    if isinstance(message, dict):
                        text = message.get('content')
                        if isinstance(text, str):
                            return text.strip()
                    text = first_choice.get('text')
                    if isinstance(text, str):
                        return text.strip()
            return ''

        choices = result.get('choices', [])
        if choices and isinstance(choices, list):
            message = choices[0].get('message')
            if isinstance(message, dict):
                return str(message.get('content', '')).strip()
        return ''
    except Exception as exc:
        print('OpenAI API request failed:', exc)
        return ''


def is_generic_job_query(query):
    tokens = re.findall(r"[\w']+", str(query or '').lower())
    if not tokens:
        return False

    
    return all(token in generic_words for token in tokens)


def rewrite_query_with_ai(query):
    if not query or not query.strip():
        return query
    if is_generic_job_query(query):
        return 'ish'

    if not OPENAI_API_KEY:
        return query

    prompt = (
        "Siz OLX.uz ish bo'limi uchun qisqacha va aniq qidiruv so'zlarini tanuvchi yordamchisiz. "
        "Foydalanuvchining so'rovini OLX ish qidiruviga mos kalit so'zlar yoki qisqacha iboraga o'zgartiring. "
        "Faqatgina qidiruv iborasini qaytaring."
        f"\n\nSo'rov: {query}"
    )
    payload = {
        'model': get_openai_model(),
        'messages': [
            {'role': 'system', 'content': 'Siz OLX ish qidiruviga mos so\'zlarni chiqaradigan yordamchisiz.'},
            {'role': 'user', 'content': prompt},
        ],
        'max_tokens': 40,
        'temperature': 0.2,
    }
    result = call_openai_api(payload, timeout=15)
    if not result:
        return query

    phrase = result.splitlines()[0].strip()
    phrase = re.sub(r'["“”‘’]+', '', phrase)
    phrase = re.sub(r'[\.:,;]+$', '', phrase).strip()
    if not phrase:
        return query
    return phrase

# Modellarni bir marta yuklash (search in project root then backend/models)
MODEL_DIR = BASE_DIR / 'models'
if not MODEL_DIR.exists():
    alt = BASE_DIR / 'backend' / 'models'
    if alt.exists():
        MODEL_DIR = alt

def _load_model_file(name: str):
    path = MODEL_DIR / name
    if not path.exists():
        print(f"Model file not found: {path}")
        raise FileNotFoundError(f"Model file not found: {path}")
    return joblib.load(path)

try:
    nn_model = _load_model_file('nn_model.pkl')
    tfidf = _load_model_file('tfidf.pkl')
    df = _load_model_file('jobs_df.pkl')
except FileNotFoundError as e:
    print(e)
    print(f"Looked for models in: {MODEL_DIR}")
    print('If you do not have prebuilt models, run the training script or copy the backend/models directory here.')
    sys.exit(1)


def extract_search_tokens(text):
    tokens = re.findall(r"[\w']+", str(text or '').lower())
    return [token for token in tokens if len(token) >= 3]


def token_match_series(series, tokens):
    lower_series = series.astype(str).str.lower()
    return lower_series.apply(lambda value: any(token in value for token in tokens))




@app.route("/recommend", methods=["POST"])
def recommend():
    data = request.json or {}

    query = str(data.get("query", "") or "").strip()
    location = str(data.get("location", "") or "")
    job_type = str(data.get("job_type", "") or "")
    employment_type = str(data.get("employment_type", "") or "")
    min_salary = data.get("min_salary")
    top_n = int(data.get("top_n", 5) or 5)

    query = rewrite_query_with_ai(query)

    parts = [query.lower()]
    if location:
        parts.append(location.lower())
    if job_type:
        parts.append(job_type.lower())
    if employment_type:
        parts.append(employment_type.lower())

    query_text = " ".join(parts)
    query_vec = tfidf.transform([query_text])

    query_tokens = extract_search_tokens(query)
    distances, indices = nn_model.kneighbors(query_vec, n_neighbors=50)
    results = df.iloc[indices[0]].copy()
    results["moslik_foizi"] = round((1 - distances[0]) * 100, 2)

    if location:
        results = results[
            results["Joylashuv"].astype(str).str.lower().str.contains(location.lower(), na=False)
        ]
    if job_type:
        results = results[
            results["Ish turi"].astype(str).str.lower().str.contains(job_type.lower(), na=False)
        ]
    if employment_type:
        results = results[
            results["Bandlik turi"].astype(str).str.lower().str.contains(employment_type.lower(), na=False)
        ]
    if min_salary:
        try:
            results = results[results["salary_num"].fillna(0) >= float(min_salary)]
        except (ValueError, TypeError):
            pass

    if query_tokens.any() if hasattr(query_tokens, 'any') else query_tokens:
        mask = token_match_series(results["Kasb"], query_tokens)
        if not mask.any():
            mask = token_match_series(results["Ish turi"], query_tokens)
        if not mask.any():
            mask = token_match_series(results["Bandlik turi"], query_tokens)
        if mask.any():
            results = results[mask]

    if len(results) == 0:
        results = df.iloc[indices[0]].copy()
        results["moslik_foizi"] = round((1 - distances[0]) * 100, 2)

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
    ].to_dict(orient="records")

    return jsonify({"status": "success", "count": len(output), "recommendations": output})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
