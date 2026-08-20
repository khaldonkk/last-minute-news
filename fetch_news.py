import os
import json
import re
import requests
import feedparser

# ==================== إعدادات المصادر (مُحسّنة لمهندس أمن معلومات) ====================
RSS_FEEDS = [
    # --- تقنية (مصادر عربية موثوقة) ---
    {"url": "https://ayon-tech.com/feed/", "source": "عُيون التقنية", "category": "تقنية"},
    {"url": "https://www.takni.com/feed/", "source": "تقني", "category": "تقنية"},
    {"url": "https://arabeed.com/feed/", "source": "عُرب تيد", "category": "تقنية"},
    
    # --- أمن سيبراني (مصادر عالمية متخصصة - ثغرات، تهديدات، اختراقات) ---
    # SANS ISC: يراقب الثغرات والهجمات لحظياً (مرجع عالمي)
    {"url": "https://isc.sans.edu/feeds/latest", "source": "SANS ISC", "category": "أمن سيبراني", "lang": "en"},
    # Dark Reading: الأمن السيبراني المؤسسي
    {"url": "https://www.darkreading.com/rss.xml", "source": "Dark Reading", "category": "أمن سيبراني", "lang": "en"},
    # BleepingComputer: سريع جداً في نشر الـ CVEs والاختراقات
    {"url": "https://www.bleepingcomputer.com/feed/", "source": "BleepingComputer", "category": "أمن سيبراني", "lang": "en"},
    # The Hacker News
    {"url": "https://feeds.feedburner.com/TheHackersNews", "source": "The Hacker News", "category": "أمن سيبراني", "lang": "en"},
    # SecurityWeek: أخبار الأمن والتهديدات العالمية
    {"url": "https://www.securityweek.com/feed/", "source": "SecurityWeek", "category": "أمن سيبراني", "lang": "en"},
    # HelpNetSecurity: الأمن السيبراني والتحليلات
    {"url": "https://www.helpnetsecurity.com/feed/", "source": "HelpNetSecurity", "category": "أمن سيبراني", "lang": "en"},
    
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

# ==================== الدوال المساعدة ====================

def fetch_feed_data(url, source_name):
    """جلب البيانات مع headers متقدمة لتجنب الحظر"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/rss+xml, application/xml, text/xml, */*'
    }
    try:
        response = requests.get(url, headers=headers, timeout=20) # زدنا الوقت قليلاً للمصادر الخارجية
        response.raise_for_status()
        return feedparser.parse(response.content)
    except Exception as e:
        print(f"🚫 Error fetching {source_name}: {e}")
        return None

def summarize_with_gemini(title, summary, lang="ar"):
    """تلخيص الخبر مع الحفاظ على الدقة التقنية"""
    if not GEMINI_API_KEY:
        return summary

    # تحسين البرومبت: نطلب من الـ AI الحفاظ على المصطلحات التقنية بالإنجليزية
    prompt = f"""
    أنت خبير تقني وأمني. قم بتلخيص الخبر التالي باللغة العربية.
    **مهم:** احتفظ بالمصطلحات التقنية بالإنجليزية إذا كانت أكثر شيوعًا (مثل: CVE-XXXX, DDoS, Firewall, Zero-day, DNS, Phishing).
    العنوان: {title}
    المحتوى: {summary}
    """
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        res = requests.post(url, json=payload, timeout=20)
        if res.status_code == 200:
            return res.json()['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        print(f"🤖 Gemini Error for '{title[:30]}...': {e}")
    
    return summary

def is_security_news(item):
    """كشف ذكي للأخبار الأمنية حتى لو كانت في مصدر عام"""
    text = f"{item.get('title', '')} {item.get('summary', '')}".lower()
    # كلمات مفتاحية تقنية دقيقة
    tech_keywords = [
        r"CVE-|XSS|SQLi|DDoS|MITM|ransomware|phishing|firewall|encryption|zero-day|exploit|vulnerability|threat|incident|breach|cyber|اختراق|ثغرة|برمجية|هجوم"
    ]
    return any(re.search(kw, text) for kw in tech_keywords)

# ==================== التنفيذ الرئيسي ====================

def main():
    all_news = []
    print(f"[*] Starting Advanced Aggregator with {len(RSS_FEEDS)} sources...")
    
    for feed_info in RSS_FEEDS:
        source = feed_info["source"]
        cat = feed_info["category"]
        lang = feed_info.get("lang", "ar")
        
        print(f"📥 Fetching [{cat}] from {source}...")
        feed = fetch_feed_data(feed_info["url"], source)
        
        if not feed:
            continue
            
        count = 0
        for entry in feed.entries:
            if count >= 4: # نأخذ عدد مناسب للتنوع
                break
                
            title = entry.get('title', '').strip()
            if not title:
                continue
            
            # تنظيف العنوان (بعض المصادر تضيف نص إضافي)
            if f"- {source}" in title:
                title = title.replace(f"- {source}", "").strip()
            elif f"| {source}" in title:
                title = title.replace(f"| {source}", "").strip()
                
            raw_summary = entry.get('summary', entry.get('description', ''))
            
            # تحديد الفئة (أمن سيبراني تلقائي للأخبار التقنية)
            if is_security_news(entry) and cat == "تقنية":
                final_category = "أمن سيبراني"
            else:
                final_category = cat
            
            ai_summary = summarize_with_gemini(title, raw_summary, lang)
            
            all_news.append({
                "title": title,
                "summary": ai_summary,
                "link": entry.get('link', '#'),
                "published": entry.get('published', 'الآن'),
                "source": source,
                "category": final_category,
                "lang": lang
            })
            count += 1

    # ترتيب الأخبار (الأولوية للأخبار الأمنية)
    all_news.sort(key=lambda x: (x['category'] != 'أمن سيبراني', x.get('published', ''), reverse=True))

    print(f"\n[✓] Successfully collected {len(all_news)} articles.")
    
    with open("news.json", "w", encoding="utf-8") as f:
        json.dump(all_news, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
