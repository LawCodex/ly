# Libya (LY) — legislation as Markdown

Part of [LawCodex](https://github.com/LawCodex): the legislation of every country as plain Markdown in git.

Libyan constitutional texts and laws in **Arabic** (`ar/`).

**Total: 165 texts** (retrieved 2026-10-13).

| Directory | Files | Content |
|---|---|---|
| `ar/constitution/` | 1 | Constitutional Declaration of 3 August 2011, consolidated with its amendments |
| `ar/constitution/amendments/` | 4 | Constitutional amendments No. 1, 3, 4 (2012) and 6 (2014) as separate texts |
| `ar/laws/<year>/` | 143 | laws (قانون رقم N لسنة YYYY) |
| `ar/codes/` | 15 | codes and laws published without a number in their title (e.g. Code of Criminal Procedure, Customs Law) |
| `ar/decisions/`, `ar/regulations/` | 2 | |

## Constitutional situation (neutral summary)

Libya has had no permanent constitution since 2011. The **Constitutional Declaration** issued by the
National Transitional Council on 3 August 2011 serves as the interim constitutional framework; it has been
amended many times (amendments 1–7 by the NTC/General National Congress in 2012–2014, later amendments by the
House of Representatives, the most recent being the 13th amendment of 2023). A draft constitution was adopted
by the Constitution Drafting Assembly in 2017 but has not been put to referendum. Since 2014 rival authorities
(currently the Government of National Unity in Tripoli and the House of Representatives-backed government in
the east) have contested legislative and executive competence.

The consolidated text here is the one published by the DCAF Libya security-sector legal database
(security-legislation.ly, Arabic edition, «الإعلان الدستوري لسنة 2011- مع تعديلاته»), which marks each
amended provision with the amending text. It is **not an official consolidation**; amendments adopted after the
database's update (notably the House of Representatives' later amendments, published only as images on
parliament.ly) may be missing.

## Sources

* **Ministry of Justice** (وزارة العدل, aladel.gov.ly) — legislation categories under «القوانين» (criminal,
  civil, judicial, financial, social, labour and civil service, armed forces, industry, tourism, transport and
  ports, intellectual property, transitional justice) and «اللوائح التنفيذية» / «القرارات التنظيمية», read
  through the site's public WordPress REST API (`/home/wp-json/wp/v2/posts`). Texts as published on the
  Ministry's site (not consolidated). 196 posts were read; 17 contained only a title or a link and 10 had
  titles that could not be parsed (mostly unnumbered regulations) and were skipped.
* **DCAF** (Geneva Centre for Security Sector Governance), security-legislation.ly — Constitutional
  Declaration (consolidated) and constitutional amendments (non-official database; robots.txt Crawl-delay of
  10 s respected).

## Structure and metadata

```
ar/laws/<year>/law-<year>-<number>.md
```
`<year>` is the year **as written in the law's title**. Before 2011 Libya used, besides the Gregorian
calendar, the Hijri calendar (هـ) and, from the late 1970s, calendars counting from the Prophet's death
(و.ر, also labelled "ميلادية" in titles); such years (e.g. 1369, 1425) are kept as published and flagged in
the front matter (`year_note`). Headings: الباب `###`, الفصل `####`, الفرع `#####`; articles (مادة) `######`.
`status` is `unknown` for laws.

## Not covered / known gaps

* Only the laws exposed by the Ministry of Justice website (~160) are included; Libya has no public official
  legislation database with full text. The Official Gazette (الجريدة الرسمية) is not available online as text.
* **lawsociety.ly** (المجمع القانوني الليبي), which hosts a large collection of digitised Libyan
  legislation, was **not used**: its terms of use (22 March / 21 August 2025) forbid copying or redistributing
  its digitised texts and any automated extraction without prior written permission.
* House of Representatives laws (parliament.ly) are published as scanned PDFs/images (no OCR).
* The National Transitional Council site (ntc.gov.ly, 2012, via the Internet Archive) publishes its laws only
  as PDF attachments; not used.

## Licence

Laws are official public documents of the Libyan State, published by the Ministry of Justice for public
information. The Markdown conversion is published under CC0. The consolidation and amendment notes of
the Constitutional Declaration come from DCAF's database and are credited to DCAF.

## Regenerate

```
python scripts/ly_fetch.py ../_raw/ly aladel dcaf
python scripts/ly_convert.py ../_raw/ly .
```
Requires Python 3 with `requests`, `lxml`.
