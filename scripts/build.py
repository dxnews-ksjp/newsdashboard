"""GoogleニュースのRSSからトピックごとの見出しを集め、public/index.html を作るスクリプト。

使い方:  python scripts/build.py
Python 3.11 以上の標準ライブラリだけで動きます（追加インストール不要）。
"""

import html
import shutil
import sys
import tomllib
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = ROOT / "topics.toml"
TEMPLATE_DIR = ROOT / "templates"
OUTPUT_DIR = ROOT / "public"

JST = timezone(timedelta(hours=9))
RSS_URL = "https://news.google.com/rss/search?q={query}&hl=ja&gl=JP&ceid=JP:ja"
USER_AGENT = "Mozilla/5.0 (compatible; newsdashboard/1.0)"


def load_config():
    with open(CONFIG_FILE, "rb") as f:
        config = tomllib.load(f)
    if not config.get("topics"):
        sys.exit("topics.toml に [[topics]] が1つもありません。")
    return config


def fetch_rss(query):
    url = RSS_URL.format(query=urllib.parse.quote(query))
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def parse_items(xml_bytes):
    """RSSの<item>を {title, source, link, published} の辞書のリストにする。"""
    items = []
    for item in ET.fromstring(xml_bytes).iter("item"):
        title = (item.findtext("title") or "").strip()
        source = (item.findtext("source") or "").strip()
        # Googleニュースの見出しは「見出し - 配信元」の形なので、末尾の配信元を取り除く
        if source and title.endswith(f" - {source}"):
            title = title[: -len(f" - {source}")]
        try:
            published = parsedate_to_datetime(item.findtext("pubDate")).astimezone(JST)
        except (TypeError, ValueError):
            published = None
        items.append({
            "title": title,
            "source": source,
            "link": (item.findtext("link") or "").strip(),
            "published": published,
        })
    oldest = datetime.min.replace(tzinfo=JST)
    items.sort(key=lambda i: i["published"] or oldest, reverse=True)
    return items


def render_card(topic, items, error):
    name = html.escape(topic["name"])
    search_url = html.escape(
        "https://news.google.com/search?q="
        + urllib.parse.quote(topic["query"])
        + "&hl=ja&gl=JP&ceid=JP:ja"
    )
    if error:
        body = '<p class="message">ニュースを取得できませんでした。次回の更新をお待ちください。</p>'
    elif not items:
        body = '<p class="message">該当するニュースがありません。</p>'
    else:
        rows = []
        for item in items:
            date = item["published"].strftime("%m/%d %H:%M") if item["published"] else ""
            rows.append(
                "<li>"
                f'<a href="{html.escape(item["link"])}" target="_blank" rel="noopener">'
                f'<span class="headline">{html.escape(item["title"])}</span>'
                f'<span class="meta"><span class="source">{html.escape(item["source"])}</span>'
                f'<time>{date}</time></span>'
                "</a></li>"
            )
        body = '<ul class="news-list">' + "".join(rows) + "</ul>"
    return (
        '<section class="card">'
        f'<h2 class="card-title">{name}</h2>'
        f"{body}"
        f'<a class="more" href="{search_url}" target="_blank" rel="noopener">もっと見る ›</a>'
        "</section>"
    )


def render_page(title, subtitle, cards, updated_at):
    title = html.escape(title)
    subtitle_html = f'\n      <p class="subtitle">{html.escape(subtitle)}</p>' if subtitle else ""
    return f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<header class="site-header">
  <div class="inner">
    <div class="titles">
      <h1>{title}</h1>{subtitle_html}
    </div>
    <p class="updated">最終更新：{updated_at.strftime("%Y/%m/%d %H:%M")}</p>
  </div>
</header>
<main class="grid">
{chr(10).join(cards)}
</main>
<footer class="site-footer">出典：Googleニュース　／　毎朝7時ごろ自動更新</footer>
</body>
</html>
"""


def main():
    config = load_config()
    max_items = int(config.get("max_items", 10))
    cards = []
    failures = 0
    for topic in config["topics"]:
        items, error = [], False
        try:
            items = parse_items(fetch_rss(topic["query"]))[:max_items]
            print(f"[OK] {topic['name']}: {len(items)}件")
        except Exception as e:  # 1トピックの失敗でページ全体を止めない
            error = True
            failures += 1
            print(f"[NG] {topic['name']}: {e}", file=sys.stderr)
        cards.append(render_card(topic, items, error))

    if failures == len(config["topics"]):
        sys.exit("すべてのトピックで取得に失敗したため、ページを更新しませんでした。")

    OUTPUT_DIR.mkdir(exist_ok=True)
    page = render_page(
        config.get("title", "ニュースダッシュボード"),
        config.get("subtitle", ""),
        cards,
        datetime.now(JST),
    )
    (OUTPUT_DIR / "index.html").write_text(page, encoding="utf-8")
    shutil.copy(TEMPLATE_DIR / "style.css", OUTPUT_DIR / "style.css")
    print(f"{OUTPUT_DIR / 'index.html'} を作成しました。")


if __name__ == "__main__":
    main()
