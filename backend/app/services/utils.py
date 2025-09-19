import re, idna
import tldextract
from urllib.parse import urlparse

SUS_WORDS = [
    "login","verify","secure","account","update","confirm","wallet","airdrop",
    "bonus","free","gift","support","resolution","invoice","okta","microsoft",
    "apple","google","bank","security","unlock","password","reset"
]

def normalize_url(u: str) -> str:
    u = u.strip()
    if not u:
        return u
    if not re.match(r'^[a-zA-Z]+://', u):
        u = "http://" + u
    return u

def extract_host(url: str) -> str:
    try:
        p = urlparse(normalize_url(url))
        host = p.hostname or ""
        # IDN 统一 punycode
        if host:
            try:
                host = idna.encode(host).decode("ascii")
            except Exception:
                pass
        return host.lower()
    except Exception:
        return ""

def suffix_match(host: str, patterns: list[str]) -> bool:
    # 后缀匹配（子域也命中）。例如 pattern=example.com 命中 a.b.example.com
    host = host.lower()
    for p in patterns:
        p = p.lower().strip(".")
        if host == p or host.endswith("." + p):
            return True
    return False

def url_char_features(url: str) -> dict:
    u = normalize_url(url)
    host = extract_host(u)
    digits = sum(c.isdigit() for c in u)
    letters = sum(c.isalpha() for c in u)
    specials = sum(not c.isalnum() for c in u)
    susp = sum(1 for w in SUS_WORDS if w in u.lower())
    return {
        "len": len(u),
        "host_len": len(host),
        "digits": digits,
        "letters": letters,
        "specials": specials,
        "digit_ratio": digits/max(len(u),1),
        "special_ratio": specials/max(len(u),1),
        "susp_words": susp
    }
