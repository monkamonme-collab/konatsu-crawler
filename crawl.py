import feedparser
import requests
from bs4 import BeautifulSoup

def get_og_image(url):
    # PR TIMES 的加藤小夏宣傳圖 (穩定備案)
    default_konatsu_img = "https://prtimes.jp/i/49241/658/ogp/d49241-658-964223126f5000787e22-0.jpg"
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        # 增加 timeout 防止網頁回應太慢卡住
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        img_tag = soup.find('meta', property='og:image')
        if img_tag and img_tag.get('content'):
            img_url = img_tag['content']
            # 過濾掉 Google News 的 Logo 或小圖
            if "google" in img_url.lower() or "news" in img_url.lower():
                return default_konatsu_img
            return img_url
    except:
        pass
    return default_konatsu_img

def crawl_and_push():
    url = "https://news.google.com/rss/search?q=加藤小夏&hl=ja&gl=JP&ceid=JP:ja"
    feed = feedparser.parse(url)
    if not feed.entries: return

    entry = feed.entries[0]
    photo_url = get_og_image(entry.link)
    
    # --- 修正重點：確保 HTML 標籤成對出現 ---
    msg = f"<b>【加藤小夏 最新資訊】</b>\n\n📌 <b>{entry.title}</b>\n\n🔗 <a href='{entry.link}'>點擊閱讀全文</a>"
    
    bot_token = "8784938561:AAHyB3vE__zfmbmO0-BuESNO9OiOsM99eZk"
    chat_id = "1738481715"
    
    # 嘗試發送圖片
    send_photo_url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    photo_payload = {
        "chat_id": chat_id,
        "photo": photo_url,
        "caption": msg,
        "parse_mode": "HTML"
    }
    
    res = requests.post(send_photo_url, json=photo_payload)
    
    # 如果發送圖片失敗，改發純文字
    if res.status_code != 200:
        send_msg_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        text_payload = {
            "chat_id": chat_id,
            "text": msg + f"\n\n(圖片加載失敗，連結: {photo_url})",
            "parse_mode": "HTML",
            "disable_web_page_preview": False
        }
        requests.post(send_msg_url, json=text_payload)

if __name__ == "__main__":
    crawl_and_push()