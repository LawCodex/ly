#!/usr/bin/env python3
"""Convert the Libyan sources fetched by ly_fetch.py into LawCodex Markdown.

Usage: python ly_convert.py RAW_DIR OUT_REPO_DIR
"""
import collections
import datetime
import html as htmlmod
import json
import os
import re
import sys
import unicodedata

from lxml import html as LH

RAW, OUT = sys.argv[1], sys.argv[2]
TODAY = datetime.date.today().isoformat()
LOG = open(os.path.join(RAW, "convert.log"), "w", encoding="utf-8")
DIG = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
HEAD = [(r"^(الكتاب|الجزء)\s", 2), (r"^الباب\s", 3), (r"^الفصل\s", 4), (r"^الفرع\s", 5)]
ART = re.compile(r"^((?:ال)?ماد[ةه]\s*\(?\s*[\d٠-٩]+\s*\)?(?:\s*مكرر(?:ا|ة)?(?:\s*\([^\)]{1,8}\))?)?|(?:ال)?ماد[ةه]\s+(?:الأولى|الثانية|الثالثة|الرابعة|الخامسة|السادسة|السابعة|الثامنة|التاسعة|العاشرة))\s*[\-–:\.]*\s*(.*)$")


def yq(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def clean(s):
    s = unicodedata.normalize("NFKC", s).replace("\xa0", " ").replace("ـ", "")
    s = s.replace("ی", "ي").replace("ک", "ك")  # Persian forms sometimes used for Arabic letters
    return re.sub(r"[ \t]+", " ", s).strip()


def html_lines(frag):
    el = LH.fromstring("<div>" + frag + "</div>")
    for bad in el.xpath("//script|//style"):
        bad.getparent().remove(bad)
    for br in el.iter("br"):
        br.tail = "\n" + (br.tail or "")
    for p in el.iter("p", "div", "tr", "li", "h1", "h2", "h3", "h4", "h5", "h6", "td"):
        p.tail = "\n" + (p.tail or "")
    return [clean(x) for x in el.text_content().split("\n")]


def merge_broken(lines):
    """DCAF pages sometimes split a word across two blocks ("الم" / "جلس"); join very short fragments."""
    out = []
    for l in lines:
        if out and len(out[-1]) <= 3 and re.fullmatch(r"[ء-ي]+", out[-1]) and l:
            out[-1] = out[-1] + l
        else:
            out.append(l)
    return out


def to_md(lines):
    out = []
    for s in lines:
        if not s:
            continue
        if len(s) < 100:
            lvl = next((l for rx, l in HEAD if re.match(rx, s)), None)
            if lvl:
                out += ["#" * lvl + " " + s, ""]
                continue
        m = ART.match(s)
        if m and len(m.group(1)) < 40:
            out += ["###### " + re.sub(r"\s+", " ", m.group(1)).strip(), ""]
            if m.group(2).strip():
                out += [m.group(2).strip(), ""]
            continue
        out += [s, ""]
    return "\n".join(out).strip() + "\n"


def parse_title(t):
    t = clean(htmlmod.unescape(re.sub(r"<[^>]+>", "", t)))
    tt = t.translate(DIG)
    m = re.search(r"(قانون|انون|قرار|التعديل الدستوري|تعديل دستوري|لائحة|مرسوم)[^\d]{0,30}?رق[ـ]*م\s*\(*\s*(\d+)\s*\)*\s*لسن[ـ]*ة\s*(\d{2,4})", tt)
    if not m:
        return t, None, None, None
    kind, num, year = m.group(1).replace("انون", "قانون") if m.group(1) == "انون" else m.group(1), m.group(2), m.group(3)
    if len(year) == 2:
        year = "19" + year
    return t, kind, num, year


def year_note(year):
    if int(year) < 1900:
        return ("Year as stated in the title: not Gregorian (Hijri هـ, or the Libyan calendars used before 2011 "
                "counting from the Prophet's death, و.ر / 'ميلادية'); folder uses that number")
    return None


def write(path, fm, title, body):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(["---"] + fm + ["---"]) + "\n\n# " + title + "\n\n" + body)


