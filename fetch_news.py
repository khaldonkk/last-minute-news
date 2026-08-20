import os
import json
import re
import time
import requests
import feedparser

# ==================== إعدادات المصادر ====================
RSS_FEEDS = [
    # --- تقنية ---
    {"url": "https://ayon-tech.com/feed/", "source": "عُيون التقنية", "category": "تقنية"},
    {"url": "https://www.takni.com/feed/", "source": "تقني", "category": "تقنية"},
    {"url": "https://arabeed.com/feed/", "source": "عُرب تيد", "category": "تقنية"},
    
    # --- أمن سيبراني ---
    {"url": "https://isc.sans.edu/feeds/latest", "source": "SANS ISC", "category": "أمن سيبراني", "lang": "en"},
    {"url": "https://www.darkreading.com/rss.xml", "source": "Dark Reading", "category": "أمن سيبراني", "lang": "en"},
    {"url": "https://www.bleepingcomputer.com/feed/", "source": "BleepingComputer", "category": "أمن سيبراني", "lang": "en"},
    {"url": "https://feeds.feedburner.com/TheHackersNews", "source": "The Hacker News", "category": "أمن سيبراني", "lang": "en"},
    
    # --- رياضة ---
    {"url": "https://www.kooora.com/rss.xml", "source": "كووورة", "category": "رياضة"},
    {"url": "https://www.skynewsarabia.com/rss/sport.xml", "source": "سكاي نيوز رياضة", "category": "رياضة"},
    
    # --- اقتصاد ---
    {"url": "https://www.skynewsarabia.com/rss/business.xml", "source": "سكاي نيوز اقتصاد", "category": "اقتصاد"},
    {"url": "https://arabic.rt.com/rss/business/", "source": "روسيا اليوم اقتصاد", "category": "اقتصاد"},
    
    # --- صحة وحياة ---
    {"url": "https://www.skynewsarabia.com/rss/varieties.xml", "source": "سكاي نيوز منوعات", "category": "صحة"},
    
    # --- أخبار عامة ---
    {"url": "https://feeds.bbci.co.uk/arabic/rss.xml", "source": "BBC عربي", "category": "عالم"},
    {"url": "https://arabic.rt.com/rss/", "source": "روسيا اليوم", "category": "عالم"}
]

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

def fetch_feed_data(url, source_name):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/rss+xml, application/xml, text/xml, */*'
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        return feedparser.parse(response.content)
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
    current_time = int(time.time())
    
    print(f"[*] Starting News Aggregator...")
    
    for feed_info in RSS_FEEDS:
        source = feed_info["source"]
        cat = feed_info["category"]
        lang = feed_info.get("lang", "ar")
        
        feed = fetch_feed_data(feed_info["url"], source)
        if not feed or not hasattr(feed, 'entries'):
            continue
            
        count = 0
        for entry in feed.entries:
            if count >= 5: # أخذ حتى 5 أخبار لكل مصدر
                break
                
            title = entry.get('title', '').strip()
            if not title or title in seen_titles:
                continue
                
            seen_titles.add(title)
            
            # تنظيف العنوان
            title = title.replace(f"- {source}", "").replace(f"| {source}", "").strip()
            raw_summary = entry.get('summary', entry.get('description', ''))
            
            final_category = "أمن سيبراني" if is_security_news(entry) and cat == "تقنية" else cat
            ai_summary = summarize_with_gemini(title, raw_summary, lang)
            
            all_news.append({
                "title": title,
                "summary": ai_summary,
                "link": entry.get('link', '#'),
                "published": entry.get('published', 'الآن'),
                "source": source,
                "category": final_category,
                "lang": lang,
                "timestamp": current_time
            })
            count += 1

    print(f"\n[✓] Collected {len(all_news)} unique articles.")
    
    with open("news.json", "w", encoding="utf-8") as f:
        json.dump(all_news, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
