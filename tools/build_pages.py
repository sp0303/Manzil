#!/usr/bin/env python3
"""Build the SEO landing pages (services, cities, localities) from tools/pages_data.py.

Usage (from the repository root):
    python3 tools/build_pages.py

It writes one <slug>.html per page at the site root, and refreshes:
  - sitemap.xml                    (core pages + every landing page)
  - components/footer.html         (block between SEO-LINKS markers)
  - llms.txt                       (block between SEO-PAGES markers)
Images are expected at images/pages/<img>.jpg.
"""
import datetime
import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from pages_data import PAGES, SERVICES, CITY, LOCALITY  # noqa: E402
from guides_data import GUIDES, FAQ_HUB, PUBLISHED  # noqa: E402

SITE = "https://manzils.in"
TODAY = datetime.date.today().isoformat()
CORE = [("/", "1.0", "weekly"), ("/services.html", "0.9", "monthly"), ("/projects.html", "0.8", "monthly"),
        ("/about.html", "0.8", "monthly"), ("/studio.html", "0.7", "monthly"), ("/contact.html", "0.8", "yearly")]
BY_SLUG = {p["slug"]: p for p in PAGES}
GUIDE_SLUG = {g["slug"]: g for g in GUIDES}
ALL_SLUG = {**BY_SLUG, **GUIDE_SLUG}
e = lambda s: html.escape(s, quote=True)


def business_node():
    """Reuse the business entity from index.html so every page describes the company identically."""
    src = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', src, re.S):
        for node in json.loads(block).get("@graph", []):
            if node.get("@type") == "HomeAndConstructionBusiness":
                return node
    raise SystemExit("Business JSON-LD not found in index.html")


def keywords(p):
    area = p["area"].split(",")[0]
    base = [p["h1"], f'{p["service"]} {area}', f"interior designers in {area}", f"construction company in {area}",
            f"Vastu interior design {area}", f"modular kitchen {area}", "luxury interiors", "Manzil Homes"]
    return ", ".join(dict.fromkeys(base))


def jsonld(p, biz):
    url = f"{SITE}/{p['slug']}.html"
    crumbs = [("Home", SITE + "/")]
    if p["kind"] == SERVICES:
        crumbs.append(("Services", SITE + "/services.html"))
    elif p["kind"] == LOCALITY and p.get("parent"):
        par = BY_SLUG[p["parent"]]
        crumbs.append((par["h1"], f"{SITE}/{par['slug']}.html"))
    crumbs.append((p["h1"], url))
    graph = [
        biz,
        {"@type": "WebPage", "@id": url + "#webpage", "url": url, "name": p["title"], "description": p["desc"],
         "isPartOf": {"@id": SITE + "/#website"}, "about": {"@id": SITE + "/#business"}, "inLanguage": "en-IN",
         "primaryImageOfPage": f"{SITE}/images/pages/{p['img']}.jpg"},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": i, "name": n, "item": u} for i, (n, u) in enumerate(crumbs, 1)]},
        {"@type": "Service", "@id": url + "#service", "name": p["h1"], "serviceType": p["service"],
         "description": p["desc"], "provider": {"@id": SITE + "/#business"},
         "areaServed": {"@type": "Place", "name": p["area"]}, "image": f"{SITE}/images/pages/{p['img']}.jpg"},
        {"@type": "FAQPage", "@id": url + "#faq", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in p["faqs"]]},
    ]
    txt = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, indent=2)
    return "\n".join("  " + line for line in txt.splitlines()), crumbs


PROCESS = [
    ("Discovery", "Lifestyle mapping, Vastu inputs and budget clarity."),
    ("Concept &amp; 3D", "Mood, materials and photo-realistic 3D renders."),
    ("Detailing", "Technical drawings, joinery and lighting layers."),
    ("Build &amp; Handover", "Site execution, quality checks and on-time handover."),
]
WHY = [
    ("bi-compass", "Vastu-aligned", "Planned with Vastu from the first sketch."),
    ("bi-receipt", "Transparent pricing", "Clear BOQs, tracked variations, no hidden costs."),
    ("bi-calendar-check", "On-time delivery", "Milestone-based schedules we commit to."),
    ("bi-person-workspace", "Women-led &amp; engineered", "Led by a Civil Engineer (M.Tech Structures)."),
]


