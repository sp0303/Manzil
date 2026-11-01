#!/usr/bin/env python3
"""Build the Design Gallery page (gallery.html) from tools/gallery_data.py.

Usage (from the repository root):
    python3 tools/build_gallery.py

It rewrites the block between the DESIGN-GALLERY markers in gallery.html
(grid, alt text and ImageGallery structured data) and adds <image:image>
entries to sitemap.xml. tools/build_pages.py also uses image_tags() so the
image sitemap survives a full rebuild.
"""
import html
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from gallery_data import BRAND, CATEGORIES, EXTRA_IMAGES, GALLERY  # noqa: E402

SITE = "https://manzils.in"
START, END = "<!-- DESIGN-GALLERY:START -->", "<!-- DESIGN-GALLERY:END -->"
IMAGE_NS = 'xmlns:image="http://www.google.com/schemas/sitemap-image/1.1"'


def alt(desc):
    return f"{desc} – {BRAND}"


def page_images(page):
    """(absolute url, caption) for every image listed in the sitemap for a page."""
    if page == "/gallery.html":
        return [(f"{SITE}/images/gallery/{f}", alt(d)) for f, _, d in GALLERY]
    return [(f"{SITE}/{p}", c) for p, c in EXTRA_IMAGES.get(page, [])]


def image_tags(page):
    return "".join(f"<image:image><image:loc>{html.escape(u)}</image:loc></image:image>"
                   for u, _ in page_images(page))


def ordered():
    """Spread categories through the grid so 'All' is not grouped by column."""
    seq = []
    for c, _ in CATEGORIES:
        items = [g for g in GALLERY if g[1] == c]
        seq += [((i + 0.5) / len(items), c, g) for i, g in enumerate(items)]
    return [g for _, _, g in sorted(seq, key=lambda t: (t[0], t[1]))]


def size(path):
    w, h = subprocess.check_output(["identify", "-format", "%w %h", path]).split()
    return int(w), int(h)


def gallery_html():
    e = html.escape
    count = {c: sum(1 for g in GALLERY if g[1] == c) for c, _ in CATEGORIES}
    out = [START,
           '<section class="design-gallery py-5" id="design-gallery">',
           '  <div class="container">',
           '    <div class="text-center">',
           '      <h2 class="fw-bold mb-3">Browse Our Interior Designs</h2>',
           '      <p class="text-muted mb-4 mx-auto" style="max-width:720px">',
           '        Explore our interior design concepts for bedrooms, living rooms, modular kitchens and wardrobes.',
           '        Tap any image to view it full size.',
           '      </p>',
           '      <div class="gallery-filters mb-4" role="group" aria-label="Filter gallery by room">',
           f'        <button type="button" class="gallery-filter active" data-filter="all" aria-pressed="true">All <span>{len(GALLERY)}</span></button>']
    for c, label in CATEGORIES:
        out.append(f'        <button type="button" class="gallery-filter" data-filter="{c}" aria-pressed="false">'
                   f'{e(label)} <span>{count[c]}</span></button>')
    out += ['      </div>', '    </div>', '    <div class="gallery-grid">']
    for f, c, d in ordered():
        w, h = size(os.path.join(ROOT, "images/gallery/thumbs", f))
        out.append(f'      <a class="gallery-item" href="images/gallery/{f}" data-category="{c}">'
                   f'<img src="images/gallery/thumbs/{f}" width="{w}" height="{h}" alt="{e(alt(d))}" '
                   f'loading="lazy" decoding="async"></a>')
    out += ['    </div>',
            '    <div class="text-center">',
            '      <a href="contact.html" class="btn btn-light rounded-pill mt-5 px-4">Get a Design Like This</a>',
            '    </div>',
            '  </div>',
            '</section>',
            '',
            '<!-- GALLERY LIGHTBOX -->',
            '<div class="gallery-lightbox" id="galleryLightbox" role="dialog" aria-modal="true" aria-label="Image viewer" hidden>',
            '  <button type="button" class="lb-close" aria-label="Close">&times;</button>',
            '  <button type="button" class="lb-prev" aria-label="Previous image">&#8249;</button>',
            '  <figure class="lb-figure">',
            '    <img src="" alt="">',
            '    <figcaption class="lb-caption"></figcaption>',
            '  </figure>',
            '  <button type="button" class="lb-next" aria-label="Next image">&#8250;</button>',
            '</div>',
            '',
            '<script type="application/ld+json">',
            json.dumps(structured_data(), indent=2, ensure_ascii=False).replace("</", "<\\/"),
            '</script>',
            END]
    return "\n".join(out)


def structured_data():
    labels = dict(CATEGORIES)
    return {
        "@context": "https://schema.org",
        "@type": "ImageGallery",
        "@id": f"{SITE}/gallery.html#design-gallery",
        "name": "Manzil Homes Interior Design Gallery",
        "description": "Interior design concepts for bedrooms, living rooms, modular kitchens and wardrobes "
                       "by Manzil Homes, Visakhapatnam and Hyderabad.",
        "url": f"{SITE}/gallery.html#design-gallery",
        "publisher": {"@id": f"{SITE}/#business"},
        "associatedMedia": [{
            "@type": "ImageObject",
            "contentUrl": f"{SITE}/images/gallery/{f}",
            "thumbnailUrl": f"{SITE}/images/gallery/thumbs/{f}",
            "name": d,
            "caption": alt(d),
            "description": alt(d),
            "keywords": labels[c],
            "width": size(os.path.join(ROOT, "images/gallery", f))[0],
            "height": size(os.path.join(ROOT, "images/gallery", f))[1],
        } for f, c, d in GALLERY],
    }


def patch_sitemap():
    p = os.path.join(ROOT, "sitemap.xml")
    s = open(p, encoding="utf-8").read()
    if IMAGE_NS not in s:
        s = s.replace('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
                      f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" {IMAGE_NS}>')
    s = re.sub(r"(<url><loc>[^<]*</loc>.*?</priority>)(?:<image:image>.*?</image:image>)+(</url>)", r"\1\2", s)
    for page in ["/gallery.html"] + list(EXTRA_IMAGES):
        loc = f"<loc>{SITE}{page}</loc>"
        s = re.sub(r"(<url>" + re.escape(loc) + r".*?</priority>)(?:<image:image>.*?</image:image>)*(</url>)",
                   lambda m: m.group(1) + image_tags(page) + m.group(2), s)
    open(p, "w", encoding="utf-8").write(s)


def main():
    p = os.path.join(ROOT, "gallery.html")
    s = open(p, encoding="utf-8").read()
    i, j = s.index(START), s.index(END) + len(END)
    open(p, "w", encoding="utf-8").write(s[:i] + gallery_html() + s[j:])
    patch_sitemap()
    print(f"Gallery: {len(GALLERY)} images; sitemap image entries updated.")


if __name__ == "__main__":
    main()
