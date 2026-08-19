import os
import json
import urllib.request
import feedparser

RSS_FEEDS = [
    {"url": "https://aljazeera.net/aljazeerarss.xml", "source": "الجزيرة"},
    {"url": "https://arabic.rt.com/rss/", "source": "روسيا اليوم"}
]

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

def summarize_with_gemini(title, summary):
    if not GEMINI_API_KEY:
        return summary

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    prompt = f"""
    قم بإعادة صياغة هذا الخبر وتلخيصه باللغة العربية بشكل جذاب ومختصر في نقطتين فقط.
    العنوان: {title}
    المحتوى: {summary}
    """
    
    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}]
    }).encode('utf-8')
    
    req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'})
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        print(f"Error calling Gemini: {e}")
        return summary

def main():
    all_news = []
    
    for feed_info in RSS_FEEDS:
        feed = feedparser.parse(feed_info["url"])
        for entry in feed.entries[:5]:
            title = entry.title
            raw_summary = entry.get('summary', entry.get('description', ''))
            ai_summary = summarize_with_gemini(title, raw_summary)
            
            all_news.append({
                "title": title,
                "summary": ai_summary,
                "link": entry.link,
                "published": entry.get('published', ''),
                "source": feed_info["source"],
                "category": feed_info["source"]
            })

    with open("news.json", "w", encoding="utf-8") as f:
        json.dump(all_news, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