def page_html(p, biz):
    url = f"{SITE}/{p['slug']}.html"
    ld, crumbs = jsonld(p, biz)
    img = f"images/pages/{p['img']}.jpg"
    crumb_html = " <span aria-hidden=\"true\">/</span> ".join(
        f'<a href="{u.replace(SITE + "/", "") or "index.html"}">{e(n)}</a>' if i < len(crumbs) - 1 else f'<span aria-current="page">{e(n)}</span>'
        for i, (n, u) in enumerate(crumbs))
    intro = "\n".join(f"        <p>{e(t)}</p>" for t in p["intro"])
    offers = "\n".join(f'          <li><i class="bi bi-check2-circle" aria-hidden="true"></i><span>{e(o)}</span></li>' for o in p["offers"])
    local = "\n".join(f"        <p>{e(t)}</p>" for t in p["local"])
    process = "\n".join(
        f'        <li class="lp-step"><span class="lp-step-n">{i}</span><div><h3 class="h6 fw-bold mb-1">{t}</h3><p class="mb-0 small text-muted">{d}</p></div></li>'
        for i, (t, d) in enumerate(PROCESS, 1))
    why = "\n".join(
        f'        <div class="col-6 col-lg-3"><div class="lp-why h-100"><i class="bi {ic}" aria-hidden="true"></i><h3 class="h6 fw-bold mt-2 mb-1">{t}</h3><p class="small text-muted mb-0">{d}</p></div></div>'
        for ic, t, d in WHY)
    faqs = "\n".join(f'        <details class="faq-item">\n          <summary>{e(q)}</summary>\n          <p>{e(a)}</p>\n        </details>' for q, a in p["faqs"])
    related = "\n".join(
        f'        <a class="lp-related" href="{r}.html"><span>{e(ALL_SLUG[r]["h1"])}</span><i class="bi bi-arrow-right" aria-hidden="true"></i></a>'
        for r in p["related"] if r in ALL_SLUG)
    wa_text = f"Hi Manzil Homes, I'd like a free consultation for {p['h1'].lower()}."
    wa = "https://wa.me/919492054954?text=" + re.sub(r"[^A-Za-z0-9]", lambda m: "%{:02X}".format(ord(m.group())), wa_text)

    return f'''<!DOCTYPE html>
<html lang="en-IN">

<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <!-- Generated by tools/build_pages.py from tools/pages_data.py. Edit the data file, not this page. -->
  <title>{e(p["title"])}</title>
  <meta name="description" content="{e(p["desc"])}" />
  <meta name="keywords" content="{e(keywords(p))}" />
  <meta name="robots" content="index, follow, max-image-preview:large" />
  <meta name="author" content="Manzil Homes" />
  <meta name="theme-color" content="#0f1335" />
  <link rel="canonical" href="{url}" />

  <meta property="og:type" content="website" />
  <meta property="og:site_name" content="Manzil Homes" />
  <meta property="og:locale" content="en_IN" />
  <meta property="og:title" content="{e(p["title"])}" />
  <meta property="og:description" content="{e(p["desc"])}" />
  <meta property="og:url" content="{url}" />
  <meta property="og:image" content="{SITE}/{img}" />
  <meta property="og:image:alt" content="{e(p["img_alt"])}" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{e(p["title"])}" />
  <meta name="twitter:description" content="{e(p["desc"])}" />
  <meta name="twitter:image" content="{SITE}/{img}" />

  <script type="application/ld+json">
{ld}
  </script>

  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Marcellus&family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" />
  <link rel="stylesheet" href="./css/style.css" />
  <link rel="icon" href="./pngs/SecondaryLogoBlack.png" type="image/png" />
  <link rel="apple-touch-icon" href="./pngs/logowithcircle.png" />
</head>

<body>
  <div id="navbar"></div>

  <!-- HERO -->
  <header class="hero-section lp-hero d-flex align-items-center text-center" style="background-image:url('{img}')">
    <div class="overlay"></div>
    <div class="hero-content container">
      <h1 class="mb-3">{e(p["h1"])}</h1>
      <p class="mb-4 lp-lead">{e(p["lead"])}</p>
      <a href="contact.html" class="btn btn-light rounded-pill px-4">Book a Free Consultation</a>
    </div>
  </header>

  <nav class="lp-crumbs container small" aria-label="Breadcrumb">
    {crumb_html}
  </nav>

  <!-- INTRO + OFFERS -->
  <section class="section-padding pt-4">
    <div class="container">
      <div class="row gx-4 gy-5 align-items-start">
        <div class="col-lg-7 lp-prose">
{intro}
          <img src="{img}" class="img-fluid rounded-4 shadow-sm mt-3" loading="lazy" alt="{e(p["img_alt"])}" />
        </div>
        <div class="col-lg-5">
          <div class="lp-card">
            <h2 class="h4 fw-bold mb-3">{e(p["offer_title"])}</h2>
            <ul class="lp-offers list-unstyled mb-4">
{offers}
            </ul>
            <a href="{wa}" target="_blank" rel="noopener" class="btn btn-success rounded-pill w-100 mb-2"><i class="bi bi-whatsapp me-2" aria-hidden="true"></i>WhatsApp Us</a>
            <a href="tel:+919492054954" class="btn btn-outline-dark rounded-pill w-100"><i class="bi bi-telephone me-2" aria-hidden="true"></i>+91 94920 54954</a>
          </div>
        </div>
      </div>
    </div>
  </section>

  <!-- LOCAL / CONTEXT -->
  <section class="section-padding bg-light">
    <div class="container lp-prose lp-narrow">
      <h2 class="fw-bold mb-3">{e(p["local_title"])}</h2>
{local}
    </div>
  </section>

  <!-- PROCESS + WHY -->
  <section class="section-padding">
    <div class="container">
      <h2 class="fw-bold mb-4 text-center">How We Work</h2>
      <ol class="lp-steps list-unstyled mb-5">
{process}
      </ol>
      <h2 class="fw-bold mb-4 text-center">Why Manzil Homes</h2>
      <div class="row g-3">
{why}
      </div>
    </div>
  </section>

  <!-- FAQ -->
  <section class="faq section-padding bg-light">
    <div class="container">
      <h2 class="fw-bold mb-4 text-center">Frequently Asked Questions</h2>
      <div class="faq-list mx-auto">
{faqs}
      </div>
    </div>
  </section>

  <!-- RELATED -->
  <section class="section-padding">
    <div class="container lp-narrow">
      <h2 class="h4 fw-bold mb-3">Related Services &amp; Areas</h2>
      <div class="lp-related-list">
{related}
      </div>
    </div>
  </section>

  <!-- CTA -->
  <section class="lp-cta text-center">
    <div class="container">
      <h2 class="fw-bold mb-2">Ready to start?</h2>
      <p class="mb-4">Visit our studio in Vishalakshi Nagar, Visakhapatnam (open all days, 9am to 7pm) or book a free consultation.</p>
      <a href="contact.html" class="btn btn-light rounded-pill px-4">Contact Us</a>
    </div>
  </section>

  <div id="footer"></div>

  <script>
    fetch('./components/navbar.html').then(r => r.text()).then(h => document.getElementById('navbar').innerHTML = h);
    fetch('./components/footer.html').then(r => r.text()).then(h => document.getElementById('footer').innerHTML = h);
  </script>
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
  <script src="./js/script.js"></script>
</body>

</html>
'''


