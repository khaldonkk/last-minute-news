import os
import json
import urllib.request
import feedparser

# 1. قائمة مصادر الـ RSS (يمكنك إضافة أو تغيير أي رابط)
RSS_FEEDS = [
    "https://aljazeera.net/aljazeerarss.xml",
    "https://arabic.rt.com/rss/"
]

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

def summarize_with_gemini(title, summary):
    """إرسال الخبر إلى Gemini لتلخيصه وإعادة صياغته"""
    if not GEMINI_API_KEY:
        return summary # في حال عدم وجود المفتاح يرجع النص الأصلي

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
    
    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        # أخذ آخر 5 أخبار من كل مصدر
        for entry in feed.entries[:5]:
            title = entry.title
            raw_summary = entry.get('summary', entry.get('description', ''))
            
            # تلخيص الخبر عبر Gemini
            ai_summary = summarize_with_gemini(title, raw_summary)
            
            all_news.append({
                "title": title,
                "summary": ai_summary,
                "link": entry.link,
                "published": entry.get('published', '')
            })

    # حفظ الأخبار في ملف news.json
    with open("news.json", "w", encoding="utf-8") as f:
        json.dump(all_news, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()