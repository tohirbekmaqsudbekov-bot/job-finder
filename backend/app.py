from pathlib import Path
import os
import joblib
import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent

MODEL_DIR = BASE_DIR / "models"

request_history = {}


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
load_env_file(BASE_DIR.parent / '.env')

FRONTEND_ORIGINS = [
    origin.strip()
    for origin in os.environ.get(
        "FRONTEND_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,https://your-app.netlify.app",
    ).split(",")
    if origin.strip()
]
CORS(app, origins=FRONTEND_ORIGINS, supports_credentials=True)

RATE_LIMIT_WINDOW = int(os.environ.get("RATE_LIMIT_WINDOW", "60"))
RATE_LIMIT_MAX = int(os.environ.get("RATE_LIMIT_MAX", "30"))

nn_model = None
tfidf = None
df = None
models_loaded = False


def get_client_ip() -> str:
    forwarded = request.headers.get('X-Forwarded-For', '')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.remote_addr or 'unknown'


def sanitize_text(value: str, max_length: int = 1200) -> str:
    if not isinstance(value, str):
        value = str(value or '')
    value = value.strip()
    value = re.sub(r'[\x00-\x1f\x7f]+', ' ', value)
    return value[:max_length]


def sanitize_int(value, default: int, min_value: int, max_value: int) -> int:
    try:
        number = int(float(value))
    except (TypeError, ValueError):
        return default
    return max(min_value, min(max_value, number))


@app.before_request
def enforce_rate_limit():
    client_ip = get_client_ip()
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW
    request_history.setdefault(client_ip, [])
    request_history[client_ip] = [ts for ts in request_history[client_ip] if ts >= window_start]
    if len(request_history[client_ip]) >= RATE_LIMIT_MAX:
        return jsonify({'status': 'error', 'message': 'Too many requests, please try again later.'}), 429
    request_history[client_ip].append(now)
GROK_API_KEY = (
    os.environ.get('OPENAI_API_KEY', '')
    or os.environ.get('VITE_GROK_API_KEY', '')
    or os.environ.get('GROK_API_KEY', '')
)
GROK_MODEL = os.environ.get('OPENAI_MODEL', 'gpt-3.5-turbo')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')


def load_models() -> bool:
    global nn_model, tfidf, df, models_loaded
    if models_loaded:
        return True
    try:
        nn_model = joblib.load(MODEL_DIR / "nn_model.pkl")
        tfidf = joblib.load(MODEL_DIR / "tfidf.pkl")
        df = joblib.load(MODEL_DIR / "jobs_df.pkl")
        models_loaded = True
        return True
    except FileNotFoundError as exc:
        print('Model files not found, OLX-only mode will still work:', exc)
        return False
    except Exception as exc:
        print('Failed to load model files:', exc)
        return False


def get_openai_model() -> str:
    if GROK_API_KEY and GROK_API_KEY.lower().startswith('gsk_'):
        return os.environ.get('OPENAI_MODEL', 'grok-1.0')
    return GROK_MODEL


def call_openai_api(payload: dict, timeout: int = 20) -> str:
    if not GROK_API_KEY:
        return ''
    model = payload.get('model', '').lower()
    endpoint = 'https://api.openai.com/v1/chat/completions'
    body = payload.copy()
    if model.startswith('grok') or GROK_API_KEY.lower().startswith('gsk_'):
        endpoint = 'https://api.openai.com/v1/responses'
        if 'messages' in body:
            messages = body.pop('messages')
            body['input'] = [{'role': m.get('role'), 'content': m.get('content')} for m in messages]

    headers = {'Authorization': f'Bearer {GROK_API_KEY}', 'Content-Type': 'application/json'}
    try:
        resp = requests.post(endpoint, headers=headers, json=body, timeout=timeout)
        resp.raise_for_status()
        result = resp.json()
        if endpoint.endswith('/responses'):
            # Grok-like response parsing
            output = result.get('output') or []
            if isinstance(output, list) and output:
                first = output[0]
                content = first.get('content')
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and item.get('type') == 'output_text':
                            return item.get('text', '').strip()
                        if isinstance(item, str) and item.strip():
                            return item.strip()
                if isinstance(content, str) and content.strip():
                    return content.strip()
            # fallback to choices
            choices = result.get('choices', [])
            if choices and isinstance(choices, list):
                first = choices[0]
                msg = first.get('message') or {}
                if isinstance(msg, dict):
                    return str(msg.get('content', '')).strip()
                return str(first.get('text', '')).strip()

        # OpenAI chat completions path
        choices = result.get('choices', [])
        if choices and isinstance(choices, list):
            message = choices[0].get('message')
            if isinstance(message, dict):
                return str(message.get('content', '')).strip()
        return ''
    except Exception as exc:
        print('OpenAI/Grok request failed:', exc)
        return ''


