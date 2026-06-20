import os
import json
import base64
import datetime
import feedparser
import requests
from bs4 import BeautifulSoup

# ── 設定 ──────────────────────────────────────────────
BOT_TOKEN  = os.environ.get("BOT_TOKEN", "")
CHAT_ID    = os.environ.get("CHAT_ID", "")
GH_TOKEN   = os.environ.get("GH_TOKEN", "")   # GitHub PAT，用來回寫 sent.txt
GH_REPO    = "monkamonme-collab/konatsu-crawler"
SENT_FILE  = "sent.txt"
DEFAULT_IMG = "https://prtimes.jp/i/49241/658/ogp/d49241-658-964223126f5000787e22-0.jpg"

KEYWORDS = ["加藤小夏", "かとうこなつ", "Konatsu Kato"]

# 多來源 RSS
RSS_SOURCES = [
    # Google News 日文
    "https://news.google.com/rss/search?q=加藤小夏+OR+かとうこなつ&hl=ja&gl=JP&ceid=JP:ja",
    # Google News 繁中
    "https://news.google.com/rss/search?q=加藤小夏&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",
    # Yahoo Japan News
    "https://news.yahoo.co.jp/rss/search?p=加藤小夏&ei=UTF-8",
    # Bing News RSS (English)
    "https://www.bing.com/news/search?q=Konatsu+Kato+%E5%8A%A0%E8%97%A4%E5%B0%8F%E5%A4%8F&format=rss",
]

# ── 工具函式 ───────────────────────────────────────────

def fetch_sent_urls():
    """從 GitHub API 讀取 sent.txt，回傳 (set_of_urls, sha)"""
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{SENT_FILE}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    r = requests.get(url, headers=headers, timeout=10)
    if r.status_code == 200:
        data = r.json()
        content = base64.b64decode(data["content"]).decode("utf-8")
        urls = set(line.strip() for line in content.splitlines() if line.strip())
        return urls, data["sha"]
    return set(), None

def push_sent_urls(urls, sha):
    """把新的 sent.txt 推回 GitHub"""
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{SENT_FILE}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    content = "\n".join(sorted(urls))
    payload = {
        "message": "chore: update sent.txt [skip ci]",
        "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
    }
    if sha:
        payload["sha"] = sha
    r = requests.put(url, headers=headers, json=payload, timeout=15)
    print(f"[sent] push sent.txt: {r.status_code}")

def get_og_image(article_url):
    """抓文章 og:image，失敗回傳預設圖"""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        r = requests.get(article_url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        tag = soup.find("meta", property="og:image")
        if tag and tag.get("content"):
            img = tag["content"]
            if "google" not in img.lower():
                return img
    except Exception as e:
        print(f"[og] {e}")
    return DEFAULT_IMG

def download_image(img_url):
    """下載圖片 bytes，失敗回傳 None"""
    try:
        r = requests.get(img_url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code == 200 and r.content:
            return r.content
    except Exception as e:
        print(f"[dl] {e}")
    return None

def send_photo_message(title, link, pub_date, img_bytes):
    """用 multipart 上傳圖片 + caption 傳送 Telegram 訊息"""
    date_str = pub_date.strftime("%Y/%m/%d") if pub_date else "—"
    caption = (
        f"📅 <b>{date_str}</b>\n"
        f"<b>【加藤小夏 最新資訊】</b>\n\n"
        f"📌 <b>{title}</b>\n\n"
        f"🔗 <a href=\'{link}\'>點擊閱讀全文</a>"
    )
    api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

    if img_bytes:
        files = {"photo": ("thumb.jpg", img_bytes, "image/jpeg")}
        data  = {"chat_id": CHAT_ID, "caption": caption, "parse_mode": "HTML"}
        r = requests.post(api_url, data=data, files=files, timeout=20)
    else:
        data = {"chat_id": CHAT_ID, "photo": DEFAULT_IMG, "caption": caption, "parse_mode": "HTML"}
        r = requests.post(api_url, json=data, timeout=20)

    print(f"[tg] sendPhoto: {r.status_code} {r.text[:120]}")

    if r.status_code != 200:
        # fallback: 純文字
        msg_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        r2 = requests.post(msg_url, json={
            "chat_id": CHAT_ID,
            "text": f"📅 {date_str}\n【加藤小夏】\n{title}\n{link}",
        }, timeout=15)
        print(f"[tg] fallback: {r2.status_code}")

def parse_pub_date(entry):
    """解析 RSS 發布時間，回傳 datetime 或 None"""
    try:
        import time
        t = entry.get("published_parsed") or entry.get("updated_parsed")
        if t:
            return datetime.datetime(*t[:6])
    except Exception:
        pass
    return None

# ── 主程式 ─────────────────────────────────────────────

def crawl_and_push():
    today = datetime.date.today()
    print(f"[crawl] date={today}, sources={len(RSS_SOURCES)}")

    # 1. 讀取已發送的 URL
    sent_urls, sent_sha = fetch_sent_urls()
    print(f"[crawl] sent history: {len(sent_urls)} urls")

    # 2. 收集所有來源的文章，去重
    seen_links = set()
    all_entries = []
    for src in RSS_SOURCES:
        try:
            feed = feedparser.parse(src)
            print(f"[crawl] {src[:60]}... => {len(feed.entries)} entries")
            for e in feed.entries:
                link = e.get("link", "")
                if link and link not in seen_links:
                    seen_links.add(link)
                    all_entries.append(e)
        except Exception as ex:
            print(f"[crawl] source error: {ex}")

    print(f"[crawl] total unique entries: {len(all_entries)}")

    # 3. 篩出「今天的新文章」（未發送過）
    new_entries = []
    for e in all_entries:
        link = e.get("link", "")
        if link in sent_urls:
            continue
        pub = parse_pub_date(e)
        if pub and pub.date() == today:
            new_entries.append((e, pub))

    # 4. 若今天沒有新文章，改用歷史文章中未發送的（最多 3 篇）
    is_fallback = False
    if not new_entries:
        print("[crawl] no new articles today, using unsent history")
        is_fallback = True
        for e in all_entries:
            link = e.get("link", "")
            if link not in sent_urls:
                pub = parse_pub_date(e)
                new_entries.append((e, pub))
                if len(new_entries) >= 3:
                    break

    if not new_entries:
        print("[crawl] nothing to send")
        return

    print(f"[crawl] will send {len(new_entries)} articles (fallback={is_fallback})")

    # 5. 逐篇發送
    newly_sent = set()
    for entry, pub in new_entries:
        link  = entry.get("link", "")
        title = entry.get("title", "（無標題）")
        print(f"[crawl] sending: {title[:60]}")
        img_url   = get_og_image(link)
        img_bytes = download_image(img_url)
        send_photo_message(title, link, pub, img_bytes)
        newly_sent.add(link)

    # 6. 更新 sent.txt
    updated = sent_urls | newly_sent
    push_sent_urls(updated, sent_sha)

if __name__ == "__main__":
    crawl_and_push()
