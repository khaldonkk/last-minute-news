import os
import json
import requests
import feedparser

# مصادر متنوعة ومصنفة لتغطية جميع المجالات
RSS_FEEDS = [
    # --- تقنية ---
    {"url": "https://www.unlimit-tech.com/feed/", "source": "التقنية بلا حدود", "category": "تقنية"},
    {"url": "https://aitnews.com/feed/", "source": "البوابة العربية للأخبار التقنية", "category": "تقنية"},
    
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

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

def fetch_feed_data(url):
    """جلب بيانات RSS مع استخدام Header يتفادى الحظر"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return feedparser.parse(response.content)
    except Exception as e:
        print(f"Error fetching {url}: {e}")
    return feedparser.parse(url)

def summarize_with_gemini(title, summary):
    if not GEMINI_API_KEY:
        return summary

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    prompt = f"""
    قم بإعادة صياغة هذا الخبر وتلخيصه باللغة العربية بشكل جذاب ومختصر في نقطتين فقط.
    العنوان: {title}
    المحتوى: {summary}
    """
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    
    try:
        res = requests.post(url, json=payload, timeout=10)
        if res.status_code == 200:
            result = res.json()
            return result['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        print(f"Error with Gemini API: {e}")
    
    return summary

def main():
    all_news = []
    
    for feed_info in RSS_FEEDS:
        print(f"Fetching [{feed_info['category']}] from {feed_info['source']}...")
        feed = fetch_feed_data(feed_info["url"])
        
        # أخذ أول 3 أخبار من كل تغذية لمجموع إجمالي يزيد عن 20-25 خبر متنوع
        count = 0
        for entry in feed.entries:
            if count >= 3:
                break
                
            title = entry.get('title', '').strip()
            if not title:
                continue
                
            raw_summary = entry.get('summary', entry.get('description', ''))
            ai_summary = summarize_with_gemini(title, raw_summary)
            
            all_news.append({
                "title": title,
                "summary": ai_summary,
                "link": entry.get('link', '#'),
                "published": entry.get('published', 'الآن'),
                "source": feed_info["source"],
                "category": feed_info["category"] # ربط التصنيف المباشر (تقنية، رياضة، إلخ)
            })
            count += 1

    print(f"Successfully collected {len(all_news)} articles.")

    with open("news.json", "w", encoding="utf-8") as f:
        json.dump(all_news, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
