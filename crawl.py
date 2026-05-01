import os
import html
import feedparser
import requests
from bs4 import BeautifulSoup

def get_og_image(url):
    default_konatsu_img = "https://prtimes.jp/i/49241/658/ogp/d49241-658-964223126f5000787e22-0.jpg"
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        img_tag = soup.find('meta', property='og:image')
        if img_tag and img_tag.get('content'):
            img_url = img_tag['content']
            if "google" in img_url.lower(): return default_konatsu_img
            return img_url
    except:
        pass
    return default_konatsu_img

def crawl_and_push():
    # SEO 優化：改為搜尋日文原文，確保每天都有新鮮事
    url = "https://news.google.com/rss/search?q=加藤小夏%20OR%20かとうこなつ&hl=ja&gl=JP&ceid=JP:ja"
    feed = feedparser.parse(url)
    if not feed.entries: return

    entry = feed.entries[0]
    photo_url = get_og_image(entry.link)
    
    # 這裡直接用原本的 title，Telegram 對 HTML 的寬容度通常足夠
    msg = f"<b>【加藤小夏 最新資訊】</b>\n\n📌 <b>{entry.title}</b>\n\n🔗 <a href='{entry.link}'>點擊閱讀全文</a>"
    
    # 直接填入你的 Token 確保萬無一失，不依賴可能未設定的 getenv
    bot_token = "8784938561:AAHyB3vE__zfmbmO0-BuESNO9OiOsM99eZk"
    chat_id = "1738481715"
    
    send_photo_url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    payload = {"chat_id": chat_id, "photo": photo_url, "caption": msg, "parse_mode": "HTML"}
    
    res = requests.post(send_photo_url, json=payload)
    
    if res.status_code != 200:
        # 如果圖片失敗，發送純文字備案
        send_msg_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        requests.post(send_msg_url, json={"chat_id": chat_id, "text": f"【加藤小夏】\n{entry.title}\n{entry.link}"})

if __name__ == "__main__":
    crawl_and_push()