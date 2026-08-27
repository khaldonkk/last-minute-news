import os
import json
import re
import time
from datetime import datetime
import requests
import feedparser
from urllib.parse import urlparse

# ==================== كلمات العاجل ====================
BREAKING_KEYWORDS = [
    r"breaking|urgent|flash|just in|explosion|attack|زلزال|هزة|انفجار|طوارئ|عاجل",
]

def get_domain(url):
    """استخراج نطاق الدومين من الرابط"""
    try:
        parsed = urlparse(url)
        return parsed.hostname.replace("www.", "")
    except Exception:
        return ""

def is_breaking_news(title, summary=""):
    """التحقق إذا كان الخبر عاجلًا بناءً على الكلمات المفتاحية"""
    text = f"{title} {summary}".lower()
    return any(re.search(kw, text, re.IGNORECASE) for kw in BREAKING_KEYWORDS)

# ==================== إعدادات المصادر ====================
RSS_FEEDS = [
    # --- تقنية ---
    {"url": "https://ayon-tech.com/feed/", "source": "عُيون التقنية", "category": "تقنية"},
    {"url": "https://www.takni.com/feed/", "source": "تقني", "category": "تقنية"},
    {"url": "https://arabeed.com/feed/", "source": "عُرب تيد", "category": "تقنية"},
    
    # --- تقنية — إنجليزية (زخم وتنوع) ---
    {"url": "https://www.theverge.com/rss/index.xml", "source": "The Verge", "category": "تقنية", "lang": "en"},
    {"url": "https://techcrunch.com/feed/", "source": "TechCrunch", "category": "تقنية", "lang": "en"},
    {"url": "https://feeds.arstechnica.com/arstechnica/index", "source": "Ars Technica", "category": "تقنية", "lang": "en"},
    {"url": "https://www.wired.com/feed/rss", "source": "Wired", "category": "تقنية", "lang": "en"},
    
    # --- أمن سيبراني ---
    {"url": "https://isc.sans.edu/feeds/latest", "source": "SANS ISC", "category": "أمن سيبراني", "lang": "en"},
    {"url": "https://www.darkreading.com/rss.xml", "source": "Dark Reading", "category": "أمن سيبراني", "lang": "en"},
    {"url": "https://www.bleepingcomputer.com/feed/", "source": "BleepingComputer", "category": "أمن سيبراني", "lang": "en"},
    {"url": "https://feeds.feedburner.com/TheHackersNews", "source": "The Hacker News", "category": "أمن سيبراني", "lang": "en"},
    {"url": "https://www.securityweek.com/feed/", "source": "SecurityWeek", "category": "أمن سيبراني", "lang": "en"},
    {"url": "https://www.helpnetsecurity.com/feed/", "source": "HelpNetSecurity", "category": "أمن سيبراني", "lang": "en"},
    {"url": "https://krebsonsecurity.com/feed/", "source": "Krebs on Security", "category": "أمن سيبراني", "lang": "en"},
    {"url": "https://www.schneier.com/feed/", "source": "Bruce Schneier", "category": "أمن سيبراني", "lang": "en"},
    {"url": "https://threatpost.com/feed/", "source": "Threatpost", "category": "أمن سيبراني", "lang": "en"},
    
    # --- رياضة ---
    {"url": "https://www.skynewsarabia.com/rss/sport.xml", "source": "سكاي الرياضة", "category": "رياضة"},
    
    # --- اقتصاد ---
    {"url": "https://www.skynewsarabia.com/rss/business.xml", "source": "سكاي اقتصاد", "category": "اقتصاد"},
    {"url": "https://arabic.rt.com/rss/business/", "source": "روسيا اليوم اقتصاد", "category": "اقتصاد"},
    
    # --- صحة وحياة ---
    {"url": "https://www.skynewsarabia.com/rss/varieties.xml", "source": "سكاي منوعات", "category": "صحة"},
    
    # --- أخبار عامة (تمت إضافة الجزيرة ✅) ---
    {"url": "https://feeds.bbci.co.uk/arabic/rss.xml", "source": "BBC عربي", "category": "عالم"},
   {"url": "https://www.aljazeera.net/rss/news", "source": "الجزيرة", "category": "عالم"},       # ✅ تمت الإضافة
    {"url": "https://www.skynewsarabia.com/rss/news", "source": "سكай نيوز", "category": "عالم"},          # ✅ تمت الإضافة
    {"url": "https://arabic.rt.com/rss/", "source": "روسيا اليوم", "category": "عالم"}
]

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