def shell(*, slug, title, desc, img, img_alt, ld_graph, body, og_type="website"):
    url = f"{SITE}/{slug}.html"
    ld = json.dumps({"@context": "https://schema.org", "@graph": ld_graph}, ensure_ascii=False, indent=2)
    ld = "\n".join("  " + line for line in ld.splitlines())
    return f"""<!DOCTYPE html>
<html lang="en-IN">

<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <!-- Generated by tools/build_pages.py from tools/guides_data.py. Edit the data file, not this page. -->
  <title>{e(title)}</title>
  <meta name="description" content="{e(desc)}" />
  <meta name="robots" content="index, follow, max-image-preview:large" />
  <meta name="author" content="Manzil Homes" />
  <meta name="theme-color" content="#0f1335" />
  <link rel="canonical" href="{url}" />

  <meta property="og:type" content="{og_type}" />
  <meta property="og:site_name" content="Manzil Homes" />
  <meta property="og:locale" content="en_IN" />
  <meta property="og:title" content="{e(title)}" />
  <meta property="og:description" content="{e(desc)}" />
  <meta property="og:url" content="{url}" />
  <meta property="og:image" content="{SITE}/{img}" />
  <meta property="og:image:alt" content="{e(img_alt)}" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{e(title)}" />
  <meta name="twitter:description" content="{e(desc)}" />
  <meta name="twitter:image" content="{SITE}/{img}" />

  <script type="application/ld+json">
{ld}
  </script>

  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Marcellus&family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" />
  <link rel="stylesheet" href="./css/style.css" />
  <link rel="icon" href="./pngs/SecondaryLogoBlack.png" type="image/png" />
  <link rel="apple-touch-icon" href="./pngs/logowithcircle.png" />
</head>

<body>
  <div id="navbar"></div>
{body}
  <div id="footer"></div>

  <script>
    fetch('./components/navbar.html').then(r => r.text()).then(h => document.getElementById('navbar').innerHTML = h);
    fetch('./components/footer.html').then(r => r.text()).then(h => document.getElementById('footer').innerHTML = h);
  </script>
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
  <script src="./js/script.js"></script>
</body>

</html>
"""


