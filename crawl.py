import feedparser
import requests

def crawl_and_push():
    # 1. 抓取加藤小夏日文新聞
    url = "https://news.google.com/rss/search?q=加藤小夏&hl=ja&gl=JP&ceid=JP:ja"
    feed = feedparser.parse(url)
    
    msg = "【加藤小夏 每日資訊彙整】\n\n"
    for entry in feed.entries[:3]: # 只取前三則最準確的
        msg += f"標題: {entry.title}\n連結: {entry.link}\n\n"
    
    # 2. 推送到 LINE Notify (這是最簡單的推播方式)
    # 你需要先去 LINE Notify 官網申請一個 Token
    line_token = "你的_LINE_TOKEN"
    api_url = "https://notify-api.line.me/api/notify"
    headers = {"Authorization": f"Bearer {line_token}"}
    requests.post(api_url, headers=headers, data={"message": msg})

if __name__ == "__main__":
    crawl_and_push()