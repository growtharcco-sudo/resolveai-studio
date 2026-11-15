"""LinkedIn via Zapier (free): publish an RSS feed of the LinkedIn posts that are due.

linkedin/<id>.json = {"post_at": "...+05:30", "text": "...", "link": "https://...", "image": "linkedin/<id>.jpg"}
Every run puts the DUE posts (post_at <= now) into _linkedin/feed.xml on the media branch (served by GitHub Pages),
with their images in _linkedin/. Zapier ("RSS by Zapier" -> "LinkedIn: Create Company Update") checks the feed every
15 minutes and posts each new item to the ResolveAI page. Items are never removed, so nothing posts twice.
"""
import datetime as dt, email.utils, glob, json, os, shutil, sys
from xml.sax.saxutils import escape
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import media_branch as mb

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES = os.environ.get("PAGES_BASE", "https://growtharcco-sudo.github.io/resolveai-studio")


def build():
    now = dt.datetime.now(dt.timezone.utc); items = []
    for p in sorted(glob.glob(os.path.join(ROOT, "linkedin", "*.json"))):
        post = json.load(open(p)); when = dt.datetime.fromisoformat(post["post_at"])
        if when <= now: items.append((when, os.path.basename(p)[:-5], post))
    items.sort(key=lambda x: x[0], reverse=True)
    tmp = mb._checkout(); d = os.path.join(tmp, "_linkedin"); os.makedirs(d, exist_ok=True)
    xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/"><channel>',
           "<title>ResolveAI LinkedIn</title>", "<link>https://www.resolveai.cc</link>", "<description>ResolveAI posts for LinkedIn</description>"]
    for when, pid, post in items[:30]:
        img = ""
        if post.get("image") and os.path.exists(os.path.join(ROOT, post["image"])):
            name = pid + os.path.splitext(post["image"])[1]; shutil.copy(os.path.join(ROOT, post["image"]), os.path.join(d, name))
            url = f"{PAGES}/_linkedin/{name}"
            img = f'<enclosure url="{url}" type="image/jpeg" length="{os.path.getsize(os.path.join(d, name))}"/><media:content url="{url}" medium="image"/>'
        title = post["text"].strip().split("\n")[0][:120]
        xml.append(f"<item><title>{escape(title)}</title><link>{escape(post.get('link', 'https://www.resolveai.cc'))}</link>"
                   f"<guid isPermaLink=\"false\">resolveai-{pid}</guid><pubDate>{email.utils.format_datetime(when.astimezone(dt.timezone.utc))}</pubDate>"
                   f"<description>{escape(post['text'].strip())}</description>{img}</item>")
    xml.append("</channel></rss>")
    new = "\n".join(xml); fp = os.path.join(d, "feed.xml")
    old = open(fp).read() if os.path.exists(fp) else ""
    if new == old: print("feed unchanged,", len(items), "items"); return
    open(fp, "w").write(new); mb._publish(tmp); print("feed updated:", len(items), "items")


if __name__ == "__main__":
    build()
