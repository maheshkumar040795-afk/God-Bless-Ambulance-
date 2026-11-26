#!/usr/bin/env python3
"""Build static SEO pages for every service area and hospital.

Reads the data already in index.html (GB_AREA_HOSPITALS, GB_TN_CITIES,
GB_PADMA_PHOTOS) and writes:
  /chennai/                      hub of all Chennai areas
  /chennai/<area>/               one page per Chennai area
  /chennai/<area>/<hospital>/    one page per hospital (once, under its home area)
  /tamil-nadu/ ...               same for Tamil Nadu cities
  /sitemap.xml                   every page above + the home page
It also makes the area chips on the home page real links so Google can follow them.

Run from the repo root:  python3 tools/build_pages.py
Re-run it whenever you add or change areas or hospitals in index.html.
"""
import datetime
import hashlib
import html
import json
import os
import re
import shutil
from urllib.parse import quote

SITE = "https://godblessambulance.in"
PHONE = "8939473038"
PHONE_DISPLAY = "+91 89394 73038"
WA = "918939473038"
OFFICE = "5/489 First Floor, Venkatesapuram, Kottivakkam, Chennai, Tamil Nadu 600041"
TODAY = datetime.date.today().isoformat()
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SERVICES = [
    ("ICU Ambulance", "Ventilator, monitor and trained staff for critical patients."),
    ("ALS Ambulance", "Advanced life support with cardiac monitor and oxygen."),
    ("BLS Ambulance", "Basic life support for stable patients and discharges."),
    ("Freezer Box Ambulance", "Mortuary van with freezer box for dignified transfer."),
    ("Hospital Transfer", "Hospital-to-hospital and home-to-hospital shifting."),
    ("Outstation Ambulance", "Long-distance trips across Tamil Nadu and other states."),
]


# ---------------------------------------------------------------- data
def js_obj(src, name):
    i = src.index("var %s=" % name) + len(name) + 5
    obj, _ = json.JSONDecoder().raw_decode(src[i:])
    return obj


def slug(t):
    t = t.lower().replace("&", " and ").replace("'", "").replace("’", "")
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-") or "page"


def esc(t):
    return html.escape(str(t), quote=True)


def pick(seed, options):
    h = int(hashlib.md5(seed.encode()).hexdigest(), 16)
    return options[h % len(options)]


def pincode(addr):
    m = re.search(r"\b6\d{5}\b", addr)
    return m.group(0) if m else ""


def road(addr):
    for part in addr.split(","):
        p = part.strip()
        if re.search(r"\b(Rd|Road|Salai|High ?Road|Street|St|Main Rd|Nagar|Trunk|Bypass)\b", p, re.I) and len(p) < 45:
            return re.sub(r"^\d+[A-Za-z/-]*\s*", "", p)
    return ""


def norm(t):
    return re.sub(r"[^a-z]", "", t.lower())


# ---------------------------------------------------------------- html
CSS = """*{box-sizing:border-box}body{margin:0;font-family:system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;color:#2d3748;background:#f7fafc;line-height:1.6;font-size:16px}
a{color:#c0392b}img{max-width:100%;display:block}
.top{background:#fff;border-bottom:1px solid #e2e8f0;position:sticky;top:0;z-index:5}
.top .in{max-width:1080px;margin:0 auto;padding:10px 16px;display:flex;align-items:center;justify-content:space-between;gap:12px}
.brand{display:flex;align-items:center;gap:8px;text-decoration:none;color:#1a2340;font-weight:800;letter-spacing:.5px;font-size:15px}
.brand small{display:block;color:#c0392b;font-size:10px;letter-spacing:2px;font-weight:700}
.btn{display:inline-flex;align-items:center;justify-content:center;gap:6px;padding:11px 18px;border-radius:999px;font-weight:700;text-decoration:none;font-size:15px;border:0;cursor:pointer}
.btn.red{background:#c0392b;color:#fff}.btn.green{background:#25d366;color:#fff}.btn.ghost{background:#fff;color:#1a2340;border:1.5px solid #cbd5e0}
main{max-width:1080px;margin:0 auto;padding:16px}
.crumb{font-size:13px;color:#718096;margin:4px 0 10px}.crumb a{color:#718096}
.hero{background:linear-gradient(135deg,#c0392b,#8e1f14);color:#fff;border-radius:16px;padding:22px 20px;margin-bottom:18px}
.hero h1{margin:0 0 8px;font-size:26px;line-height:1.25}.hero p{margin:0 0 14px;opacity:.95}
.hero .acts{display:flex;flex-wrap:wrap;gap:10px}
.card{background:#fff;border:1px solid #e2e8f0;border-radius:14px;padding:18px;margin-bottom:16px}
.card h2{font-size:20px;margin:0 0 10px;color:#1a2340}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:10px}
.svc{border:1px solid #edf2f7;border-radius:10px;padding:10px 12px}.svc b{display:block;color:#1a2340}.svc span{font-size:14px;color:#4a5568}
.list{list-style:none;padding:0;margin:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:8px}
.list li{border:1px solid #edf2f7;border-radius:10px;padding:10px 12px;background:#fff}
.list a{font-weight:700;text-decoration:none;color:#1a2340}.list small{display:block;color:#718096;font-size:13px}
.chips{display:flex;flex-wrap:wrap;gap:8px}.chips a{padding:7px 13px;border:1.5px solid #e2e8f0;border-radius:999px;text-decoration:none;color:#2d3748;font-size:14px;background:#fff}
.photo{aspect-ratio:2/1;background:linear-gradient(135deg,#fff5f5,#fed7d7);border-radius:12px;overflow:hidden;margin-bottom:12px}
.photo img{width:100%;height:100%;object-fit:cover}
.map{aspect-ratio:16/9;background:#edf2f7;border-radius:12px;display:flex;align-items:center;justify-content:center;overflow:hidden}
.map iframe{width:100%;height:100%;border:0}
dl{margin:0}dt{font-weight:700;color:#1a2340;margin-top:12px}dd{margin:4px 0 0}
.facts{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:10px;margin:0;padding:0;list-style:none}
.facts li{background:#f7fafc;border-radius:10px;padding:10px 12px;font-size:14px}.facts b{display:block;color:#1a2340}
footer{background:#1a2340;color:#cbd5e0;margin-top:24px;padding:24px 16px 90px;font-size:14px}
footer .in{max-width:1080px;margin:0 auto}footer a{color:#fff}
.bar{position:fixed;left:0;right:0;bottom:0;display:flex;gap:8px;padding:10px;background:#fff;border-top:1px solid #e2e8f0;z-index:6}
.bar .btn{flex:1}
@media(min-width:800px){.hero h1{font-size:32px}.bar{display:none}footer{padding-bottom:24px}}
"""

