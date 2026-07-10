#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kommunbevakningen — automatisk nyhetsinsamling för Rättvis Demokrati.

Hämtar nyheter om Strömsunds kommun från öppna RSS-källor, filtrerar på
kommunrelevanta nyckelord, tar bort dubbletter och skriver in rubrik +
kort sammanfattning + källa + länk i nyheter/index.html (mellan markörerna).

Neutralt: ingen partihållning, ingen återpublicering av hela artiklar —
bara rubrik, kort utdrag, datum och länk till respektive källa.

Körs av GitHub Actions var 12:e timme. Endast Python-standardbibliotek.
"""
import html
import re
import sys
import os
import urllib.request
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.normpath(os.path.join(HERE, "..", "nyheter", "index.html"))

MAX_ITEMS = 16
TIMEOUT = 25
UA = "Mozilla/5.0 (compatible; RattvisDemokratiBot/1.0; +https://rattvisdemokrati.pro)"

# Källor. type: "google" = redan Strömsund-scopad sökning (behåll alla träffar);
#         "filter" = bred regional feed (kräver nyckelordsträff).
SOURCES = [
    {"name": "Google Nyheter", "type": "google",
     "url": "https://news.google.com/rss/search?q=%22Str%C3%B6msunds%20kommun%22&hl=sv&gl=SE&ceid=SE:sv"},
    {"name": "Google Nyheter", "type": "google",
     "url": "https://news.google.com/rss/search?q=%C3%84lvg%C3%A5rden%20Backe%20Str%C3%B6msund&hl=sv&gl=SE&ceid=SE:sv"},
    {"name": "SVT Nyheter Jämtland", "type": "filter",
     "url": "https://www.svt.se/nyheter/lokalt/jamtland/rss.xml"},
    {"name": "Östersunds-Posten", "type": "filter",
     "url": "https://www.op.se/feed"},
]

# Starka, kommun-specifika nyckelord (låg risk för falska träffar).
KEYWORDS = [
    "strömsund", "älvgården", "alvgården", "gäddede", "hoting", "rossön",
    "frostviken", "kyrktåsjö", "fjällsjö", "hammerdal", "alanäs",
    "vattudalsskolan", "backe", "strömsunds kommun",
]

MONTHS_SV = ["", "januari", "februari", "mars", "april", "maj", "juni",
             "juli", "augusti", "september", "oktober", "november", "december"]


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.read()


def strip_html(text):
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def sv_date(dt):
    if not dt:
        return ""
    return f"{dt.day} {MONTHS_SV[dt.month]} {dt.year}"


def parse_date(raw):
    if not raw:
        return None
    try:
        dt = parsedate_to_datetime(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def relevant(text):
    low = text.lower()
    # ordgräns för att undvika t.ex. "skidbacke" på nyckelordet "backe"
    for kw in KEYWORDS:
        if re.search(r"(?<![a-zåäö])" + re.escape(kw) + r"(?![a-zåäö])", low):
            return True
    return False


def norm_key(title):
    return re.sub(r"[^a-z0-9åäö]", "", title.lower())[:45]


def parse_feed(src):
    items = []
    try:
        data = fetch(src["url"])
        root = ET.fromstring(data)
    except Exception as e:
        sys.stderr.write(f"[warn] {src['name']}: {e}\n")
        return items

    for it in root.iter("item"):
        title = strip_html(it.findtext("title") or "")
        link = (it.findtext("link") or "").strip()
        desc = strip_html(it.findtext("description") or "")
        dt = parse_date(it.findtext("pubDate"))
        source_name = src["name"]

        if not title or not link:
            continue

        if src["type"] == "google":
            # Google News-titel: "Rubrik - Källa"; plocka källan, städa rubriken.
            src_el = it.find("source")
            if src_el is not None and (src_el.text or "").strip():
                source_name = src_el.text.strip()
                if title.endswith(" - " + source_name):
                    title = title[: -(len(source_name) + 3)].strip()
            else:
                m = re.search(r"\s-\s([^-]+)$", title)
                if m:
                    source_name = m.group(1).strip()
                    title = title[: m.start()].strip()
            # Google News-beskrivningar är oftast bara rubriken/källan i repris.
            desc = ""
        else:
            # Bred regional feed — kräver kommunrelevans.
            if not relevant(title + " " + desc):
                continue

        items.append({
            "title": title, "link": link, "desc": desc,
            "dt": dt, "source": source_name,
        })
    return items


def build_cards(items):
    if not items:
        return ('<p style="color:#3A4270;font-size:18px;">Inga aktuella '
                'nyheter hittades just nu. Titta in igen snart.</p>')
    out = []
    for it in items:
        title = html.escape(it["title"])
        link = html.escape(it["link"], quote=True)
        source = html.escape(it["source"])
        date = html.escape(sv_date(it["dt"]))
        desc = html.escape(it["desc"])
        if len(desc) > 190:
            desc = desc[:190].rsplit(" ", 1)[0] + "…"
        meta = source + (f" · {date}" if date else "")
        desc_html = f'<p class="news-text">{desc}</p>' if desc else ""
        out.append(
            '<article class="news">'
            f'<p class="news-meta">{meta}</p>'
            f'<h2 class="news-title"><a href="{link}" target="_blank" rel="noopener">{title}</a></h2>'
            f'{desc_html}'
            '</article>'
        )
    return "\n".join(out)


def replace_between(text, start, end, new_inner):
    s = text.find(start)
    e = text.find(end)
    if s == -1 or e == -1:
        raise SystemExit(f"Markör saknas: {start} / {end}")
    return text[: s + len(start)] + new_inner + text[e:]


def main():
    all_items = []
    for src in SOURCES:
        all_items.extend(parse_feed(src))

    # Dubblettfiltrering (behåll första förekomst — SVT/ÖP före Google).
    seen, deduped = set(), []
    # sortera så att icke-Google (direktlänkar) prioriteras vid dubblett
    all_items.sort(key=lambda x: 0 if "google" not in x["link"] else 1)
    for it in all_items:
        k = norm_key(it["title"])
        if not k or k in seen:
            continue
        seen.add(k)
        deduped.append(it)

    # Sortera på datum, nyast först (odaterade sist).
    deduped.sort(key=lambda x: x["dt"] or datetime.min.replace(tzinfo=timezone.utc),
                 reverse=True)
    items = deduped[:MAX_ITEMS]

    cards = build_cards(items)
    now = datetime.now(timezone.utc)
    updated = f"{now.day} {MONTHS_SV[now.month]} {now.year}, kl {now.strftime('%H:%M')} (UTC)"

    with open(PAGE, encoding="utf-8") as f:
        page = f.read()
    page = replace_between(page, "<!--FEED_START-->", "<!--FEED_END-->", "\n" + cards + "\n")
    page = replace_between(page, "<!--UPDATED_START-->", "<!--UPDATED_END-->", updated)
    with open(PAGE, "w", encoding="utf-8") as f:
        f.write(page)

    print(f"Klart: {len(items)} nyheter skrivna till {PAGE}")
    for it in items:
        print(f"  - [{it['source']}] {it['title'][:70]}")


if __name__ == "__main__":
    main()