def main():
    counts = collections.Counter()
    # 1. Constitutional Declaration (consolidated) + amendments (DCAF)
    dcaf = json.load(open(os.path.join(RAW, "dcaf_constitutional.json"), encoding="utf-8"))
    for p in dcaf:
        title, kind, num, year = parse_title(p["title"]["rendered"])
        lines = merge_broken(html_lines(p["content"]["rendered"]))
        if p.get("consolidated_declaration"):
            fm = ["title: " + yq("الإعلان الدستوري الصادر عن المجلس الوطني الانتقالي المؤقت (2011) مع تعديلاته"),
                  'identifier: "Constitutional Declaration 2011 (consolidated)"', "type: constitution",
                  "jurisdiction: ly", "language: ar", "date: 2011-08-03", "status: in_force",
                  "consolidated: true", "consolidated_by: \"DCAF Libya security sector legal database (non-official)\"",
                  "source: " + yq(requests_unquote(p["link"])), "retrieved: " + TODAY]
            write(os.path.join(OUT, "ar", "constitution", "constitutional-declaration-2011.md"), fm,
                  "الإعلان الدستوري (2011) مع تعديلاته", to_md(lines))
            counts["constitution"] += 1
            continue
        if kind in ("التعديل الدستوري", "تعديل دستوري") and num:
            fm = ["title: " + yq(title), "identifier: " + yq("التعديل الدستوري رقم %s لسنة %s" % (num, year)),
                  "type: constitutional_amendment", "jurisdiction: ly", "language: ar", "year: %s" % year,
                  "status: unknown", "source: " + yq(requests_unquote(p["link"])), "retrieved: " + TODAY,
                  "note: \"Published by DCAF (non-official database).\""]
            write(os.path.join(OUT, "ar", "constitution", "amendments", "amendment-%s-%s.md" % (year, num)), fm,
                  title, to_md(lines))
            counts["constitutional_amendment"] += 1
    # 2. Ministry of Justice laws (aladel.gov.ly)
    posts = json.load(open(os.path.join(RAW, "aladel_posts.json"), encoding="utf-8"))
    seen = set()
    for p in posts:
        title, kind, num, year = parse_title(p["title"]["rendered"])
        lines = html_lines(p["content"]["rendered"])
        text_len = sum(len(x) for x in lines)
        if text_len < 300:
            print("SHORT", p["link"], title, file=LOG)
            counts["too_short"] += 1
            continue
        if not num:
            if title.startswith(("قانون", "القانون", "مدونة", "مجموعة", "مرسوم")):
                fm = ["title: " + yq(title), "identifier: " + yq(title), "type: code", "jurisdiction: ly",
                      "language: ar", "status: unknown", "source: " + yq(requests_unquote(p["link"])),
                      "retrieved: " + TODAY, "note: \"Text as published by the Ministry of Justice website.\""]
                write(os.path.join(OUT, "ar", "codes", "aladel-%d.md" % p["id"]), fm, title, to_md(lines))
                counts["code"] += 1
                continue
            print("NONUM", p["link"], title, file=LOG)
            counts["unparsed_title"] += 1
            continue
        typ, sub = {"قانون": ("law", "laws"), "قرار": ("decision", "decisions"), "لائحة": ("regulation", "regulations"),
                    "مرسوم": ("decree", "decrees")}.get(kind, ("law", "laws"))
        key = (sub, year, num)
        if key in seen:
            continue
        seen.add(key)
        fm = ["title: " + yq(title), "identifier: " + yq("%s رقم %s لسنة %s" % (kind, num, year)), "type: " + typ,
              "jurisdiction: ly", "language: ar", "year: %s" % year]
        yn = year_note(year)
        if yn:
            fm.append("year_note: " + yq(yn))
        fm += ["status: unknown", "source: " + yq(requests_unquote(p["link"])), "retrieved: " + TODAY,
               "note: \"Text as published by the Ministry of Justice website (not consolidated).\""]
        write(os.path.join(OUT, "ar", sub, year, "%s-%s-%s.md" % (sub[:-1], year, num)), fm, title, to_md(lines))
        counts[typ] += 1
    # 3. NTC 2011-2012 items (Internet Archive)
    pth = os.path.join(RAW, "ntc_items.json")
    if os.path.exists(pth):
        for it in json.load(open(pth, encoding="utf-8")):
            doc = LH.fromstring(it["html"])
            h = doc.xpath('//h2[contains(@class,"itemTitle")]')
            body = doc.xpath('//div[contains(@class,"itemFullText")]') or doc.xpath('//div[contains(@class,"itemIntroText")]')
            if not h or not body:
                continue
            title, kind, num, year = parse_title(h[0].text_content())
            if not num or kind not in ("قانون", "التعديل الدستوري", "تعديل دستوري"):
                continue
            lines = html_lines(LH.tostring(body[0], encoding="unicode"))
            if sum(len(x) for x in lines) < 200:
                continue
            if kind == "قانون":
                key = ("laws", year, num)
                if key in seen:
                    continue
                seen.add(key)
                path = os.path.join(OUT, "ar", "laws", year, "law-%s-%s.md" % (year, num))
                typ = "law"
            else:
                path = os.path.join(OUT, "ar", "constitution", "amendments", "amendment-%s-%s.md" % (year, num))
                if os.path.exists(path):
                    continue
                typ = "constitutional_amendment"
            fm = ["title: " + yq(title), "identifier: " + yq("%s رقم %s لسنة %s" % (kind, num, year)), "type: " + typ,
                  "jurisdiction: ly", "language: ar", "year: %s" % year, "status: unknown",
                  "source: " + yq(requests_unquote(it["original"])), "archived_source: " + yq(it["wayback"]),
                  "archived: %s-%s-%s" % (it["timestamp"][:4], it["timestamp"][4:6], it["timestamp"][6:8]),
                  "retrieved: " + TODAY, "note: \"National Transitional Council website (2012), via Internet Archive.\""]
            write(path, fm, title, to_md(lines))
            counts["ntc_" + typ] += 1
    for k, v in sorted(counts.items()):
        print(k, v)


def requests_unquote(u):
    import urllib.parse
    return urllib.parse.unquote(u)


if __name__ == "__main__":
    main()
