import feedparser
import requests
from bs4 import BeautifulSoup

def get_og_image(url):
    """
    抓取新聞頁面的 Open Graph 圖片。
    如果抓到的是 Google News 標誌或無效圖，則回傳加藤小夏的官方頭像。
    """
    # 設定加藤小夏的穩定官方圖網址作為備案
    default_konatsu_img = "https://www.sunmusic-gp.co.jp/talent/kato_konatsu/images/top.jpg"
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        img_tag = soup.find('meta', property='og:image')
        if img_tag and img_tag.get('content'):
            img_url = img_tag['content']
            # 過濾掉 Google News 的 Logo 圖片
            if "google" in img_url.lower() or "news" in img_url.lower():
                return default_konatsu_img
            return img_url
    except:
        pass
    return default_konatsu_img

def crawl_and_push():
    # 爬取加藤小夏的新聞
    url = "https://news.google.com/rss/search?q=加藤小夏&hl=ja&gl=JP&ceid=JP:ja"
    feed = feedparser.parse(url)
    
    if not feed.entries:
        return

    entry = feed.entries[0]
    # 呼叫改進後的圖片抓取函數
    photo_url = get_og_image(entry.link)
    
    msg = f"<b>【加藤小夏 最新資訊】</b>\n\n📌 <b>{entry.title}</b>\n\n🔗 <a href='{entry.link}'>點擊閱讀全文</a>"
    
    # 你的 Telegram 設定
    bot_token = "8784938561:AAHyB3vE__zfmbmO0-BuESNO9OiOsM99eZk"
    chat_id = "1738481715"
    
    send_url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    payload = {
        "chat_id": chat_id,
        "photo": photo_url,
        "caption": msg,
        "parse_mode": "HTML"
    }
    
    requests.post(send_url, json=payload)

if __name__ == "__main__":
    crawl_and_push()