def extract_job_keywords_advanced(query: str) -> str:
    """Extract job-related keywords from Uzbek query using pattern matching."""
    if not query:
        return ""
    
    normalized = normalize_text(query)
    keywords = []
    
    # Check for programming languages and technical roles
    tech_keywords = [
        'python', 'java', 'javascript', 'nodejs', 'react', 'django', 'flask',
        'frontend', 'backend', 'fullstack', 'developer', 'dasturchi', 'programmer',
        'admin', 'administrator', 'tarmoq', 'tizim', 'sistem', 'network',
        'database', 'sql', 'mongodb', 'devops', 'docker', 'kubernetes',
        'aws', 'azure', 'cloud', 'security', 'qa', 'tester', 'engineer',
        'analyst', 'menajeri', 'manager', 'sales', 'sotuvchi', 'marketing',
        'ui', 'ux', 'design', 'grafik', 'web', 'mobile', 'android', 'ios'
    ]
    
    for keyword in tech_keywords:
        if keyword in normalized:
            keywords.append(keyword)
    
    return ' '.join(keywords) if keywords else ""


def call_gemini_api(query: str, timeout: int = 10) -> dict:
    """Call Gemini API to analyze job search query and extract job title + location.
    
    This provides intelligent query analysis. If API fails, returns empty dict 
    and backend falls back to standard normalization.
    """
    if not GEMINI_API_KEY or not query:
        return {}
    
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        
        prompt = f"""Analyze Uzbek job search query. Return ONLY JSON (no markdown):
Query: "{query}"
{{"job_title": "job name", "location": "city or empty", "search_phrase": "combined keywords"}}

Examples:
- "men python bilaman ish ber" -> {{"job_title": "python developer", "location": "", "search_phrase": "python"}}
- "tarmoq admin Toshkent" -> {{"job_title": "tarmoq administratori", "location": "toshkent", "search_phrase": "tarmoq administratori toshkent"}}
"""
        
        headers = {'Content-Type': 'application/json'}
        body = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.1, "maxOutputTokens": 150}
        }
        
        resp = requests.post(url, headers=headers, json=body, timeout=timeout)
        
        if resp.status_code == 200:
            result = resp.json()
            if "candidates" in result and len(result["candidates"]) > 0:
                candidate = result["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    text = candidate["content"]["parts"][0].get("text", "").strip()
                    import json
                    try:
                        # Extract JSON from response
                        json_match = re.search(r'\{[^}]+\}', text)
                        if json_match:
                            parsed = json.loads(json_match.group())
                            if parsed.get("search_phrase"):
                                print(f"[Gemini] Analysis: job={parsed.get('job_title')}, loc={parsed.get('location')}, phrase={parsed.get('search_phrase')}")
                                return parsed
                    except (json.JSONDecodeError, AttributeError):
                        pass
        
        return {}
    except Exception as exc:
        print(f'[Gemini] Error: {exc}')
        return {}



def extract_search_tokens(text: str) -> list:
    tokens = re.findall(r"[\w']+", str(text or '').lower())
    return [t for t in tokens if len(t) >= 3]


def smart_extract_query(query: str) -> tuple:
    """
    Intelligently extract job title and location from natural language query.
    No fixed synonyms - uses semantic understanding instead.
    Returns (search_phrase, location, job_title)
    """
    if not query:
        return ("", "", "")
    
    normalized = normalize_text(query)
    
    # Extract location
    location = extract_location_from_query(query)
    
    # Remove location from query for cleaner job extraction
    query_without_location = normalized
    if location:
        for variant in get_location_variants(location):
            query_without_location = re.sub(rf'\b{variant}(da|dan|dagi|ga|de|den)?\b', '', query_without_location)
    
    # Extract all meaningful tokens (not generic words)
    tokens = [t for t in extract_search_tokens(query_without_location) if t not in GENERIC_QUERY_WORDS]
    
    if not tokens:
        return ("", location, "")
    
    # Create search phrase from tokens
    search_phrase = ' '.join(tokens)
    if location and location not in search_phrase:
        search_phrase = f"{search_phrase} {location}".strip()
    
    # Job title is the meaningful tokens
    job_title = ' '.join(tokens[:3]) if tokens else ""
    
    return (search_phrase, location, job_title)




LOCATION_KEYWORDS = {
    'toshkent', 'samarqand', 'andijon', 'namangan', 'fergana', 'buxoro', 'navoiy', 'xorazm', 'urganch',
    'qarshi', 'termez', 'jizzax', 'sirdaryo', 'nukus', 'surxondaryo', 'namangan', 'qo`qon', 'qarshi',
}

# Uzbek (Latin) to Russian/Cyrillic city name mapping for OLX matching
LOCATION_CYRILLIC_VARIANTS = {
    'toshkent': ['ташкент', 'tashkent'],
    'samarqand': ['самарканд', 'samarkand'],
    'andijon': ['андиджан', 'andijan'],
    'namangan': ['наманган', 'namangan'],
    'fergana': ['фергона', 'ferghana'],
    'buxoro': ['бухара', 'bukhara'],
    'navoiy': ['навои', 'navoi'],
    'xorazm': ['хорезм', 'khorezm'],
    'urganch': ['ургенч', 'urgench'],
    'qarshi': ['карши', 'karshi'],
    'termez': ['термез', 'termez'],
    'jizzax': ['джизак', 'jizzakh'],
    'sirdaryo': ['сырдарья', 'sirdaryo'],
    'nukus': ['нукус', 'nukus'],
    'surxondaryo': ['сурхандарья', 'surkhandarya'],
    'qo`qon': ['коканд', 'kokand'],
}


def get_location_variants(location_name: str) -> list:
    """Get all variants (Uzbek + Cyrillic) of a location for matching."""
    if not location_name:
        return []
    normalized = location_name.lower().strip()
    # If it's a known Uzbek location, return its variants
    if normalized in LOCATION_CYRILLIC_VARIANTS:
        return [normalized] + LOCATION_CYRILLIC_VARIANTS[normalized]
    # Otherwise return just the normalized version
    return [normalized]


def normalize_text(text: str) -> str:
    if not text:
        return ''

    normalized = str(text).lower()
    normalized = re.sub(r'["“”‘’…\.,:;!?(){}\[\]/\\]+', ' ', normalized)
    normalized = re.sub(r"\s+", ' ', normalized).strip()
    if has_cyrillic(normalized):
        normalized = transliterate_cyrillic_to_latin(normalized)
    return normalized


def replace_synonyms(text: str) -> str:
    """Replace only critical synonyms. Rely on smart extraction otherwise."""
    normalized = normalize_text(text)
    if not normalized:
        return ''

    # Only replace truly critical cases
    replacements = {
        'programmer': 'dasturchi',
        'developer': 'dasturchi',
    }
    
    for old, new in replacements.items():
        normalized = re.sub(rf'\b{old}\b', new, normalized)
    
    return normalized


def extract_location_from_query(query: str) -> str:
    normalized = normalize_text(query)
    for city in LOCATION_KEYWORDS:
        if city in normalized:
            return city
        if f"{city}da" in normalized or f"{city}dan" in normalized or f"{city}dagi" in normalized or f"{city}ga" in normalized or f"{city}ga" in normalized:
            return city
    return ''


def normalize_location_tokens(text: str, location: str) -> str:
    if not text or not location:
        return text

    pattern = rf"\b{re.escape(location)}(?:da|dan|dagi|ga|ga|de|den)?\b"
    return re.sub(pattern, location, text)


def remove_location_tokens(text: str, location: str) -> str:
    if not text or not location:
        return text

    pattern = rf"\b{re.escape(location)}(?:da|dan|dagi|ga|ga|de|den)?\b"
    return re.sub(pattern, '', text).strip()


def normalize_user_query(query: str) -> str:
    """Normalize query using smart extraction instead of fixed synonyms."""
    search_phrase, location, job_title = smart_extract_query(query)
    return search_phrase if search_phrase else normalize_text(query)


GENERIC_QUERY_WORDS = {
    'ish', 'ishlar', 'ishini', 'ishga', 'qidir', 'qidirar', 'qidiray', 'qidiraman', 'qidiryapman', 'qidirayapman', 'qidirayotgan', 'qidiryapsiz', 'qidiryapti',
    'izlayman', 'izlayapman', 'izlayapsiz', 'izlamoq', 'topish', 'topmoq', 'topmoqdaman', 'topdim',
    'vakansiya', 'vakansiyalar', 'job', 'jobs', 'barcha', 'har', 'xil', 'harxil', 'kerak', 'chiqsin',
    'faqat', 'menga', 'men', 'meni', 'mening', 'sohasida', 'bo\'yicha', 'bilan', 'va', 'ham', 'uchun', 'shunday',
    'ha', 'bor', 'yo\'q', 'qilib', 'qilsam', 'bo\'lsa', 'bo\'lmasa', 'lozim', 'kabi', 'buni', 'qaysi', 'qayer',
    'man', 'mavjud', 'hozir', 'keyin', 'yoki', 'qaerda', 'qayerda', 'yaqin', 'ba\'zi', 'ular', 'ularni', 'ularga',
    'qidir', 'qidirar', 'qidiray', 'qidiraman', 'qidiryapman', 'qidirayapman', 'qidirayotgan', 'qidiryapsiz', 'qidiryapti',
    'qil', 'hamda', 'yana', 'boshqa', 'shu', 'juda', 'hali', 'chunki', 'buyuk', 'many', 'his', 'an', 'the', 'to', 'for', 'on', 'in', 'of'
}

JOB_ROLE_KEYWORDS = {
    'tarmoq', 'administrator', 'admin', 'sistem', 'system', 'dasturchi', 'programmer', 'developer', 'frontend',
    'backend', 'menejer', 'manager', 'sotuvchi', 'buxgalter', 'marketing', 'support', 'texnik', 'technical',
    'services', 'servis', 'analyst', 'analitik', 'ux', 'ui', 'web', 'mobile', 'it', 'network', 'ga', 'da', 'uz',
    'ishonch', 'mentor'
}


def get_query_keywords(query: str) -> list:
    tokens = extract_search_tokens(query)
    if not tokens:
        return []
    keywords = [t for t in tokens if t not in GENERIC_QUERY_WORDS and len(t) >= 3]
    return keywords


def extract_job_phrase(query: str) -> str:
    tokens = extract_search_tokens(query)
    if not tokens:
        return ""

    # First try to find a role-related keyword and return surrounding tokens.
    for idx, token in enumerate(tokens):
        if token in JOB_ROLE_KEYWORDS:
            start = max(0, idx - 2)
            end = min(len(tokens), idx + 3)
            phrase = " ".join(tokens[start:end])
            return phrase

    # If no explicit role word, return a short phrase of the most important tokens.
    filtered = [t for t in tokens if t not in GENERIC_QUERY_WORDS]
    if filtered:
        # Prefer longer tokens first, but preserve order of first occurrences
        ordered = sorted(filtered, key=lambda x: (-len(x), filtered.index(x)))
        return " ".join(ordered[:5])

    return ""


def has_cyrillic(text: str) -> bool:
    return bool(re.search(r"[\u0400-\u04FF]", text or ""))


def transliterate_cyrillic_to_latin(text: str) -> str:
    mapping = {
        'а': 'a', 'б': 'b', 'д': 'd', 'е': 'e', 'ё': 'yo', 'ж': 'j', 'з': 'z', 'и': 'i', 'й': 'y',
        'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't',
        'у': 'u', 'ф': 'f', 'х': 'x', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch', 'ъ': '', 'ы': 'i',
        'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
        'ғ': 'g', 'қ': 'q', 'ҳ': 'h', 'ў': 'o', 'ё': 'yo',
        'А': 'A', 'Б': 'B', 'Д': 'D', 'Е': 'E', 'Ё': 'Yo', 'Ж': 'J', 'З': 'Z', 'И': 'I', 'Й': 'Y',
        'К': 'K', 'Л': 'L', 'М': 'M', 'Н': 'N', 'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T',
        'У': 'U', 'Ф': 'F', 'Х': 'X', 'Ц': 'Ts', 'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Shch', 'Ъ': '', 'Ы': 'I',
        'Ь': '', 'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya',
        'Ғ': 'G', 'Қ': 'Q', 'Ҳ': 'H', 'Ў': 'O',
    }
    return ''.join(mapping.get(ch, ch) for ch in text)


def prepare_query_for_olx(query: str) -> str:
    """Prepare a concise OLX-friendly search phrase from the user's query.

    Strategy:
    - Prefer extracted keywords from `get_query_keywords` when available.
    - Otherwise, extract a short role-related phrase from the query.
    - Fallback to the first few words of the normalized query.
    """
    if not query:
        return ""

    kws = get_query_keywords(query)
    if kws:
        phrase = " ".join(kws)
        return phrase[:120].strip()

    job_phrase = extract_job_phrase(query)
    if job_phrase:
        return job_phrase[:120].strip()

    s = re.sub(r'["“”‘’…\.,:;!?(){}\[\]/\\]+', ' ', query)
    s = re.sub(r"\s+", ' ', s).strip()
    parts = s.split()
    return ' '.join(parts[:6]).strip()


def get_olx_search_terms(query: str) -> list:
    terms = []
    if not query:
        return terms

    normalized = normalize_user_query(query)
    if not normalized:
        return terms

    prepared = prepare_query_for_olx(normalized)
    if prepared and prepared not in terms:
        terms.append(prepared)

    short_phrase = ' '.join(prepared.split()[:3]) if prepared else ''
    if short_phrase and short_phrase not in terms:
        terms.append(short_phrase)

    cleaned_tokens = [t for t in extract_search_tokens(normalized) if t not in GENERIC_QUERY_WORDS]
    cleaned_phrase = ' '.join(cleaned_tokens[:5])
    if cleaned_phrase and cleaned_phrase not in terms:
        terms.append(cleaned_phrase)

    if has_cyrillic(normalized):
        translit = transliterate_cyrillic_to_latin(normalized)
        if translit and translit not in terms:
            terms.append(translit)

    if normalized not in terms:
        terms.append(normalized)

    return [t for t in terms if t]



def score_olx_result(item: dict, query: str) -> int:
    if not query:
        return 0

    query_text = str(query or '').lower()
    keywords = [t for t in get_query_keywords(query_text) if len(t) > 2]
    text = ' '.join([
        str(item.get('Kasb', '')).lower(),
        str(item.get('Joylashuv', '')).lower(),
        str(item.get('Ish turi', '')).lower(),
        str(item.get('Bandlik turi', '')).lower(),
    ])

    score = 0
    for kw in keywords:
        if kw in text:
            score += 5 if len(kw) >= 5 else 2
            if text.startswith(kw) or text.endswith(kw):
                score += 2

    if query_text in text:
        score += 10

    return score



def create_session():
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        }
    )
    return session


