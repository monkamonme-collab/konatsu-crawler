import os
import html
import feedparser
import requests
from bs4 import BeautifulSoup

def get_og_image(url):
    # PR TIMES 的加藤小夏宣傳圖 (穩定備案)
    default_konatsu_img = "https://prtimes.jp/i/49241/658/ogp/d49241-658-964223126f5000787e22-0.jpg"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        # 增加 timeout 防止網頁回應太慢卡住
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        img_tag = soup.find('meta', property='og:image')
        if img_tag and img_tag.get('content'):
            img_url = img_tag['content']
            # 過濾掉 Google News 的 Logo 或小圖
            if "google" in img_url.lower() or "news" in img_url.lower():
                return default_konatsu_img
            return img_url
    except Exception as e:
        print(f"get_og_image error: {e}")
    return default_konatsu_img

def crawl_and_push():
    url = "https://news.google.com/rss/search?q=加藤小夏&hl=ja&gl=JP&ceid=JP:ja"
    feed = feedparser.parse(url)
    if not feed.entries:
        print("No RSS entries found.")
        return

    entry = feed.entries[0]
    photo_url = get_og_image(entry.link)
    title = html.escape(entry.title)
    link = html.escape(entry.link)
    
    msg = (
        f"<b>【加藤小夏 最新資訊】</b>\n\n"
        f"📌 <b>{title}</b>\n\n"
        f"🔗 <a href='{link}'>點擊閱讀全文</a>"
    )
    
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "8784938561:AAHyB3vE__zfmbmO0-BuESNO9OiOsM99eZk")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "1738481715")
    
    # 嘗試發送圖片
    send_photo_url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    photo_payload = {
        "chat_id": chat_id,
        "photo": photo_url,
        "caption": msg,
        "parse_mode": "HTML"
    }
    
    res = requests.post(send_photo_url, json=photo_payload)
    if res.status_code != 200:
        print(f"sendPhoto failed: {res.status_code} {res.text}")
        send_msg_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        text_payload = {
            "chat_id": chat_id,
            "text": (
                f"【加藤小夏 最新資訊】\n\n📌 {entry.title}\n\n{entry.link}"
                f"\n\n(圖片加載失敗，連結: {photo_url})"
            )
        }
        res2 = requests.post(send_msg_url, json=text_payload)
        if res2.status_code != 200:
            print(f"sendMessage failed: {res2.status_code} {res2.text}")

if __name__ == "__main__":
    crawl_and_push()