def hero(h1, lead, img, cta=True):
    btn = '\n      <a href="contact.html" class="btn btn-light rounded-pill px-4">Book a Free Consultation</a>' if cta else ""
    return f"""
  <header class="hero-section lp-hero lp-hero-sm d-flex align-items-center text-center" style="background-image:url('{img}')">
    <div class="overlay"></div>
    <div class="hero-content container">
      <h1 class="mb-3">{e(h1)}</h1>
      <p class="mb-4 lp-lead">{e(lead)}</p>{btn}
    </div>
  </header>"""


def crumbs_html(items):
    return " <span aria-hidden=\"true\">/</span> ".join(
        f'<a href="{u}">{e(n)}</a>' if u else f'<span aria-current="page">{e(n)}</span>' for n, u in items)


def faq_block(faqs, heading="Frequently Asked Questions"):
    items = "\n".join(f'        <details class="faq-item">\n          <summary>{e(q)}</summary>\n          <p>{e(a)}</p>\n        </details>' for q, a in faqs)
    return f"""
  <section class="faq section-padding bg-light">
    <div class="container">
      <h2 class="fw-bold mb-4 text-center">{e(heading)}</h2>
      <div class="faq-list mx-auto">
{items}
      </div>
    </div>
  </section>"""


def render_blocks(blocks):
    out = []
    for kind, val in blocks:
        if kind == "h2":
            out.append(f"        <h2>{e(val)}</h2>")
        elif kind == "p":
            out.append(f"        <p>{e(val)}</p>")
        elif kind in ("ul", "ol"):
            out.append(f"        <{kind}>\n" + "\n".join(f"          <li>{e(i)}</li>" for i in val) + f"\n        </{kind}>")
        elif kind == "tip":
            out.append(f'        <aside class="guide-tip"><i class="bi bi-lightbulb" aria-hidden="true"></i><p>{e(val)}</p></aside>')
        else:
            raise ValueError(kind)
    return "\n".join(out)