def build_olx_url(query: str = "", page: int = 1) -> str:
    base = "https://www.olx.uz/d/rabota/"
    if query:
        query_slug = quote_plus(query.strip().lower().replace(" ", "-"))
        return f"{base}q-{query_slug}/?page={page}"
    return f"{base}?page={page}"


def get_olx_listing_link_and_title(listing):
    best_anchor = None

    for anchor in listing.find_all("a", href=True):
        href = anchor["href"].strip()
        if not href or href.startswith("#") or href.startswith("javascript:"):
            continue

        if "/d/rabota/" in href or href.startswith("/d/") or href.startswith("https://www.olx.uz/d/"):
            best_anchor = anchor
            break

        if best_anchor is None:
            best_anchor = anchor

    if best_anchor is None:
        return None, None

    link = best_anchor["href"].strip()
    if link and not link.startswith("http"):
        link = f"https://www.olx.uz{link}"

    title = best_anchor.get_text(" ", strip=True)
    return link, title


def scrape_olx(query: str = "", location: str = "", job_type: str = "", top_n: int = 5, max_pages: int = 3):
    session = create_session()
    seen_links = set()
    jobs = []
    page = 1

    while page <= max_pages and len(jobs) < top_n:
        url = build_olx_url(query, page)
        try:
            resp = session.get(url, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
        except Exception as e:
            print(f"OLX fetch error page {page}: {e}")
            break

        listings = soup.find_all("div", {"data-cy": "l-card"})
        if not listings:
            listings = soup.select("div[data-cy='l-card'], li[data-cy='l-card'], article")
        if not listings:
            print(f"OLX page {page} parsing found no listings")
            break

        for listing in listings:
            if len(jobs) >= top_n:
                break

            link, title = get_olx_listing_link_and_title(listing)
            if not link or not title:
                continue
            if link in seen_links or "/list/user" in link:
                continue
            seen_links.add(link)

            salary = "Noma'lum"
            salary_elem = listing.find("p", class_="css-3xwpr4")
            if salary_elem:
                salary = salary_elem.get_text(" ", strip=True)
            else:
                text = listing.get_text(" ", strip=True)
                salary_match = re.search(r"\d[\d\s,.]*\s*(?:сум|у\.е\.|у\.е\.|usd|dollar|сум\b)", text, flags=re.IGNORECASE)
                if salary_match:
                    salary = salary_match.group(0).strip()

            info_tags = [tag.get_text(" ", strip=True) for tag in listing.find_all("p", class_="css-1gwti7f")]
            joylashuv = info_tags[0] if len(info_tags) > 0 else ""
            ish_turi = info_tags[1] if len(info_tags) > 1 else ""
            bandlik_turi = info_tags[2] if len(info_tags) > 2 else ""

            if location:
                # Check if any variant of the location appears in joylashuv
                location_variants = get_location_variants(location)
                joylashuv_lower = joylashuv.lower()
                if not any(variant in joylashuv_lower for variant in location_variants):
                    continue
            if job_type and job_type.lower() not in (ish_turi + " " + bandlik_turi).lower():
                continue

            jobs.append(
                {
                    "Kasb": title,
                    "Ish haqi": salary,
                    "Joylashuv": joylashuv,
                    "Ish turi": ish_turi,
                    "Bandlik turi": bandlik_turi,
                    "Telefon": "Ko'rsatilmadi",
                    "Link": link,
                }
            )

        page += 1

    return jobs[:top_n]

# Model fayllarni hozircha yuklamaymiz; kerak bo'lsa keyin yuklaymiz.


@app.route("/")
def home():
    return "Job Finder AI server ishlayapti!"


@app.route("/ai-response", methods=["POST"])
def ai_response():
    data = request.json or {}
    message = str(data.get("message", "")).strip()
    jobs = data.get("jobs", [])

    print(f"[backend] /ai-response hit: message={message!r}, jobs_count={len(jobs) if isinstance(jobs, list) else 'invalid'}")

    if not message or not isinstance(jobs, list):
        return jsonify({"status": "error", "message": "Invalid request"}), 400

    if OPENAI_API_KEY and jobs:
        job_texts = []
        for idx, job in enumerate(jobs[:5], start=1):
            title = str(job.get("Kasb") or job.get("kasb") or "Noma'lum ish")
            location = str(job.get("Joylashuv") or job.get("joylashuv") or "Noma'lum joy")
            salary = str(job.get("Ish haqi") or job.get("ish haqi") or "Ma'lumot yo'q")
            job_texts.append(f"{idx}. {title} — {location}, ish haqi {salary}")

        prompt = (
            "Siz ish qidirish bo'yicha yordamchisiz. Foydalanuvchining so'rovi: "
            f'"{message}".\n\n'
            "Quyidagi topilgan ishlarni foydalanuvchiga qisqacha va odob bilan tushuntirib bering:\n"
            + "\n".join(job_texts)
            + "\n\nFaqatgina javob bering va formatlashni sodda saqlang."
        )
        payload = {
            'model': get_openai_model(),
            'messages': [
                {'role': 'system', 'content': "Siz ish qidirish bo'yicha yordamchisiz."},
                {'role': 'user', 'content': prompt},
            ],
            'max_tokens': 200,
            'temperature': 0.5,
        }
        ai_text = call_openai_api(payload, timeout=15)
        if ai_text:
            return jsonify({"status": "success", "response": ai_text})

    if not jobs:
        return jsonify({"status": "success", "response": f'Kechirasiz, "{message}" bo\'yicha hozircha mos vakansiya topilmadi.'})

    top3 = jobs[:3]
    summary_lines = []
    for idx, job in enumerate(top3):
        title = str(job.get('Kasb') or job.get('kasb') or "Noma'lum ish")
        location = str(job.get('Joylashuv') or job.get('joylashuv') or "Noma'lum joy")
        salary = str(job.get('Ish haqi') or job.get('ish haqi') or "Ma'lumot yo'q")
        summary_lines.append(f"{idx + 1}. {title} — {location}, ish haqi {salary}")

    summary = "\n".join(summary_lines)
    response_text = (
        f'Sizning so\'rovingiz bo\'yicha {len(jobs)} ta mos vakansiya topdim:\n\n{summary}\n\n'
        'Agar xohlasangiz, ulardan birini batafsil ko\'rib chiqishingiz mumkin.'
    )
    return jsonify({"status": "success", "response": response_text})


@app.route("/recommend", methods=["POST"])
def recommend():
    data = request.json or {}

    query = str(data.get("query", "")).strip()
    location = str(data.get("location", "")).strip()
    job_type = str(data.get("job_type", "")).strip()
    employment_type = str(data.get("employment_type", "")).strip()
    source = str(data.get("source", "model")).strip().lower()
    top_n = max(1, int(data.get("top_n", 100)))
    max_pages = min(20, max(1, int(data.get("max_pages", 10))))
    min_salary = data.get("min_salary", None)

    # Try to use Gemini API to analyze the query first (AI-powered understanding)
    gemini_result = call_gemini_api(query)
    if gemini_result and gemini_result.get("search_phrase"):
        # Use Gemini's analyzed search phrase
        if not location and gemini_result.get("location"):
            location = gemini_result["location"]
        query = gemini_result.get("search_phrase", query)
        print(f"[Gemini] AI Analysis: {query}")
    else:
        # Fallback 1: Smart semantic extraction (no fixed synonyms)
        search_phrase, extracted_location, job_title = smart_extract_query(query)
        if search_phrase:
            query = search_phrase
            if not location and extracted_location:
                location = extracted_location
            print(f"[Smart] Extracted: job='{job_title}', loc='{location}', phrase='{query}'")
        else:
            # Fallback 2: Try advanced keyword extraction
            advanced_keywords = extract_job_keywords_advanced(query)
            if advanced_keywords:
                print(f"[Keywords] Extracted: {advanced_keywords}")
                query = advanced_keywords
                if not location:
                    location = extract_location_from_query(query)
            else:
                # Fallback 3: Normalize query
                normalized_query = normalize_user_query(query)
                if normalized_query:
                    query = normalized_query
                    print(f"[Normalized] Query: {query}")
                    if not location:
                        location = extract_location_from_query(query)

    if min_salary in ("", None):
        min_salary = None
    else:
        try:
            min_salary = int(float(min_salary))
        except ValueError:
            min_salary = None

    if source == "olx":
        # Build candidate OLX search phrases: try AI rewrite, prepared query, and heuristics
        terms = []
        if GROK_API_KEY and query:
            # ask Grok/OpenAI to create a short OLX search phrase
            prompt = (
                "Siz OLX.uz ish bo'limi uchun qidiruv so'zlarini tanlash bo'yicha yordamchisiz. "
                "Foydalanuvchining so'rovini qisqacha, aniq va OLX qidiruviga mos iboraga o'zgartiring. "
                "Faqatgina qidiruv iborasini qaytaring.\n\n"
                f"So'rov: {query}"
            )
            payload = {'model': get_openai_model(), 'messages': [{'role': 'system', 'content': 'Siz OLX ish qidiruviga mos so\'zlarni chiqaradigan yordamchisiz.'}, {'role': 'user', 'content': prompt}], 'max_tokens': 40, 'temperature': 0.2}
            ai_phrase = call_openai_api(payload, timeout=12)
            if ai_phrase:
                ai_phrase = ai_phrase.splitlines()[0].strip()
                ai_phrase = re.sub(r'["“”‘’]+', '', ai_phrase)
                ai_phrase = re.sub(r'[\.:,;]+$', '', ai_phrase).strip()
                if ai_phrase:
                    terms.append(ai_phrase)

        search_terms = get_olx_search_terms(query)
        for term in search_terms:
            if term not in terms:
                terms.append(term)

        # Try each term and collect OLX listings directly (no network-token filtering)
        collected = []
        seen = set()

        for t in terms:
            if len(collected) >= top_n:
                break
            results = scrape_olx(query=t, location=location, job_type=job_type, top_n=top_n, max_pages=max_pages)
            for item in results:
                link = item.get('Link')
                if not link or link in seen:
                    continue
                collected.append(item)
                seen.add(link)
                if len(collected) >= top_n:
                    break

        if collected:
            collected.sort(key=lambda item: score_olx_result(item, query), reverse=True)
            return jsonify({'status': 'success', 'count': len(collected), 'recommendations': collected[:top_n]})

        # fallback to model-based recommendations if OLX search didn't yield relevant results
        if not load_models():
            return jsonify({'status': 'success', 'count': 0, 'recommendations': []})

        query_text = ' '.join([p for p in [query, location, job_type, employment_type] if p]).lower()
        query_vec = tfidf.transform([query_text or ' '])
        n_neighbors = min(50, len(df))
        distances, indices = nn_model.kneighbors(query_vec, n_neighbors=n_neighbors)
        base_results = df.iloc[indices[0]].copy()
        base_results['moslik_foizi'] = (1 - distances[0]) * 100
        output_cols = [c for c in ['Kasb', 'Ish haqi', 'Joylashuv', 'Ish turi', 'Bandlik turi', 'Telefon', 'Link', 'moslik_foizi'] if c in base_results.columns]
        output = base_results.head(top_n)[output_cols].to_dict(orient='records')
        return jsonify({'status': 'success', 'count': len(output), 'recommendations': output})

    # So'rov matni
    query_text = " ".join(
        [p for p in [query, location, job_type, employment_type] if p]
    ).lower()

    if not load_models():
        return jsonify({'status': 'error', 'message': 'Model files are not available.'}), 503

    query_vec = tfidf.transform([query_text or " "])

    # Eng yaqin natijalar
    n_neighbors = min(50, len(df))
    distances, indices = nn_model.kneighbors(query_vec, n_neighbors=n_neighbors)

    base_results = df.iloc[indices[0]].copy()
    base_results["moslik_foizi"] = (1 - distances[0]) * 100

    results = base_results.copy()

    # Kasb (job title) bo'yicha filtr — oddiy contains, agar hech nima topilmasa, fuzzy fallback
    if "Kasb" in results.columns and query:
        q = query.lower()
        # Birinchi navbatda to'g'ridan-to'g'ri contains bilan filtr
        contains_mask = results["Kasb"].astype(str).str.lower().str.contains(q, na=False)
        if contains_mask.any():
            results = results[contains_mask]
        else:
            # Agar contains bo'yicha topilmasa, difflib yordamida yaqin so'zlarni qidiring
            from difflib import SequenceMatcher

            kasb_values = results["Kasb"].astype(str).unique()
            close = [k for k in kasb_values if SequenceMatcher(None, k.lower(), q).ratio() >= 0.6]
            if close:
                results = results[results["Kasb"].astype(str).isin(close)]

    # Filtrlash
    if location:
        # Get all variants of the location
        location_variants = get_location_variants(location)
        # Create a mask that checks if any variant appears in Joylashuv
        mask = results["Joylashuv"].astype(str).str.lower().apply(
            lambda x: any(variant in x for variant in location_variants)
        )
        results = results[mask]

    if job_type:
        results = results[
            results["Ish turi"]
            .astype(str)
            .str.lower()
            .str.contains(job_type.lower(), na=False)
        ]

    if employment_type:
        results = results[
            results["Bandlik turi"]
            .astype(str)
            .str.lower()
            .str.contains(employment_type.lower(), na=False)
        ]

    if min_salary is not None and "salary_num" in results.columns:
        results = results[results["salary_num"].fillna(0) >= min_salary]

    # Agar filtrdan keyin natija bo'lmasa, base natijaga qaytish
    if results.empty:
        results = base_results

    output_cols = [
        c
        for c in [
            "Kasb",
            "Ish haqi",
            "Joylashuv",
            "Ish turi",
            "Bandlik turi",
            "Telefon",
            "Link",
            "moslik_foizi",
        ]
        if c in results.columns
    ]

    output = results.head(top_n)[output_cols].to_dict(orient="records")

    return jsonify(
        {"status": "success", "count": len(output), "recommendations": output}
    )


if __name__ == "__main__":
    app.run(debug=True, port=5001, use_reloader=False)
