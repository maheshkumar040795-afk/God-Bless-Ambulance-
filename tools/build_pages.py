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
<a href="/">Home</a> &middot; <a href="/#booking">Book an ambulance</a> &middot; <a href="/chennai/">Chennai areas</a> &middot; <a href="/tamil-nadu/">Tamil Nadu cities</a></div></footer>
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
    with open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8") as f:
        f.write(src)
    print("area pages:", sum(len(d) for _, _, d in regions), "hospital pages:", len(hosp), "sitemap urls:", len(urls))


if __name__ == "__main__":
    build()
