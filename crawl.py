import feedparser
import requests

def crawl_and_push():
    # 1. 爬取資訊
    url = "https://news.google.com/rss/search?q=加藤小夏&hl=ja&gl=JP&ceid=JP:ja"
    feed = feedparser.parse(url)
    
    msg = "【加藤小夏 每日資訊彙整】\n\n"
    for entry in feed.entries[:3]:
        msg += f"標題: {entry.title}\n連結: {entry.link}\n\n"
    
    # 2. 推送到 Telegram
    # 將下方替換為你的 Token 和 Chat ID
    bot_token = "8784938561:AAHyB3vE__zfmbmO0-BuESNO9OiOsM99eZk"
    chat_id = "1738481715"
    send_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    payload = {
        "chat_id": chat_id,
        "text": msg,
        "disable_web_page_preview": False
    }
    
    requests.post(send_url, json=payload)

if __name__ == "__main__":
    crawl_and_push()