LOGO = ('<svg viewBox="0 0 100 100" width="36" height="36" aria-hidden="true"><path d="M50,82 C50,82 13,57 13,33 C13,21 23,13 33,13 '
        'C40,13 46,17 50,23 C54,17 60,13 67,13 C77,13 87,21 87,33 C87,57 50,82 50,82 Z" fill="none" stroke="#C0392B" stroke-width="6" '
        'stroke-linecap="round" stroke-linejoin="round"/><polyline points="16,43 29,43 35,27 43,58 50,35 57,47 63,43 84,43" fill="none" '
        'stroke="#1a2340" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/></svg>')

MAP_JS = ("<script>document.querySelectorAll('[data-map]').forEach(function(b){b.addEventListener('click',function(){"
          "var f=document.createElement('iframe');f.src=b.getAttribute('data-map');f.loading='lazy';f.title='Map';"
          "f.referrerPolicy='no-referrer-when-downgrade';b.parentNode.replaceChild(f,b);});});</script>")


def page(path, title, desc, body, ld, crumbs, wa_text):
    url = SITE + path
    lds = "".join('<script type="application/ld+json">%s</script>' % json.dumps(x, ensure_ascii=False, separators=(",", ":"))
                  for x in ld)
    crumb_html = " &rsaquo; ".join(
        ('<a href="%s">%s</a>' % (esc(u), esc(n)) if u else esc(n)) for n, u in crumbs)
    wa = "https://wa.me/%s?text=%s" % (WA, quote(wa_text))
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{esc(url)}">
<meta property="og:type" content="website"><meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{esc(url)}">
<meta name="theme-color" content="#c0392b">
<link rel="icon" href="/favicon.ico"><link rel="apple-touch-icon" href="/apple-touch-icon.png">
<style>{CSS}</style>{lds}
</head><body>
<header class="top"><div class="in"><a class="brand" href="/">{LOGO}<span>GOD BLESS AMBULANCE<small>24/7 SERVICE</small></span></a>
<a class="btn red" href="tel:{PHONE}">&#128222; {PHONE_DISPLAY}</a></div></header>
<main><nav class="crumb" aria-label="Breadcrumb">{crumb_html}</nav>
{body}
</main>
<footer><div class="in"><b>God Bless Ambulance Service</b><br>{esc(OFFICE)}<br>
Phone: <a href="tel:{PHONE}">{PHONE_DISPLAY}</a> &middot; Open 24 hours, 7 days<br><br>
<a href="/">Home</a> &middot; <a href="/#booking">Book an ambulance</a> &middot; <a href="/chennai/">Chennai areas</a> &middot; <a href="/tamil-nadu/">Tamil Nadu cities</a><br><br><span style="opacity:.75">Designed &amp; developed by <a href="https://thinkthroughtechnology.in" target="_blank" rel="noopener">Think Through Technology</a> &middot; <a href="https://thinkthroughtechnology.in" target="_blank" rel="noopener">thinkthroughtechnology.in</a></span></div></footer>
<div class="bar"><a class="btn red" href="tel:{PHONE}">&#128222; Call</a><a class="btn green" href="{esc(wa)}">WhatsApp</a></div>
{MAP_JS}
</body></html>
"""


def write(path, content):
    full = os.path.join(ROOT, path.strip("/"), "index.html")
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)


def business_ld(area_name, region):
    return {"@context": "https://schema.org", "@type": "EmergencyService", "name": "God Bless Ambulance Service",
            "url": SITE + "/", "telephone": "+91-" + PHONE, "openingHours": "Mo-Su 00:00-23:59",
            "address": {"@type": "PostalAddress", "streetAddress": "5/489 First Floor, Venkatesapuram, Kottivakkam",
                        "addressLocality": "Chennai", "addressRegion": "Tamil Nadu", "postalCode": "600041",
                        "addressCountry": "IN"},
            "areaServed": {"@type": "Place", "name": "%s, %s" % (area_name, region)}}


def crumb_ld(crumbs):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": SITE + (u or "")} for i, (n, u) in enumerate(crumbs)]}


def faq_ld(faqs):
    return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faqs]}


def faq_html(faqs):
    return '<section class="card"><h2>Frequently asked questions</h2><dl>%s</dl></section>' % "".join(
        "<dt>%s</dt><dd>%s</dd>" % (esc(q), esc(a)) for q, a in faqs)


def services_html(place):
    return '<section class="card"><h2>Ambulance services in %s</h2><div class="grid">%s</div></section>' % (
        esc(place), "".join('<div class="svc"><b>%s</b><span>%s</span></div>' % (esc(a), esc(b)) for a, b in SERVICES))


def map_block(query, label):
    src = "https://maps.google.com/maps?q=%s&z=15&output=embed" % quote(query)
    link = "https://www.google.com/maps/search/?api=1&query=%s" % quote(query)
    return ('<section class="card"><h2>%s</h2><div class="map"><button type="button" class="btn ghost" data-map="%s">'
            '&#128205; Show map</button></div><p><a href="%s" target="_blank" rel="noopener">Get directions in Google Maps &rarr;</a></p></section>'
            % (esc(label), esc(src), esc(link)))


# ---------------------------------------------------------------- locations
ZONES = ["Thiruvottiyur", "Manali", "Madhavaram", "Tondiarpet", "Royapuram", "Thiru-Vi-Ka Nagar", "Ambattur", "Anna Nagar",
         "Teynampet", "Kodambakkam", "Valasaravakkam", "Alandur", "Adyar", "Perungudi", "Sholinganallur"]
HOT = ["Velachery", "Porur", "OMR", "ECR", "Tambaram", "Chromepet", "Pallavaram", "Medavakkam", "Perumbakkam", "Guindy",
       "Nungambakkam", "Mylapore"]
TOP_TN = ["Coimbatore", "Madurai", "Trichy", "Salem", "Tirunelveli", "Vellore", "Erode", "Tiruppur", "Thanjavur", "Hosur"]

PIN = ('<svg viewBox="0 0 24 24" width="14" height="14" aria-hidden="true"><path fill="currentColor" d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 '
       '7-13c0-3.87-3.13-7-7-7zm0 9.5A2.5 2.5 0 1 1 12 6.5a2.5 2.5 0 0 1 0 5z"/></svg>')
CROSS = ('<svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true"><path fill="currentColor" d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 '
         '0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-1 11h-4v4h-4v-4H6v-4h4V6h4v4h4v4z"/></svg>')

HOME_LOC_CSS = """
#locations{position:relative;overflow:hidden;background:radial-gradient(1200px 500px at 85% -10%,rgba(229,62,62,.28),transparent 60%),radial-gradient(900px 500px at -10% 110%,rgba(229,62,62,.18),transparent 60%),linear-gradient(160deg,#0f172a 0%,#1a2340 55%,#111827 100%);padding:96px 0;color:#e2e8f0}
#locations .section-header h2{color:#fff}#locations .section-header p{color:#a0aec0}
.gbl-wrap{max-width:1100px;margin:0 auto;padding:0 24px}
.gbl-stats{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:-18px 0 34px}
.gbl-stat{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.12);border-radius:16px;padding:18px 16px;text-align:center;backdrop-filter:blur(6px)}
.gbl-stat b{display:block;font-family:"Oswald",sans-serif;font-size:34px;line-height:1.1;color:#fff}.gbl-stat span{font-size:12.5px;letter-spacing:.5px;color:#a0aec0;text-transform:uppercase;font-weight:700}
.gbl-panels{display:grid;grid-template-columns:1fr 1fr;gap:18px}
.gbl-panel{background:linear-gradient(180deg,rgba(255,255,255,.08),rgba(255,255,255,.03));border:1px solid rgba(255,255,255,.12);border-radius:20px;padding:24px}
.gbl-panel h3{display:flex;align-items:center;justify-content:space-between;gap:10px;margin:0 0 6px;font-family:"Oswald",sans-serif;font-size:22px;color:#fff;font-weight:600}
.gbl-panel h3 small{font-family:"Inter",sans-serif;font-size:11px;font-weight:800;letter-spacing:1.5px;color:#fc8181;background:rgba(229,62,62,.15);border:1px solid rgba(229,62,62,.35);padding:4px 10px;border-radius:999px}
.gbl-panel p{margin:0 0 16px;font-size:14px;color:#a0aec0}
.gbl-chips{display:flex;flex-wrap:wrap;gap:8px}
.gbl-chip{display:inline-flex;align-items:center;gap:6px;font-family:"Inter",sans-serif;font-size:13px;font-weight:600;color:#e2e8f0;text-decoration:none;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.14);border-radius:999px;padding:8px 14px;transition:all .2s}
.gbl-chip svg{color:#fc8181}.gbl-chip:hover{background:#e53e3e;border-color:#e53e3e;color:#fff;transform:translateY(-1px)}.gbl-chip:hover svg{color:#fff}
.gbl-more{margin-top:14px;font-size:13px;font-weight:700;color:#fc8181;text-decoration:none;display:inline-block}.gbl-more:hover{color:#fff}
.gbl-cta{text-align:center;margin-top:34px}
.gbl-btn{display:inline-flex;align-items:center;gap:10px;font-family:"Inter",sans-serif;font-weight:800;font-size:15px;color:#fff;text-decoration:none;background:linear-gradient(135deg,#e53e3e,#a52317);padding:15px 30px;border-radius:999px;box-shadow:0 12px 30px rgba(229,62,62,.35);transition:transform .2s,box-shadow .2s}
.gbl-btn:hover{transform:translateY(-2px);box-shadow:0 16px 40px rgba(229,62,62,.45)}
#hospitals{background:#fff}
#hospitals .hosp-grid{max-width:1100px;grid-template-columns:repeat(4,1fr);gap:16px}
#hospitals .hosp-card{flex-direction:column;align-items:stretch;gap:0;padding:0;overflow:hidden;background:#fff;border:1px solid #edf2f7;border-radius:16px;box-shadow:0 6px 24px rgba(15,23,42,.06)}
#hospitals .hosp-card:hover{transform:translateY(-4px);box-shadow:0 18px 40px rgba(15,23,42,.14);border-color:#fed7d7}
#hospitals .hosp-ico{width:100%;min-width:0;height:150px;border-radius:0}
#hospitals .hosp-ico svg{width:34px;height:34px}
#hospitals .hosp-txt{padding:14px 16px 16px;position:relative}
#hospitals .hosp-txt strong{font-size:15px}
#hospitals .hosp-txt small{display:flex;align-items:center;gap:4px}
#hospitals .hosp-txt small::before{content:"";width:6px;height:6px;border-radius:50%;background:#38a169;box-shadow:0 0 0 3px rgba(56,161,105,.18)}
@media(max-width:900px){.gbl-stats{grid-template-columns:repeat(2,1fr)}.gbl-panels{grid-template-columns:1fr}#hospitals .hosp-grid{grid-template-columns:repeat(2,1fr)}}
@media(max-width:520px){#locations{padding:70px 0}.gbl-stat b{font-size:28px}#hospitals .hosp-grid{grid-template-columns:1fr 1fr;gap:10px}#hospitals .hosp-ico{height:110px}#hospitals .hosp-txt{padding:10px 12px 12px}#hospitals .hosp-txt strong{font-size:13.5px}}
"""


def build_locations(src, chennai, tn, area_url, by_area, hosp, photo_url):
    n_hosp = len(hosp)
    hosp_round = "%d+" % (n_hosp // 100 * 100)
    cnt = lambda rdir, a: len(by_area.get((rdir, a), []))

    def home_chip(rdir, a):
        return ('<a class="gbl-chip" href="%s" onclick="gbOpenArea(\'%s\');return false;">%s%s</a>'
                % (area_url[(rdir, a)], a.replace("'", "\\'"), PIN, esc(a)))

    chen_chips = "".join(home_chip("chennai", a) for a in HOT + ZONES[:6] if ("chennai", a) in area_url)
    tn_chips = "".join(home_chip("tamil-nadu", a) for a in TOP_TN if ("tamil-nadu", a) in area_url)
    home = f"""<!--GB-LOC--><style>{HOME_LOC_CSS}</style>
<section id="locations">
<div class="section-header reveal"><span class="section-eyebrow">Where We Serve</span><h2>Serving Chennai &amp; All of Tamil Nadu</h2><p>Ambulances on standby across every Chennai zone and every district headquarters in Tamil Nadu &mdash; tap your area to see the hospitals near you.</p></div>
<div class="gbl-wrap">
<div class="gbl-stats reveal"><div class="gbl-stat"><b>{len(chennai)}</b><span>Chennai areas</span></div><div class="gbl-stat"><b>{len(tn)}</b><span>Tamil Nadu cities</span></div><div class="gbl-stat"><b>{hosp_round}</b><span>Hospitals covered</span></div><div class="gbl-stat"><b>24/7</b><span>Dispatch</span></div></div>
<div class="gbl-panels">
<div class="gbl-panel reveal"><h3>Chennai <small>{len(chennai)} AREAS</small></h3><p>Most-requested pickup areas across North, Central and South Chennai.</p><div class="gbl-chips">{chen_chips}</div><a class="gbl-more" href="/locations/#chennai">See all {len(chennai)} Chennai areas &rarr;</a></div>
<div class="gbl-panel reveal"><h3>Tamil Nadu <small>{len(tn)} CITIES</small></h3><p>Long-distance, ICU and hospital-to-hospital transfers to every major city.</p><div class="gbl-chips">{tn_chips}</div><a class="gbl-more" href="/locations/#tamil-nadu">See all {len(tn)} cities &rarr;</a></div>
</div>
<div class="gbl-cta reveal"><a class="gbl-btn" href="/locations/">Explore All Locations &rarr;</a></div>
</div>
</section><!--/GB-LOC-->"""

    # ---------- /locations/ page
    def top_names(rdir, a, k=3):
        hs = sorted(by_area.get((rdir, a), []), key=lambda h: (not photo_url(h["name"]), h["home"] != a, h["name"]))
        return [h["name"] for h in hs[:k]]

    def card(rdir, a, badge=""):
        tops = top_names(rdir, a)
        q = (a + " " + " ".join(h["name"] for h in by_area.get((rdir, a), []))).lower()
        return ('<a class="lc" href="%s" data-q="%s"><span class="lc-h"><span class="lc-pin">%s</span><b>%s</b>%s</span>'
                '<span class="lc-n">%d hospitals</span><span class="lc-t">%s</span><span class="lc-go">View hospitals &rarr;</span></a>'
                % (area_url[(rdir, a)], esc(q), PIN, esc(a), ('<i>%s</i>' % badge) if badge else "", cnt(rdir, a),
                   esc(" · ".join(tops))))

    zones = "".join(card("chennai", a, "Zone") for a in ZONES if ("chennai", a) in area_url)
    hot = "".join(card("chennai", a, "High demand") for a in HOT if ("chennai", a) in area_url)
    letters = {}
    for a in sorted(chennai):
        letters.setdefault(a[0].upper(), []).append(a)
    az_nav = "".join('<a href="#az-%s">%s</a>' % (L, L) for L in letters)
    az = "".join('<div class="az" id="az-%s" data-grp><h4>%s</h4><div class="az-list">%s</div></div>' % (
        L, L, "".join('<a href="%s" data-q="%s">%s<small>%d</small></a>' % (
            area_url[("chennai", a)], esc((a + " " + " ".join(h["name"] for h in by_area.get(("chennai", a), []))).lower()),
            esc(a), cnt("chennai", a)) for a in lst)) for L, lst in letters.items())
    tn_cards = "".join(card("tamil-nadu", a, "Top city" if a in TOP_TN[:6] else "") for a in sorted(tn, key=lambda c: (c not in TOP_TN, TOP_TN.index(c) if c in TOP_TN else 0, c)))
    extra = "".join(card("chennai", a, "Chennai belt") for a in ("Chengalpattu", "Tiruvallur") if ("chennai", a) in area_url)

    # major hospitals = the home page Hospital Coverage list
    by_name = {}
    for h in hosp.values():
        by_name.setdefault(h["name"], h)
    majors = re.findall(r"gbOpenHosp\('((?:[^'\\]|\\.)*)','((?:[^'\\]|\\.)*)','((?:[^'\\]|\\.)*)'\)",
                        src[src.index('<section id="hospitals">'):])
    mh = ""
    for n, addr, area in majors[:12]:
        n = n.replace("\\'", "'")
        h = by_name.get(n) or next((x for x in hosp.values() if x["name"].lower().startswith(n.split(",")[0].lower())), None)
        link = h["url"] if h else area_url.get(("chennai", area), "/chennai/")
        ph = photo_url(n)
        img = ('<img src="%s" alt="%s" loading="lazy" width="320" height="200" onerror="this.remove()">' % (esc(ph), esc(n))) if ph else ""
        short, _, loc = n.partition(",")
        mh += ('<a class="mh" href="%s" data-q="%s"><span class="mh-ph">%s%s</span><span class="mh-b"><b>%s</b><small>%s%s</small></span></a>'
               % (esc(link), esc((n + " " + area).lower()), CROSS, img, esc(short), PIN, esc((loc or area).strip())))

    css = """*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;font-family:"Inter",system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;color:#2d3748;background:#f7fafc;line-height:1.6}
a{color:inherit}h1,h2,h3,h4{font-family:"Oswald","Inter",sans-serif;letter-spacing:.2px}
.top{position:sticky;top:0;z-index:20;background:rgba(255,255,255,.92);backdrop-filter:blur(10px);border-bottom:1px solid #edf2f7}
.top .in{max-width:1180px;margin:0 auto;padding:10px 20px;display:flex;align-items:center;gap:18px}
.brand{display:flex;align-items:center;gap:10px;text-decoration:none;color:#1a2340;font-weight:800;font-size:15px;letter-spacing:.5px;margin-right:auto}.brand small{display:block;color:#c0392b;font-size:10px;letter-spacing:2px}
.top nav{display:flex;gap:22px}.top nav a{text-decoration:none;font-weight:700;font-size:14px;color:#4a5568}.top nav a.on,.top nav a:hover{color:#c0392b}
.call{display:inline-flex;align-items:center;gap:6px;text-decoration:none;background:linear-gradient(135deg,#e53e3e,#a52317);color:#fff;font-weight:800;font-size:14px;padding:10px 18px;border-radius:999px;box-shadow:0 8px 20px rgba(229,62,62,.3)}
.hero{position:relative;overflow:hidden;color:#fff;background:radial-gradient(900px 420px at 90% -20%,rgba(229,62,62,.35),transparent 60%),radial-gradient(700px 400px at -10% 120%,rgba(229,62,62,.2),transparent 60%),linear-gradient(160deg,#0f172a,#1a2340 60%,#111827);padding:64px 20px 90px}
.hero .in{max-width:1180px;margin:0 auto}
.eb{display:inline-block;font-size:11px;font-weight:800;letter-spacing:3px;color:#fc8181;text-transform:uppercase;margin-bottom:10px}
.hero h1{font-size:clamp(32px,5vw,54px);line-height:1.1;margin:0 0 14px}.hero h1 em{font-style:normal;color:#fc8181}
.hero p{max-width:640px;color:#cbd5e0;font-size:16.5px;margin:0 0 26px}
.stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;max-width:760px}
.st{background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.13);border-radius:14px;padding:14px}.st b{display:block;font-family:"Oswald",sans-serif;font-size:30px;line-height:1.1}.st span{font-size:11.5px;font-weight:700;letter-spacing:.6px;text-transform:uppercase;color:#a0aec0}
.search{max-width:1180px;margin:-34px auto 0;padding:0 20px;position:relative;z-index:5}
.search .box{display:flex;align-items:center;gap:12px;background:#fff;border-radius:18px;padding:8px 8px 8px 20px;box-shadow:0 20px 50px rgba(15,23,42,.18);border:1px solid #edf2f7}
.search input{flex:1;border:0;outline:0;font:inherit;font-size:16px;padding:12px 0;min-width:0}
.tabs{display:flex;gap:6px;flex-wrap:wrap}.tabs a{text-decoration:none;font-weight:800;font-size:13px;padding:10px 14px;border-radius:12px;color:#4a5568;background:#f7fafc}.tabs a:hover{background:#fff5f5;color:#c0392b}
main{max-width:1180px;margin:0 auto;padding:36px 20px 20px}
.sec{margin-bottom:46px;scroll-margin-top:80px}
.sh{display:flex;align-items:flex-end;justify-content:space-between;gap:16px;margin-bottom:18px;flex-wrap:wrap}
.sh h2{font-size:clamp(24px,3vw,34px);margin:0;color:#1a2340;line-height:1.15}.sh p{margin:4px 0 0;color:#718096;font-size:14.5px}
.pill{font-size:11px;font-weight:800;letter-spacing:1.5px;color:#c0392b;background:#fff5f5;border:1px solid #fed7d7;padding:5px 12px;border-radius:999px;text-transform:uppercase}
h3.sub{font-size:19px;color:#1a2340;margin:26px 0 12px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:14px}
.lc{position:relative;display:flex;flex-direction:column;gap:6px;text-decoration:none;background:#fff;border:1px solid #edf2f7;border-radius:16px;padding:16px 16px 14px;box-shadow:0 4px 18px rgba(15,23,42,.05);transition:transform .2s,box-shadow .2s,border-color .2s}
.lc:hover{transform:translateY(-3px);box-shadow:0 16px 36px rgba(15,23,42,.12);border-color:#fed7d7}
.lc-h{display:flex;align-items:center;gap:8px}.lc-h b{font-size:16.5px;color:#1a2340}
.lc-pin{display:inline-flex;align-items:center;justify-content:center;width:28px;height:28px;border-radius:9px;background:linear-gradient(135deg,#e53e3e,#a52317);color:#fff;flex:none}
.lc-h i{margin-left:auto;font-style:normal;font-size:10px;font-weight:800;letter-spacing:1px;text-transform:uppercase;color:#c0392b;background:#fff5f5;padding:3px 8px;border-radius:999px;white-space:nowrap}
.lc-n{font-size:13px;font-weight:800;color:#38a169}
.lc-t{font-size:13px;color:#718096;line-height:1.45;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;min-height:38px}
.lc-go{font-size:13px;font-weight:800;color:#c0392b;margin-top:2px}
.aznav{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:14px}.aznav a{text-decoration:none;font-weight:800;font-size:13px;width:34px;height:34px;display:inline-flex;align-items:center;justify-content:center;border-radius:10px;background:#fff;border:1px solid #edf2f7;color:#1a2340}.aznav a:hover{background:#c0392b;color:#fff}
.azwrap{background:#fff;border:1px solid #edf2f7;border-radius:18px;padding:8px 20px 18px;columns:3 260px;column-gap:28px}
.az{break-inside:avoid;padding-top:12px;scroll-margin-top:90px}.az h4{margin:0 0 6px;font-size:18px;color:#c0392b;border-bottom:1px solid #fed7d7;padding-bottom:2px}
.az-list a{display:flex;justify-content:space-between;gap:10px;text-decoration:none;padding:5px 2px;font-size:14.5px;color:#2d3748;border-bottom:1px dashed #edf2f7}.az-list a:hover{color:#c0392b}
.az-list small{font-weight:800;color:#a0aec0;font-size:12px}
.mgrid{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}
.mh{display:flex;flex-direction:column;text-decoration:none;background:#fff;border:1px solid #edf2f7;border-radius:16px;overflow:hidden;box-shadow:0 4px 18px rgba(15,23,42,.05);transition:transform .2s,box-shadow .2s}.mh:hover{transform:translateY(-3px);box-shadow:0 16px 36px rgba(15,23,42,.12)}
.mh-ph{position:relative;height:150px;background:linear-gradient(135deg,#e53e3e,#a52317);color:#fff;display:flex;align-items:center;justify-content:center}.mh-ph img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.mh-b{padding:12px 14px 14px}.mh-b b{display:block;color:#1a2340;font-size:15px}.mh-b small{display:flex;align-items:center;gap:4px;color:#718096;font-size:13px}.mh-b small svg{color:#c0392b}
.band{margin:10px 0 40px;border-radius:22px;padding:30px;color:#fff;background:linear-gradient(135deg,#c0392b,#7b1d12);display:flex;align-items:center;justify-content:space-between;gap:20px;flex-wrap:wrap;box-shadow:0 20px 50px rgba(192,57,43,.3)}
.band h2{margin:0 0 4px;font-size:28px}.band p{margin:0;opacity:.9}.band .acts{display:flex;gap:10px;flex-wrap:wrap}
.band a{text-decoration:none;font-weight:800;padding:13px 22px;border-radius:999px;background:#fff;color:#c0392b}.band a.wa{background:#25d366;color:#fff}
.none{display:none;text-align:center;color:#718096;padding:30px;background:#fff;border-radius:16px;border:1px dashed #cbd5e0}
footer{background:#0f172a;color:#a0aec0;padding:30px 20px 100px;font-size:14px}footer .in{max-width:1180px;margin:0 auto}footer a{color:#fff}
.bar{position:fixed;left:0;right:0;bottom:0;display:flex;gap:8px;padding:10px;background:#fff;border-top:1px solid #e2e8f0;z-index:30}.bar a{flex:1;text-align:center;text-decoration:none;font-weight:800;padding:12px;border-radius:999px;color:#fff;background:#c0392b}.bar a.wa{background:#25d366}
.hide{display:none!important}
@media(max-width:900px){.top nav{display:none}.mgrid{grid-template-columns:repeat(2,1fr)}.stats{grid-template-columns:repeat(2,1fr)}}
@media(min-width:900px){.bar{display:none}footer{padding-bottom:30px}}
@media(max-width:520px){.hero{padding:44px 18px 80px}.search .box{flex-wrap:wrap;padding:10px 12px}.tabs{width:100%}.tabs a{flex:1;text-align:center;padding:9px 6px}.mh-ph{height:110px}.azwrap{padding:4px 14px 14px}}
"""
    js = """<script>(function(){var i=document.getElementById('q');if(!i)return;var items=[].slice.call(document.querySelectorAll('[data-q]')),grps=[].slice.call(document.querySelectorAll('[data-grp]')),secs=[].slice.call(document.querySelectorAll('[data-sec]')),none=document.getElementById('none');
i.addEventListener('input',function(){var q=i.value.toLowerCase().trim(),any=false;items.forEach(function(e){var ok=!q||e.getAttribute('data-q').indexOf(q)>=0;e.classList.toggle('hide',!ok);if(ok&&q)any=true;});
grps.forEach(function(g){g.classList.toggle('hide',!!q&&!g.querySelector('[data-q]:not(.hide)'));});secs.forEach(function(s){s.classList.toggle('hide',!!q&&!s.querySelector('[data-q]:not(.hide)'));});none.style.display=q&&!any?'block':'none';});})();</script>"""
    crumbs = [("Home", "/"), ("Locations", None)]
    title = "Ambulance Service Locations in Chennai & Tamil Nadu | God Bless Ambulance"
    desc = ("God Bless Ambulance serves %d Chennai areas and %d Tamil Nadu cities, covering %s hospitals. 24/7 ICU, ALS and BLS ambulances. Call %s."
            % (len(chennai), len(tn), hosp_round, PHONE_DISPLAY))
    ld = [crumb_ld(crumbs), {"@context": "https://schema.org", "@type": "EmergencyService", "name": "God Bless Ambulance Service",
                              "url": SITE + "/", "telephone": "+91-" + PHONE,
                              "areaServed": [{"@type": "City", "name": "Chennai"}] + [{"@type": "City", "name": c} for c in sorted(tn)]}]
    lds = "".join('<script type="application/ld+json">%s</script>' % json.dumps(x, ensure_ascii=False, separators=(",", ":")) for x in ld)
    page_html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title><meta name="description" content="{esc(desc)}"><link rel="canonical" href="{SITE}/locations/">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{SITE}/locations/">
<meta name="theme-color" content="#0f172a"><link rel="icon" href="/favicon.ico"><link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&family=Oswald:wght@600;700&display=swap" rel="stylesheet">
<style>{css}</style>{lds}</head><body>
<header class="top"><div class="in"><a class="brand" href="/">{LOGO}<span>GOD BLESS AMBULANCE<small>24/7 SERVICE</small></span></a>
<nav><a href="/">Home</a><a href="/#services">Services</a><a class="on" href="/locations/">Locations</a><a href="/#contact">Contact</a></nav>
<a class="call" href="tel:{PHONE}">&#128222; {PHONE_DISPLAY}</a></div></header>
<section class="hero"><div class="in"><span class="eb">Where we serve</span><h1>Ambulance Service Across <em>Chennai</em> &amp; <em>Tamil Nadu</em></h1>
<p>ICU, ALS, BLS and freezer box ambulances on standby 24/7. Find your area or city to see the hospitals we cover, then call once &mdash; we send the nearest available ambulance.</p>
<div class="stats"><div class="st"><b>{len(chennai)}</b><span>Chennai areas</span></div><div class="st"><b>{len(tn)}</b><span>TN cities</span></div><div class="st"><b>{hosp_round}</b><span>Hospitals</span></div><div class="st"><b>24/7</b><span>Dispatch</span></div></div></div></section>
<div class="search"><div class="box"><span aria-hidden="true">&#128269;</span><input id="q" type="search" placeholder="Search area, city or hospital (e.g. Porur, Madurai, Apollo)" aria-label="Search locations">
<div class="tabs"><a href="#chennai">Chennai</a><a href="#tamil-nadu">Tamil Nadu</a><a href="#hospitals">Hospitals</a></div></div></div>
<main>
<p class="none" id="none">No area or hospital matches your search. Call {PHONE_DISPLAY} &mdash; we cover all of Chennai and Tamil Nadu.</p>
<section class="sec" id="chennai" data-sec><div class="sh"><div><h2>Chennai</h2><p>All 15 corporation zones and every locality, with the hospitals in each.</p></div><span class="pill">{len(chennai)} areas</span></div>
<div data-grp><h3 class="sub">Greater Chennai Corporation zones</h3><div class="grid">{zones}</div></div>
<div data-grp><h3 class="sub">High-demand pickup areas</h3><div class="grid">{hot}</div></div>
<h3 class="sub">All Chennai areas A&ndash;Z</h3><nav class="aznav" aria-label="Jump to letter">{az_nav}</nav><div class="azwrap">{az}</div></section>
<section class="sec" id="tamil-nadu" data-sec><div class="sh"><div><h2>Tamil Nadu</h2><p>Every district headquarters, plus Hosur and Kumbakonam &mdash; long-distance and ICU transfers to and from Chennai.</p></div><span class="pill">{len(tn)} cities</span></div>
<div data-grp><div class="grid">{tn_cards}{extra}</div></div></section>
<section class="sec" id="hospitals" data-sec><div class="sh"><div><h2>Major hospitals</h2><p>Regular pickups, discharges and inter-hospital transfers.</p></div><span class="pill">Hospital transfers</span></div>
<div data-grp><div class="mgrid">{mh}</div></div></section>
<div class="band"><div><h2>Need an ambulance now?</h2><p>One call &mdash; we confirm the ambulance type and dispatch immediately.</p></div><div class="acts"><a href="tel:{PHONE}">&#128222; Call {PHONE_DISPLAY}</a><a class="wa" href="https://wa.me/{WA}?text={quote('Hello, I need an ambulance.')}">WhatsApp</a><a href="/#booking">Book online</a></div></div>
</main>
<footer><div class="in"><b style="color:#fff">God Bless Ambulance Service</b><br>{esc(OFFICE)}<br>Phone: <a href="tel:{PHONE}">{PHONE_DISPLAY}</a> &middot; Open 24 hours, 7 days<br><br><a href="/">Home</a> &middot; <a href="/#booking">Book an ambulance</a> &middot; <a href="/chennai/">Chennai areas</a> &middot; <a href="/tamil-nadu/">Tamil Nadu cities</a><br><br><span style="opacity:.75">Designed &amp; developed by <a href="https://thinkthroughtechnology.in" target="_blank" rel="noopener">Think Through Technology</a> &middot; <a href="https://thinkthroughtechnology.in" target="_blank" rel="noopener">thinkthroughtechnology.in</a></span></div></footer>
<div class="bar"><a href="tel:{PHONE}">&#128222; Call</a><a class="wa" href="https://wa.me/{WA}">WhatsApp</a></div>
{js}</body></html>
"""
    write("/locations/", page_html)
    return home


# ---------------------------------------------------------------- build
def build():
    with open(os.path.join(ROOT, "index.html"), encoding="utf-8") as f:
        src = f.read()
    chennai = js_obj(src, "GB_AREA_HOSPITALS")
    tn = js_obj(src, "GB_TN_CITIES")
    padma = js_obj(src, "GB_PADMA_PHOTOS")
    # areas that are Tamil Nadu towns rather than Chennai localities stay under /chennai/ only if the home page lists them there
    regions = [("chennai", "Chennai", chennai), ("tamil-nadu", "Tamil Nadu", tn)]

    for d in ("chennai", "tamil-nadu"):
        shutil.rmtree(os.path.join(ROOT, d), ignore_errors=True)

    urls = [(SITE + "/", "1.0")]
    area_url = {}
    # ---- decide one home area per hospital (no duplicate pages)
    hosp = {}  # key -> dict
    for rdir, rname, data in regions:
        for area, items in data.items():
            area_url[(rdir, area)] = "/%s/%s/" % (rdir, slug(area))
            for n, addr in items:
                key = (rdir, n.lower(), addr.split(",")[0].lower())
                h = hosp.setdefault(key, {"name": n, "addr": addr, "areas": [], "rdir": rdir, "rname": rname})
                h["areas"].append(area)
    for h in hosp.values():
        home = next((a for a in h["areas"] if norm(a) and norm(a) in norm(h["addr"])), h["areas"][0])
        h["home"] = home
    used = set()
    for h in sorted(hosp.values(), key=lambda x: (x["rdir"], x["home"], x["name"])):
        base = area_url[(h["rdir"], h["home"])] + slug(h["name"])
        u, i = base + "/", 2
        while u in used:
            u = "%s-%d/" % (base, i)
            i += 1
        used.add(u)
        h["url"] = u
    by_area = {}
    for h in hosp.values():
        for a in h["areas"]:
            by_area.setdefault((h["rdir"], a), []).append(h)

    # neighbours: areas that share hospitals
    neigh = {}
    for h in hosp.values():
        for a in h["areas"]:
            for b in h["areas"]:
                if a != b:
                    neigh.setdefault((h["rdir"], a), {}).setdefault(b, 0)
                    neigh[(h["rdir"], a)][b] += 1

    def photo_url(name):
        p = padma.get(name)
        if not p:
            return ""
        return "https://padmaambulanceservice.com/_next/image?w=640&q=75&url=" + quote("/hospital-images/%s.jpg" % p, safe="")

    # ---- area pages
    for rdir, rname, data in regions:
        for area, items in data.items():
            path = area_url[(rdir, area)]
            place = area if rname == "Tamil Nadu" else "%s, Chennai" % area
            hs = sorted(by_area[(rdir, area)], key=lambda x: (x["home"] != area, x["name"]))
            pins = sorted({pincode(h["addr"]) for h in hs if pincode(h["addr"])})
            roads = []
            for h in hs:
                r = road(h["addr"])
                if r and r not in roads:
                    roads.append(r)
            nb = sorted(neigh.get((rdir, area), {}).items(), key=lambda x: -x[1])[:10]
            title = "Ambulance Service in %s | 24/7 ICU Ambulance | God Bless" % place
            desc = ("24/7 ambulance service in %s. ICU, ALS, BLS and freezer box ambulances for %d hospitals in and around %s. "
                    "Call %s." % (place, len(hs), area, PHONE_DISPLAY))
            intro = pick(area, [
                "Need an ambulance in %s? God Bless Ambulance keeps ICU, ALS and BLS ambulances ready around the clock for emergencies, hospital discharges and transfers from %s." % (place, area),
                "God Bless Ambulance serves %s day and night. Call once and we send the nearest available ambulance, with trained staff and oxygen on board, to your home or hospital in %s." % (place, area),
                "From home pickups to hospital-to-hospital transfers, God Bless Ambulance covers every street in %s. Our ICU and basic ambulances run 24 hours, 7 days a week." % place,
            ])
            facts = ['<li><b>Hospitals covered</b>%d in and around %s</li>' % (len(hs), esc(area))]
            if pins:
                facts.append('<li><b>Pincodes</b>%s</li>' % esc(", ".join(pins[:8])))
            if roads:
                facts.append('<li><b>Main roads</b>%s</li>' % esc(", ".join(roads[:4])))
            facts.append('<li><b>Availability</b>24 hours, 7 days a week</li>')
            hl = "".join('<li><a href="%s">%s</a><small>%s</small></li>' % (esc(h["url"]), esc(h["name"]), esc(h["addr"])) for h in hs)
            nb_html = ('<section class="card"><h2>Nearby areas we also serve</h2><div class="chips">%s</div></section>' % "".join(
                '<a href="%s">%s</a>' % (esc(area_url[(rdir, b)]), esc(b)) for b, _ in nb)) if nb else ""
            faqs = [
                ("How do I book an ambulance in %s?" % area,
                 "Call %s or message us on WhatsApp with the pickup address in %s. We confirm the ambulance type and send the nearest available vehicle." % (PHONE_DISPLAY, area)),
                ("Do you have ICU ambulances in %s?" % area,
                 "Yes. ICU ambulances with ventilator and cardiac monitor, as well as ALS, BLS and freezer box ambulances, are available for %s." % place),
                ("Which hospitals in %s do you cover?" % area,
                 "We cover all %d hospitals listed on this page, including %s, and any other hospital you need to reach." % (
                     len(hs), ", ".join(h["name"] for h in hs[:3]))),
                ("Is the ambulance service in %s available at night?" % area,
                 "Yes. God Bless Ambulance works 24 hours a day, including nights, Sundays and holidays."),
            ]
            crumbs = [("Home", "/"), (rname, "/%s/" % rdir), (area, None)]
            body = (f'<section class="hero"><h1>Ambulance Service in {esc(place)}</h1><p>{esc(intro)}</p>'
                    f'<div class="acts"><a class="btn ghost" href="tel:{PHONE}">&#128222; Call {PHONE_DISPLAY}</a>'
                    f'<a class="btn green" href="https://wa.me/{WA}?text={quote("I need an ambulance in " + place)}">WhatsApp</a>'
                    f'<a class="btn ghost" href="/#booking">Book online</a></div></section>'
                    f'<section class="card"><h2>About our service in {esc(area)}</h2><ul class="facts">{"".join(facts)}</ul></section>'
                    f'<section class="card"><h2>Hospitals in and around {esc(area)}</h2><ul class="list">{hl}</ul></section>'
                    + services_html(area) + map_block(place + ", Tamil Nadu", "%s on the map" % area) + nb_html + faq_html(faqs))
            ld = [business_ld(area, rname), crumb_ld(crumbs), faq_ld(faqs)]
            write(path, page(path, title, desc, body, ld, crumbs, "Hello, I need an ambulance in %s." % place))
            urls.append((SITE + path, "0.8"))

    # ---- hospital pages
    for h in hosp.values():
        rdir, rname, area, n, addr = h["rdir"], h["rname"], h["home"], h["name"], h["addr"]
        place = area if rname == "Tamil Nadu" else "%s, Chennai" % area
        path = h["url"]
        others = [o for o in by_area[(rdir, area)] if o is not h][:8]
        pin = pincode(addr)
        title = "Ambulance Service near %s, %s | God Bless Ambulance" % (n, area)
        if len(title) > 70:
            title = "Ambulance near %s, %s" % (n, area)
        desc = ("24/7 ambulance to and from %s, %s. ICU, ALS and BLS ambulances for admission, discharge and hospital transfer. Call %s."
                % (n, place, PHONE_DISPLAY))
        intro = pick(n + addr, [
            "Taking a patient to %s or bringing them home after discharge? God Bless Ambulance sends ICU, ALS or BLS ambulances to %s at any hour." % (n, area),
            "God Bless Ambulance runs 24/7 ambulances to and from %s in %s, for emergencies, planned admissions, discharges and transfers to other hospitals." % (n, area),
            "Need an ambulance near %s? Call God Bless Ambulance for a quick pickup anywhere in %s, with trained staff and oxygen on board." % (n, place),
        ])
        ph = photo_url(n)
        photo = ('<div class="photo"><img src="%s" alt="%s, %s" width="640" height="320" fetchpriority="high" '
                 'onerror="this.parentNode.style.display=\'none\'"></div>' % (esc(ph), esc(n), esc(area))) if ph else ""
        facts = ['<li><b>Hospital</b>%s</li>' % esc(n), '<li><b>Address</b>%s</li>' % esc(addr), '<li><b>Area</b>%s</li>' % esc(place)]
        if pin:
            facts.append('<li><b>Pincode</b>%s</li>' % pin)
        if len(h["areas"]) > 1:
            facts.append('<li><b>Also serving</b>%s</li>' % esc(", ".join(a for a in h["areas"] if a != area)[:120]))
        ol = "".join('<li><a href="%s">%s</a><small>%s</small></li>' % (esc(o["url"]), esc(o["name"]), esc(o["addr"])) for o in others)
        faqs = [
            ("How do I book an ambulance to %s?" % n,
             "Call %s or WhatsApp us with the pickup address and say the patient is going to %s, %s." % (PHONE_DISPLAY, n, area)),
            ("Can you shift a patient from %s to another hospital?" % n,
             "Yes. We handle discharges and hospital-to-hospital transfers from %s, including ICU transfers with a ventilator, within Chennai and across Tamil Nadu." % n),
            ("Is the ambulance to %s available 24 hours?" % n,
             "Yes. God Bless Ambulance runs 24 hours a day, 7 days a week, including nights and holidays."),
        ]
        crumbs = [("Home", "/"), (rname, "/%s/" % rdir), (area, area_url[(rdir, area)]), (n, None)]
        body = (f'<section class="hero"><h1>Ambulance Service near {esc(n)}</h1><p>{esc(intro)}</p>'
                f'<div class="acts"><a class="btn ghost" href="tel:{PHONE}">&#128222; Call {PHONE_DISPLAY}</a>'
                f'<a class="btn green" href="https://wa.me/{WA}?text={quote("I need an ambulance to/from " + n + ", " + area)}">WhatsApp</a>'
                f'<a class="btn ghost" href="/#booking">Book online</a></div></section>'
                f'<section class="card">{photo}<h2>{esc(n)}</h2><ul class="facts">{"".join(facts)}</ul></section>'
                + services_html(n) + map_block(n + ", " + addr, "Location of %s" % n)
                + (f'<section class="card"><h2>Other hospitals in {esc(area)}</h2><ul class="list">{ol}</ul>'
                   f'<p><a href="{esc(area_url[(rdir, area)])}">All hospitals in {esc(area)} &rarr;</a></p></section>' if ol else "")
                + faq_html(faqs))
        ld = [business_ld(area, rname), crumb_ld(crumbs), faq_ld(faqs)]
        write(path, page(path, title, desc, body, ld, crumbs, "Hello, I need an ambulance to/from %s, %s." % (n, area)))
        urls.append((SITE + path, "0.6"))

    # ---- hubs
    for rdir, rname, data in regions:
        path = "/%s/" % rdir
        chips = "".join('<a href="%s">%s</a>' % (esc(area_url[(rdir, a)]), esc(a)) for a in sorted(data))
        title = ("Ambulance Service in All Chennai Areas | God Bless Ambulance" if rdir == "chennai"
                 else "Ambulance Service Across Tamil Nadu | God Bless Ambulance")
        desc = ("24/7 ICU, ALS and BLS ambulance service in %d %s. Pick your area to see hospitals near you. Call %s."
                % (len(data), "Chennai areas" if rdir == "chennai" else "Tamil Nadu cities", PHONE_DISPLAY))
        h1 = "Ambulance Service in All Chennai Areas" if rdir == "chennai" else "Ambulance Service Across Tamil Nadu"
        crumbs = [("Home", "/"), (rname, None)]
        body = (f'<section class="hero"><h1>{h1}</h1><p>Choose your {"area" if rdir == "chennai" else "city"} to see the hospitals we cover and book an ambulance.</p>'
                f'<div class="acts"><a class="btn ghost" href="tel:{PHONE}">&#128222; Call {PHONE_DISPLAY}</a></div></section>'
                f'<section class="card"><h2>{len(data)} {"areas" if rdir == "chennai" else "cities"}</h2><div class="chips">{chips}</div></section>')
        write(path, page(path, title, desc, body, [crumb_ld(crumbs)], crumbs, "Hello, I need an ambulance."))
        urls.append((SITE + path, "0.9"))

    # ---- locations page + crisp home section
    home_loc = build_locations(src, chennai, tn, area_url, by_area, hosp, photo_url)
    urls.insert(1, (SITE + "/locations/", "0.9"))

    # ---- sitemap
    with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        for u, p in urls:
            f.write("<url><loc>%s</loc><lastmod>%s</lastmod><priority>%s</priority></url>\n" % (esc(u), TODAY, p))
        f.write("</urlset>\n")
    with open(os.path.join(ROOT, "robots.txt"), "w") as f:
        f.write("User-agent: *\nAllow: /\n\nSitemap: %s/sitemap.xml\n" % SITE)

    # ---- home page: make area chips real links (popup still opens), static TN chips
    def chip(m):
        area = m.group(2).replace("\\'", "'")
        rdir = "tamil-nadu" if area in tn else "chennai"
        u = area_url.get((rdir, area)) or area_url.get(("chennai", area))
        if not u:
            return m.group(0)
        return '<a class="%s" href="%s" onclick="gbOpenArea(\'%s\');return false;">%s</a>' % (
            m.group(1), u, m.group(2), m.group(3))
    src = re.sub(r'<button type="button" class="(loc-chip[^"]*)" onclick="gbOpenArea\(\'((?:[^\'\\]|\\.)*)\'\)">([^<]*)</button>', chip, src)
    tn_chips = "".join('<a class="loc-chip" href="%s" onclick="gbOpenArea(\'%s\');return false;">%s</a>' % (
        area_url[("tamil-nadu", c)] if c in tn else area_url[("chennai", c)], c.replace("'", "\\'"), esc(c))
        for c in sorted(list(tn) + [x for x in ("Chengalpattu", "Tiruvallur") if x in chennai]))
    src = re.sub(r'<div class="loc-chips reveal" id="tnChips">.*?</div>', '<div class="loc-chips reveal" id="tnChips">%s</div>' % tn_chips, src, count=1, flags=re.S)
    if "b.children.length" not in src:
        src = src.replace("var b=document.getElementById('tnChips');if(!b||", "var b=document.getElementById('tnChips');if(!b||b.children.length||")
    # replace the old location sections (first run) or the previous generated block
    if "<!--GB-LOC-->" in src:
        src = re.sub(r"<!--GB-LOC-->.*?<!--/GB-LOC-->", lambda m: home_loc, src, count=1, flags=re.S)
    else:
        a, b = src.index('<section id="locations">'), src.index('<section id="hospitals">')
        src = src[:a] + home_loc + "\n" + src[b:]
    src = src.replace('<button type="button" class="loc-btn-solid" onclick="gbOpenAll()">View All Hospital Locations</button>',
                      '<a class="loc-btn-solid" href="/locations/#hospitals">View All Hospital Locations</a>')
    # add "Locations" after "Services" in every menu (the page has two desktop navs and one mobile nav)
    src = src.replace('<a href="#services">Services</a>\n<a href="#equipment">',
                      '<a href="#services">Services</a>\n<a href="/locations/">Locations</a>\n<a href="#equipment">')
    src = src.replace('<a href="#services" onclick="toggleMobileNav()">Services</a>\n  <a href="#equipment"',
                      '<a href="#services" onclick="toggleMobileNav()">Services</a>\n  <a href="/locations/">Locations</a>\n  <a href="#equipment"')
    with open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8") as f:
        f.write(src)
    print("area pages:", sum(len(d) for _, _, d in regions), "hospital pages:", len(hosp), "sitemap urls:", len(urls))


if __name__ == "__main__":
    build()
