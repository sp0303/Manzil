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

SITE = "https://manzils.in"
TODAY = datetime.date.today().isoformat()
CORE = [("/", "1.0", "weekly"), ("/services.html", "0.9", "monthly"), ("/projects.html", "0.8", "monthly"),
        ("/about.html", "0.8", "monthly"), ("/studio.html", "0.7", "monthly"), ("/contact.html", "0.8", "yearly")]
BY_SLUG = {p["slug"]: p for p in PAGES}
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
        f'        <a class="lp-related" href="{r}.html"><span>{e(BY_SLUG[r]["h1"])}</span><i class="bi bi-arrow-right" aria-hidden="true"></i></a>'
        for r in p["related"] if r in BY_SLUG)
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
            assert r in BY_SLUG, f"{p['slug']}: unknown related page {r}"
        assert os.path.exists(os.path.join(ROOT, "images/pages", p["img"] + ".jpg")), p["img"]
        open(os.path.join(ROOT, p["slug"] + ".html"), "w", encoding="utf-8").write(page_html(p, biz))

    # sitemap
    rows = [f"  <url><loc>{SITE}{u}</loc><lastmod>{TODAY}</lastmod><changefreq>{f}</changefreq><priority>{pr}</priority></url>"
            for u, pr, f in CORE]
    rows += [f"  <url><loc>{SITE}/{p['slug']}.html</loc><lastmod>{TODAY}</lastmod><changefreq>monthly</changefreq>"
             f"<priority>{'0.8' if p['kind'] != LOCALITY else '0.7'}</priority></url>" for p in PAGES]
    open(os.path.join(ROOT, "sitemap.xml"), "w").write(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(rows) + "\n</urlset>\n")

    # footer link block
    def links(kind):
        return "\n".join(f'            <li><a href="{p["slug"]}.html" class="footer-link">{e(p["nav"])}</a></li>'
                         for p in PAGES if p["kind"] == kind)
    footer = f'''    <div class="row gy-3 footer-seo">
      <div class="col-md-4">
        <h2 class="h6 fw-bold mb-2">Services</h2>
        <ul class="list-unstyled small mb-0">
{links(SERVICES)}
        </ul>
      </div>
      <div class="col-md-4">
        <h2 class="h6 fw-bold mb-2">Cities We Serve</h2>
        <ul class="list-unstyled small mb-0">
{links(CITY)}
        </ul>
      </div>
      <div class="col-md-4">
        <h2 class="h6 fw-bold mb-2">Popular Areas</h2>
        <ul class="list-unstyled small mb-0">
{links(LOCALITY)}
        </ul>
      </div>
    </div>'''
    replace_block(os.path.join(ROOT, "components/footer.html"), "<!-- SEO-LINKS:START -->", "<!-- SEO-LINKS:END -->", footer)

    # llms.txt page list
    llms = "\n".join(f"- [{p['h1']}]({SITE}/{p['slug']}.html): {p['lead']}" for p in PAGES)
    replace_block(os.path.join(ROOT, "llms.txt"), "<!-- SEO-PAGES:START -->", "<!-- SEO-PAGES:END -->", llms)
    print(f"Built {len(PAGES)} pages; sitemap has {len(rows)} URLs.")


if __name__ == "__main__":
    main()