def fetch_feed_data(url, source_name):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'ar,en-US;q=0.7,en;q=0.3',
        'Cache-Control': 'no-cache'
    }
    try:
        session = requests.Session()
        response = session.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            return feedparser.parse(response.content)
        else:
            print(f"⚠️ {source_name} returned status {response.status_code}")
            return None
    except Exception as e:
        print(f"🚫 Error fetching {source_name}: {e}")
        return None

def summarize_with_gemini(title, summary, lang="ar"):
    if not GEMINI_API_KEY:
        return summary
    prompt = f"""
    أنت خبير تقني وأمني. قم بتلخيص الخبر التالي باللغة العربية بأسلوب مكثف في نقطتين.
    **مهم:** احتفظ بالمصطلحات التقنية بالإنجليزية (مثل: CVE-XXXX, DDoS, Firewall, Zero-day, DNS, Phishing).
    العنوان: {title}
    المحتوى: {summary}
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        res = requests.post(url, json=payload, timeout=10)
        if res.status_code == 200:
            return res.json()['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        print(f"🤖 Gemini Error: {e}")
    return summary

def is_security_news(item):
    text = f"{item.get('title', '')} {item.get('summary', '')}".lower()
    tech_keywords = [
        r"cve-|xss|sqli|ddos|mitm|ransomware|phishing|firewall|encryption|zero-day|exploit|vulnerability|threat|incident|breach|cyber|اختراق|ثغرة|برمجية|هجوم"
    ]
    return any(re.search(kw, text) for kw in tech_keywords)

def main():
    all_news = []
    seen_titles = set()
    current_timestamp = int(time.time())
    
    print(f"[*] Starting News Aggregator at {datetime.now()}...")
    
    for feed_info in RSS_FEEDS:
        source = feed_info["source"]
        cat = feed_info["category"]
        lang = feed_info.get("lang", "ar")
        
        try:
            print(f"📥 Fetching [{cat}] from {source}...")
            feed = fetch_feed_data(feed_info["url"], source)
            
            if not feed or not hasattr(feed, 'entries') or len(feed.entries) == 0:
                print(f"⚠️ No entries for {source}")
                continue
            
            count = 0
            for entry in feed.entries:
                if count >= 4:
                    break
                
                title = entry.get('title', '').strip()
                if not title or title in seen_titles:
                    continue
                seen_titles.add(title)
                
                title = title.replace(f"- {source}", "").replace(f"| {source}", "").strip()
                raw_summary = entry.get('summary', entry.get('description', ''))
                
                final_category = "أمن سيبراني" if is_security_news(entry) and cat == "تقنية" else cat
                ai_summary = summarize_with_gemini(title, raw_summary, lang)
                article_link = entry.get('link', '#')
                domain = get_domain(article_link)
                is_breaking = is_breaking_news(title, raw_summary)
                
                all_news.append({
                    "title": title,
                    "summary": ai_summary,
                    "link": article_link,
                    "published": entry.get('published', 'الآن'),
                    "source": source,
                    "category": final_category,
                    "lang": lang,
                    "domain": domain,
                    "breaking": is_breaking,
                    "fetched_at": current_timestamp
                })
                count += 1
        except Exception as e:
            print(f"❌ Failed processing {source}: {e}")
            continue

    print(f"\n[✓] Collected {len(all_news)} unique articles.")
    
    with open("news.json", "w", encoding="utf-8") as f:
        json.dump(all_news, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
