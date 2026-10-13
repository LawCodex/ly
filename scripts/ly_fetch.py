#!/usr/bin/env python3
"""Fetch Libyan legislation:

1. Ministry of Justice (aladel.gov.ly) "قوانين" categories through the site's public WordPress REST API
   (posts with the full text of each law);
2. the 2011 Constitutional Declaration (consolidated) and its constitutional amendments from the
   DCAF Libya security-sector legislation database (security-legislation.ly, Arabic edition, REST API),
   honouring its robots.txt Crawl-delay of 10 s;
3. Internet Archive captures of the National Transitional Council site (ntc.gov.ly, 2012): laws and
   constitutional amendments published as K2 items.

Usage: python ly_fetch.py RAW_DIR
"""
import json
import os
import re
import sys
import time
import urllib.parse

import requests

UA = "LawCodex/1.0 (+https://github.com/LawCodex)"
RAW = sys.argv[1]
os.makedirs(RAW, exist_ok=True)
S = requests.Session()
S.headers["User-Agent"] = UA

ALADEL = "https://aladel.gov.ly/home/wp-json/wp/v2/"
# category ids under "القوانين" (24) — legislation by field; drafts (84) excluded
ALADEL_CATS = [80, 82, 83, 81, 74, 75, 78, 112, 77, 76, 79, 85, 22, 23]
DCAF = "https://security-legislation.ly/ar/wp-json/wp/v2/"


def get(url, delay=1.0, **kw):
    for i in range(6):
        try:
            r = S.get(url, timeout=120, **kw)
            time.sleep(delay)
            if r.status_code == 200:
                return r
            if r.status_code in (400, 404):
                return None
        except requests.RequestException as e:
            print("retry", e, flush=True)
        time.sleep(10 * (i + 1))
    return None


def aladel():
    out = os.path.join(RAW, "aladel_posts.json")
    if os.path.exists(out):
        return
    posts = {}
    for cat in ALADEL_CATS:
        page = 1
        while True:
            r = get(ALADEL + "posts", params={"categories": cat, "per_page": 50, "page": page,
                                              "_fields": "id,date,modified,link,title,content,categories"})
            if r is None:
                break
            data = r.json()
            for p in data:
                posts[p["id"]] = p
            print("aladel cat", cat, "page", page, len(data), flush=True)
            if page >= int(r.headers.get("X-WP-TotalPages", "1")):
                break
            page += 1
    json.dump(list(posts.values()), open(out, "w", encoding="utf-8"), ensure_ascii=False)


def dcaf():
    out = os.path.join(RAW, "dcaf_constitutional.json")
    if os.path.exists(out):
        return
    found = {}
    for q in ("الإعلان الدستوري", "التعديل الدستوري"):
        r = get(DCAF + "latest-laws", delay=10, params={"search": q, "per_page": 50,
                                                         "_fields": "id,date,modified,link,title,content"})
        if r is None:
            continue
        for p in r.json():
            found[p["id"]] = p
    # consolidated Constitutional Declaration ("الإعلان الدستوري لسنة 2011 مع تعديلاته")
    r = get(DCAF + "latest-laws", delay=10, params={"slug": "الإعلان-الدستوري-لسنة-2011-مع-تعديلاته",
                                                     "_fields": "id,date,modified,link,title,content"})
    if r is not None:
        for p in r.json():
            p["consolidated_declaration"] = True
            found[p["id"]] = p
    json.dump(list(found.values()), open(out, "w", encoding="utf-8"), ensure_ascii=False)
    print("dcaf", len(found), flush=True)


def ntc():
    out = os.path.join(RAW, "ntc_items.json")
    if os.path.exists(out):
        return
    r = get("https://web.archive.org/cdx/search/cdx", params={
        "url": "ntc.gov.ly/", "matchType": "domain", "fl": "original,timestamp,mimetype",
        "filter": ["statuscode:200", "mimetype:text/html"], "collapse": "urlkey"})
    items = {}
    for line in (r.text.splitlines() if r is not None else []):
        orig, ts, _ = line.split(" ")
        if "com_k2" not in orig or "view=item" not in orig:
            continue
        m = re.search(r"[?&]id=(\d+)", urllib.parse.unquote(orig))
        if not m:
            continue
        items.setdefault(m.group(1), []).append((ts, orig))
    res = []
    for iid, caps in sorted(items.items(), key=lambda kv: int(kv[0])):
        for ts, orig in sorted(caps, reverse=True)[:3]:
            rr = get("https://web.archive.org/web/%sid_/%s" % (ts, orig), delay=2)
            if rr is None or len(rr.content) < 2000:
                continue
            res.append({"id": iid, "original": orig, "timestamp": ts,
                        "wayback": "https://web.archive.org/web/%s/%s" % (ts, orig),
                        "html": rr.content.decode("utf-8", "replace")})
            break
        print("ntc", iid, flush=True)
    json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False)


if __name__ == "__main__":
    steps = sys.argv[2:] or ["aladel", "dcaf", "ntc"]
    for st in steps:
        globals()[st]()