def guide_html(g, biz):
    url = f"{SITE}/{g['slug']}.html"
    img = f"images/pages/{g['img']}.jpg"
    graph = [
        biz,
        {"@type": "BlogPosting", "@id": url + "#article", "headline": g["h1"], "description": g["desc"],
         "image": f"{SITE}/{img}", "datePublished": g.get("published", PUBLISHED), "dateModified": g.get("modified", g.get("published", PUBLISHED)),
         "inLanguage": "en-IN", "mainEntityOfPage": url,
         "author": {"@type": "Organization", "name": "Manzil Homes Design Team", "url": SITE + "/about.html"},
         "publisher": {"@id": SITE + "/#business"}},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Guides", "item": SITE + "/guides.html"},
            {"@type": "ListItem", "position": 3, "name": g["h1"], "item": url}]},
        {"@type": "FAQPage", "@id": url + "#faq", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in g["faqs"]]},
    ]
    related = "\n".join(
        f'        <a class="lp-related" href="{r}.html"><span>{e(ALL_SLUG[r]["h1"])}</span><i class="bi bi-arrow-right" aria-hidden="true"></i></a>'
        for r in g["related"])
    body = f"""{hero(g["h1"], g["lead"], img, cta=False)}

  <nav class="lp-crumbs container small" aria-label="Breadcrumb">
    {crumbs_html([("Home", "index.html"), ("Guides", "guides.html"), (g["h1"], None)])}
  </nav>

  <article class="section-padding pt-4">
    <div class="container guide-body">
      <p class="guide-meta small text-muted">By the Manzil Homes design team · Visakhapatnam</p>
{render_blocks(g["body"])}
    </div>
  </article>
{faq_block(g["faqs"])}

  <section class="section-padding">
    <div class="container lp-narrow">
      <h2 class="h4 fw-bold mb-3">Keep Reading</h2>
      <div class="lp-related-list">
{related}
        <a class="lp-related" href="guides.html"><span>All guides</span><i class="bi bi-arrow-right" aria-hidden="true"></i></a>
      </div>
    </div>
  </section>

  <section class="lp-cta text-center">
    <div class="container">
      <h2 class="fw-bold mb-2">Have a question about your home?</h2>
      <p class="mb-4">Talk to our team at the Vishalakshi Nagar studio, Visakhapatnam (open all days, 9am to 7pm). The first consultation is free.</p>
      <a href="contact.html" class="btn btn-light rounded-pill px-4">Book a Free Consultation</a>
    </div>
  </section>
"""
    return shell(slug=g["slug"], title=g["title"], desc=g["desc"], img=img, img_alt=g["img_alt"], ld_graph=graph, body=body, og_type="article")


