import os
import json
import re
import requests
import feedparser

# ==================== إعدادات المصادر ====================
RSS_FEEDS = [
    # --- تقنية وخدمات سحابية ---
    {"url": "https://www.unlimit-tech.com/feed/", "source": "التقنية بلا حدود", "category": "تقنية"},
    {"url": "https://aitnews.com/feed/", "source": "البوابة العربية للأخبار التقنية", "category": "تقنية"},
    {"url": "https://ayon-tech.com/feed/", "source": "عُيون التقنية", "category": "تقنية"},
    {"url": "https://takni.com/feed/", "source": "تقني", "category": "تقنية"},
    {"url": "https://arabeed.com/feed/", "source": "عُرب تيد", "category": "تقنية"},
    {"url": "https://techblog.sa/feed/", "source": "مدونة التقنية", "category": "تقنية"},
    
    # --- أمن سيبراني (أخبار عربية + مراجع عالمية) ---
    {"url": "https://www.bleepingcomputer.com/feed/", "source": "BleepingComputer", "category": "أمن سيبراني", "lang": "en"},
    {"url": "https://feeds.feedburner.com/TheHackersNews", "source": "The Hacker News", "category": "أمن سيبراني", "lang": "en"},
    {"url": "https://www.microsoft.com/security/rss.xml", "source": "Microsoft Security", "category": "أمن سيبراني", "lang": "en"},
    
    # --- شبكات وبنية تحتية ---
    {"url": "https://www.arabia.com.sa/rss", "source": "أرابيا (شبكات)", "category": "شبكات"},
    {"url": "https://techblog.sa/feed/", "source": "مدونة التقنية (شبكات)", "category": "شبكات"},

    # --- رياضة ---
    {"url": "https://www.kooora.com/rss.xml", "source": "كووورة", "category": "رياضة"},
    {"url": "https://www.skynewsarabia.com/rss/sport.xml", "source": "سكاي نيوز رياضة", "category": "رياضة"},
    
    # --- اقتصاد ---
    {"url": "https://www.skynewsarabia.com/rss/business.xml", "source": "سكاي نيوز اقتصاد", "category": "اقتصاد"},
    {"url": "https://arabic.rt.com/rss/business/", "source": "روسيا اليوم اقتصاد", "category": "اقتصاد"},
    
    # --- صحة وحياة ---
    {"url": "https://www.skynewsarabia.com/rss/varieties.xml", "source": "سكاي نيوز منوعات", "category": "صحة"},
    
    # --- أخبار عامة وسياسة ---
    {"url": "https://feeds.bbci.co.uk/arabic/rss.xml", "source": "BBC عربي", "category": "عالم"},
    {"url": "https://arabic.rt.com/rss/", "source": "روسيا اليوم", "category": "عالم"}
]

# مفتاح Gemini API
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# ==================== دوال مساعدة ====================

def fetch_feed_data(url, source_name):
    """جلب بيانات RSS مع Header متوافق مع GitHub Actions والسيرفرات"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/rss+xml, application/xml, text/xml, */*'
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        return feedparser.parse(response.content)
    except Exception as e:
        print(f"[!] Error fetching {source_name}: {e}")
        return None

def summarize_with_gemini(title, summary):
    """تلخيص الخبر عبر Gemini API"""
    if not GEMINI_API_KEY:
        return summary
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    prompt = f"""
    قم بإعادة صياغة هذا الخبر وتلخيصه باللغة العربية بشكل جذاب ومختصر (جمله إلى جملتين).
    العنوان: {title}
    المحتوى: {summary}
    """
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        res = requests.post(url, json=payload, timeout=15)
        if res.status_code == 200:
            return res.json()['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        print(f"[!] Gemini Error for '{title[:20]}...': {e}")
    
    return summary

def is_security_news(item):
    """فلتر ذكي يميز الأخبار الأمنية من المصادر العامة"""
    text = f"{item.get('title', '')} {item.get('summary', '')}".lower()
    keywords = [
        r"ثغرة|اختراق|برمجية|DDoS|CVE-|هجوم|تشفير|اختراق|بيانات|معلومات|سайбер|امن سيبراني|فاير وول"
    ]
    return any(re.search(kw, text) for kw in keywords)

# ==================== التنفيذ الرئيسي ====================

def main():
    all_news = []
    print(f"[*] Starting News Aggregator with {len(RSS_FEEDS)} sources...\n")
    
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
            if count >= 4:  # زيادة العدد قليلاً للتنوع
                break
                
            title = entry.get('title', '').strip()
            if not title:
                continue
                
            raw_summary = entry.get('summary', entry.get('description', ''))
            
            # تحديد الفئة النهائية للخبر (أمن سيبراني تلقائي أو الفئة المحددة)
            if is_security_news(entry) and cat == "تقنية":
                final_category = "أمن سيبراني"
            else:
                final_category = cat
                
            # تلخيص الخبر عبر Gemini
            ai_summary = summarize_with_gemini(title, raw_summary)
            
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

    print(f"\n[✓] Successfully collected {len(all_news)} articles.")
    
    with open("news.json", "w", encoding="utf-8") as f:
        json.dump(all_news, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
