import feedparser
import requests
from bs4 import BeautifulSoup
import re

def get_og_image(url):
    """訪問新聞網頁並抓取分享縮圖 (og:image)"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 尋找 <meta property="og:image" content="...">
        img_tag = soup.find('meta', property='og:image')
        if img_tag:
            return img_tag['content']
    except Exception as e:
        print(f"抓取圖片失敗: {url}, 錯誤: {e}")
    # 若抓不到，回傳一個透明背景或預設頭像，避免程式崩潰
    return "https://www.sunmusic-gp.co.jp/talent/kato_konatsu/images/top.jpg"

def crawl_and_push():
    url = "https://news.google.com/rss/search?q=加藤小夏&hl=ja&gl=JP&ceid=JP:ja"
    feed = feedparser.parse(url)
    
    # 這裡我們只處理第一則最新新聞，因為 Telegram 一次發送多張圖代碼會變複雜
    if not feed.entries:
        print("沒有找到新聞")
        return

    entry = feed.entries[0]
    title = entry.title
    link = entry.link
    
    # 執行關鍵動作：去抓新聞內部的圖片
    photo_url = get_og_image(link)
    
    msg = f"<b>【加藤小夏 最新資訊】</b>\n\n📌 <b>{title}</b>\n\n🔗 <a href='{link}'>點擊閱讀全文</a>"
    
    bot_token = "8784938561:AAHyB3vE__zfmbmO0-BuESNO9OiOsM99eZk"
    chat_id = "1738481715"
    
    send_url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    payload = {
        "chat_id": chat_id,
        "photo": photo_url,
        "caption": msg,
        "parse_mode": "HTML"
    }
    
    response = requests.post(send_url, json=payload)
    print(f"發送狀態: {response.status_code}")

if __name__ == "__main__":
    crawl_and_push()