def guides_index_html(biz):
    url = SITE + "/guides.html"
    cards = "\n".join(f"""        <div class="col-md-6 col-lg-4">
          <a class="guide-card h-100" href="{g['slug']}.html">
            <img src="images/pages/{g['img']}.jpg" alt="{e(g['img_alt'])}" loading="lazy" />
            <div class="p-3">
              <h2 class="h5 fw-bold mb-2">{e(g['h1'])}</h2>
              <p class="small text-muted mb-0">{e(g['lead'])}</p>
            </div>
          </a>
        </div>""" for g in GUIDES)
    graph = [biz,
             {"@type": "CollectionPage", "@id": url + "#webpage", "url": url, "name": "Interior Design & Construction Guides | Manzil Homes",
              "about": {"@id": SITE + "/#business"}, "inLanguage": "en-IN",
              "mainEntity": {"@type": "ItemList", "itemListElement": [
                  {"@type": "ListItem", "position": i, "url": f"{SITE}/{g['slug']}.html", "name": g["h1"]} for i, g in enumerate(GUIDES, 1)]}},
             {"@type": "BreadcrumbList", "itemListElement": [
                 {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
                 {"@type": "ListItem", "position": 2, "name": "Guides", "item": url}]}]
    body = f"""{hero("Interior Design & Construction Guides", "Straight answers to the questions homeowners in Vizag, Hyderabad and across Andhra Pradesh and Telangana ask us most.", "images/pages/g-faq.jpg", cta=False)}

  <nav class="lp-crumbs container small" aria-label="Breadcrumb">
    {crumbs_html([("Home", "index.html"), ("Guides", None)])}
  </nav>

  <section class="section-padding pt-4">
    <div class="container">
      <div class="row g-4">
{cards}
      </div>
      <p class="text-center mt-5 mb-0"><a href="faq.html" class="btn btn-outline-dark rounded-pill px-4">Browse all FAQs</a></p>
    </div>
  </section>
"""
    return shell(slug="guides", title="Interior Design & Construction Guides | Vizag & Hyderabad | Manzil Homes",
                 desc="Practical guides on interior design and home construction: choosing a designer in Vizag, cost factors, Vastu tips, coastal materials, modular kitchens, lighting, timelines and more.",
                 img="images/pages/g-faq.jpg", img_alt="Elegant dining room with chandelier", ld_graph=graph, body=body)


def faq_hub_html(biz):
    url = SITE + "/faq.html"
    allq = [qa for _, qs in FAQ_HUB for qa in qs]
    sections = "\n".join(f"""
  <section class="faq section-padding{' bg-light' if i % 2 else ''}">
    <div class="container">
      <h2 class="fw-bold mb-4 text-center">{e(name)}</h2>
      <div class="faq-list mx-auto">
""" + "\n".join(f'        <details class="faq-item">\n          <summary>{e(q)}</summary>\n          <p>{e(a)}</p>\n        </details>' for q, a in qs) + """
      </div>
    </div>
  </section>""" for i, (name, qs) in enumerate(FAQ_HUB))
    graph = [biz,
             {"@type": "FAQPage", "@id": url + "#faq", "url": url, "inLanguage": "en-IN", "mainEntity": [
                 {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in allq]},
             {"@type": "BreadcrumbList", "itemListElement": [
                 {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
                 {"@type": "ListItem", "position": 2, "name": "FAQs", "item": url}]}]
    body = f"""{hero("Frequently Asked Questions", "Everything you've wanted to ask about Manzil Homes, our services, design, cost and timelines.", "images/pages/g-questions.jpg", cta=False)}

  <nav class="lp-crumbs container small" aria-label="Breadcrumb">
    {crumbs_html([("Home", "index.html"), ("FAQs", None)])}
  </nav>
{sections}

  <section class="lp-cta text-center">
    <div class="container">
      <h2 class="fw-bold mb-2">Still have a question?</h2>
      <p class="mb-4">Call or WhatsApp +91 94920 54954, or read our detailed guides.</p>
      <a href="guides.html" class="btn btn-light rounded-pill px-4">Read the Guides</a>
    </div>
  </section>
"""
    return shell(slug="faq", title="Interior Design & Construction FAQs | Manzil Homes, Visakhapatnam",
                 desc="Answers to common questions about Manzil Homes: services, areas served, Vastu, 3D design, cost factors, free consultation, timelines and after-care.",
                 img="images/pages/g-questions.jpg", img_alt="Table with white flowers", ld_graph=graph, body=body)


def replace_block(path, start, end, body):
    s = open(path, encoding="utf-8").read()
    pat = re.compile(re.escape(start) + r".*?" + re.escape(end), re.S)
    if not pat.search(s):
        raise SystemExit(f"Markers {start} / {end} not found in {path}")
    open(path, "w", encoding="utf-8").write(pat.sub(lambda m: f"{start}\n{body}\n{end}", s))


def main():
    biz = business_node()
    for p in PAGES:
        for r in p["related"]:
            assert r in ALL_SLUG, f"{p['slug']}: unknown related page {r}"
        assert os.path.exists(os.path.join(ROOT, "images/pages", p["img"] + ".jpg")), p["img"]
        open(os.path.join(ROOT, p["slug"] + ".html"), "w", encoding="utf-8").write(page_html(p, biz))

    for g in GUIDES:
        for r in g["related"]:
            assert r in ALL_SLUG, f"{g['slug']}: unknown related page {r}"
        assert os.path.exists(os.path.join(ROOT, "images/pages", g["img"] + ".jpg")), g["img"]
        open(os.path.join(ROOT, g["slug"] + ".html"), "w", encoding="utf-8").write(guide_html(g, biz))
    open(os.path.join(ROOT, "guides.html"), "w", encoding="utf-8").write(guides_index_html(biz))
    open(os.path.join(ROOT, "faq.html"), "w", encoding="utf-8").write(faq_hub_html(biz))

    # sitemap
    rows = [f"  <url><loc>{SITE}{u}</loc><lastmod>{TODAY}</lastmod><changefreq>{f}</changefreq><priority>{pr}</priority></url>"
            for u, pr, f in CORE]
    rows += [f"  <url><loc>{SITE}/{p['slug']}.html</loc><lastmod>{TODAY}</lastmod><changefreq>monthly</changefreq>"
             f"<priority>{'0.8' if p['kind'] != LOCALITY else '0.7'}</priority></url>" for p in PAGES]
    rows += [f"  <url><loc>{SITE}/{u}.html</loc><lastmod>{TODAY}</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>"
             for u in ["guides", "faq"] + [g["slug"] for g in GUIDES]]
    open(os.path.join(ROOT, "sitemap.xml"), "w").write(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(rows) + "\n</urlset>\n")

    # footer link block
    def links(kind):
        return "\n".join(f'            <li><a href="{p["slug"]}.html" class="footer-link">{e(p["nav"])}</a></li>'
                         for p in PAGES if p["kind"] == kind)
    guide_links = "\n".join(f'            <li><a href="{g["slug"]}.html" class="footer-link">{e(g["h1"])}</a></li>' for g in GUIDES[:6])
    footer = f'''    <div class="row gy-3 footer-seo">
      <div class="col-md-3">
        <h2 class="h6 fw-bold mb-2">Services</h2>
        <ul class="list-unstyled small mb-0">
{links(SERVICES)}
        </ul>
      </div>
      <div class="col-md-3">
        <h2 class="h6 fw-bold mb-2">Cities We Serve</h2>
        <ul class="list-unstyled small mb-0">
{links(CITY)}
        </ul>
      </div>
      <div class="col-md-3">
        <h2 class="h6 fw-bold mb-2">Popular Areas</h2>
        <ul class="list-unstyled small mb-0">
{links(LOCALITY)}
        </ul>
      </div>
      <div class="col-md-3">
        <h2 class="h6 fw-bold mb-2">Guides</h2>
        <ul class="list-unstyled small mb-0">
{guide_links}
            <li><a href="guides.html" class="footer-link">All guides</a></li>
            <li><a href="faq.html" class="footer-link">FAQs</a></li>
        </ul>
      </div>
    </div>'''
    replace_block(os.path.join(ROOT, "components/footer.html"), "<!-- SEO-LINKS:START -->", "<!-- SEO-LINKS:END -->", footer)

    # llms.txt page list
    llms = "\n".join(f"- [{p['h1']}]({SITE}/{p['slug']}.html): {p['lead']}" for p in PAGES)
    llms += "\n\n## Guides and FAQs\n" + f"- [All guides]({SITE}/guides.html)\n- [FAQs]({SITE}/faq.html)\n" + "\n".join(
        f"- [{g['h1']}]({SITE}/{g['slug']}.html): {g['lead']}" for g in GUIDES)
    replace_block(os.path.join(ROOT, "llms.txt"), "<!-- SEO-PAGES:START -->", "<!-- SEO-PAGES:END -->", llms)
    print(f"Built {len(PAGES)} landing pages, {len(GUIDES)} guides, guides.html, faq.html; sitemap has {len(rows)} URLs.")


if __name__ == "__main__":
    main()
