#!/usr/bin/env python3
"""
Static build for edmdfw.com (no API calls; safe to run any time).

Reads events.js (the data the homepage loads) and writes search-engine
landing pages whose listings are pre-built into the HTML -- artist names,
venues, dates and cities are in the page source, plus schema.org Event data:
  * dallas-edm-shows/  -- the full calendar ("dallas edm shows"); the old
                         dallas-edm-events/ address forwards to it
  * dallas-edm-concerts/ -- "dallas edm concerts": concert halls, arenas, festivals
  * this-weekend/       -- "edm events this weekend dallas"
  * genres/<genre>/     -- "dfw house music", "dallas techno", ...
  * venues/<venue>/     -- "silo dallas events", ...
  * sitemap.xml and robots.txt.

On the homepage (index.html) only the <head> block between <!--seo:head-->
markers is rewritten (search title, description, link-preview tags and
schema.org Event data); nothing the page displays or runs is touched. The
landing pages reuse its CSS so they match the site. The card / day-group markup below mirrors
cardHTML(), weeklyHTML() and render() in index.html.

Run:  python3 build_site.py
"""

import html
import json
import os
import re
import subprocess
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = "https://edmdfw.com"
TZ = ZoneInfo("America/Chicago")
INSTAGRAM = "https://www.instagram.com/dfw.edm/"

GENRE_COLORS = {
    "Bass": "#FB923C", "Downtempo": "#CBD5E1", "Drum & Bass": "#A3E635",
    "Dubstep": "#A78BFA", "Hard Dance": "#E879F9", "House": "#F5A524",
    "Techno": "#4C8DFF", "Trance": "#22D3EE", "Trap": "#F87171",
    "UK Bass / Garage": "#2DD4BF",
}
WEEKDAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
LATE_NIGHT_CUTOFF_HOUR = 6  # same rule as update_events.py: 1 AM Saturday is Friday night


# ---------------------------------------------------------------- data

def load_data():
    """Evaluate events.js with Node (it builds resale links with a JS helper)."""
    script = (
        "const fs=require('fs');eval(fs.readFileSync(process.argv[1],'utf8')+"
        "';process.stdout.write(JSON.stringify({LAST_UPDATED,VENUES,EVENTS,"
        "CLOSED_VENUES_NOTE:typeof CLOSED_VENUES_NOTE!==\"undefined\"?CLOSED_VENUES_NOTE:\"\"}))')"
    )
    out = subprocess.run(["node", "-e", script, os.path.join(ROOT, "events.js")],
                         check=True, capture_output=True, text=True).stdout
    return json.loads(out)


def now_ct():
    return datetime.now(TZ)


def today_str():
    # Same as the page: "today" runs until 12:30 AM so tonight's shows stay up.
    return (now_ct() - timedelta(minutes=30)).date().isoformat()


def parse_date(d):
    return date.fromisoformat(d)


def add_days(d, n):
    return (parse_date(d) + timedelta(days=n)).isoformat()


def weekend_range(today):
    dow = (parse_date(today).weekday() + 1) % 7  # 0 = Sunday, like JS getDay()
    if dow == 0:
        return today, today
    fri = today if dow >= 5 else add_days(today, 5 - dow)
    return fri, add_days(today, 7 - dow)


def is_weekly(e):
    return any(re.search(d, e.get("recurring") or "", re.I) for d in WEEKDAYS)


def upcoming(events, today):
    return sorted((e for e in events if e.get("date") and e["date"] >= today), key=lambda e: e["date"])


def slugify(s):
    s = s.lower().replace("&", " and ").replace("'", "")
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


# ---------------------------------------------------------------- markup (mirrors index.html)

def esc(s):
    return html.escape("" if s is None else str(s), quote=True).replace("&#x27;", "&#39;")


def short_time(t):
    if not t:
        return ""
    s = re.sub(r"\s*-\s*", "–", t.replace(":00", ""))
    m = re.match(r"^(\d+(?::\d+)?)\s*(AM|PM)–(\d+(?::\d+)?)\s*(AM|PM)$", s, re.I)
    if m and m.group(2).upper() == m.group(4).upper():
        return f"{m.group(1)}–{m.group(3)} {m.group(4).upper()}"
    return s


def split_title(artist):
    m = re.match(r"^(.+?)\s+(?:ft\.?|feat\.?|w/)\s+(.+)$", artist, re.I) or re.match(r"^(.+?)\s+\|\s+(.+)$", artist)
    return (m.group(1), m.group(2)) if m else (artist, "")


def venue_name(e, venues):
    v = venues.get(e["venue"])
    return v["name"] if v else e["venue"]


def asset(url, base):
    """Repo-relative assets (img/..., logo.png) need a prefix on sub-pages."""
    return url if not url or re.match(r"^(https?:)?//", url) else base + url


def img_tag(e, venues, base=""):
    venue_image = (venues.get(e["venue"]) or {}).get("image")
    chain = []
    for u in (e.get("image"), venue_image):
        if u and u not in chain:
            chain.append(u)
    if not chain:
        return ""
    chain = [asset(u, base) for u in chain]
    style = f' style="object-position:{esc(e["focus"])}"' if e.get("focus") and e.get("image") else ""
    return (f'<img src="{esc(chain[0])}" alt="" loading="lazy"{style}'
            f' data-fallbacks="{esc("|".join(chain[1:]))}" onerror="imgFallback(this)">')


def genre_pill(g):
    c = GENRE_COLORS.get(g)
    return f'<span class="pill" style="--c:{c}">{esc(g)}</span>' if c else ""


def card_html(e, venues, base=""):
    title, lineup = split_title(e["artist"])
    meta = " &middot; ".join(esc(x) for x in (short_time(e.get("time")), venue_name(e, venues), e.get("price")) if x)
    if e.get("free"):
        actions = (f'<a class="info-link" href="{esc(e["direct"])}" target="_blank" rel="noopener"'
                   f' aria-label="Event info: {esc(e["artist"])}">Event info &rarr;</a>')
    else:
        resale = [] if (venues.get(e["venue"]) or {}).get("noResale") else (e.get("resale") or [])
        links = " &middot; ".join(
            f'<a href="{esc(r["url"])}" target="_blank" rel="noopener"'
            f' aria-label="{esc(r["site"])} resale tickets: {esc(e["artist"])}">{esc(r["site"])}</a>' for r in resale)
        actions = (f'<a class="btn-tickets" href="{esc(e["direct"])}" target="_blank" rel="noopener"'
                   f' aria-label="Tickets: {esc(e["artist"])}">Tickets</a>'
                   + (f'<span class="resale">{links}</span>' if links else ""))
    free_pill = '<span class="pill free">FREE</span>' if e.get("free") else ""
    return (
        '<article class="ev">'
        f'<div class="thumb">{img_tag(e, venues, base)}</div>'
        '<div class="ev-body">'
        f'<div class="tags">{genre_pill(e.get("genre"))}{free_pill}</div>'
        f'<div class="ev-title">{esc(title)}</div>'
        + (f'<div class="lineup">{esc(lineup)}</div>' if lineup else "")
        + f'<div class="meta">{meta}</div>'
        + promo_html(e, venues)
        + f'<div class="actions">{actions}</div>'
        '</div>'
        '</article>'
    )


def promo_html(e, venues):
    """Our promoter discount code for the venue, on ticketed (not free) shows."""
    code = None if e.get("free") else (venues.get(e["venue"]) or {}).get("promo")
    return (f'<div class="promo">Discount code <button type="button" class="promo-code" data-code="{esc(code)}"'
            f' aria-label="Copy discount code {esc(code)}">{esc(code)}</button></div>') if code else ""


def weekly_days(e):
    days = [d for d in WEEKDAYS if re.search(d, e.get("recurring") or "", re.I)]
    return " & ".join(d.upper() + "S" for d in days) if days else (e.get("recurring") or "").upper()


def weekly_html(e, venues, base=""):
    when = esc(weekly_days(e)) + (" &middot; " + esc(short_time(e["time"])) if e.get("time") else "")
    return (
        '<article class="ev wk">'
        f'<div class="thumb square">{img_tag(e, venues, base)}</div>'
        '<div class="ev-body">'
        f'<div class="tags">{genre_pill(e.get("genre"))}</div>'
        f'<div class="ev-title fit">{esc(e["artist"])}</div>'
        f'<div class="wk-when fit">{when}</div>'
        f'<div class="meta fit">{esc(venue_name(e, venues))}</div>'
        f'<div class="actions"><a class="btn-tickets" href="{esc(e["direct"])}" target="_blank" rel="noopener"'
        f' aria-label="Event info: {esc(e["artist"])}">Event Info</a></div>'
        '</div>'
        '</article>'
    )


def month_range(first, last):
    out, y, m = [], int(first[:4]), int(first[5:7])
    while True:
        ym = f"{y}-{m:02d}"
        out.append(ym)
        if ym >= last:
            return out
        m += 1
        if m > 12:
            m, y = 1, y + 1


def month_long(ym):
    return date(int(ym[:4]), int(ym[5:7]), 1).strftime("%B %Y")


def day_label(d):
    dt = parse_date(d)
    return f"{dt:%a}, {dt:%b} {dt.day}"


def list_html(dated, venues, today, base="", fill_months=True):
    """Month sections with day groups -- render() in index.html."""
    tomorrow = add_days(today, 1)
    by_day = {}
    for e in dated:
        by_day.setdefault(e["date"], []).append(e)
    if not dated:
        return '<p class="no-results">No shows match these filters.</p>'
    if fill_months:
        months = month_range(dated[0]["date"][:7], dated[-1]["date"][:7])
    else:
        months = list(dict.fromkeys(e["date"][:7] for e in dated))
    out = []
    for ym in months:
        out.append(f'<h2 class="month-head">{esc(month_long(ym))}</h2>')
        days = sorted(d for d in by_day if d[:7] == ym)
        if not days:
            out.append('<p class="empty">No events announced yet.</p>')
            continue
        for d in days:
            n = len(by_day[d])
            soon = "TONIGHT" if d == today else "TOMORROW" if d == tomorrow else ""
            soon_html = f'<span class="soon">{soon}</span> &middot; ' if soon else ""
            out.append(
                f'<div class="day-head"><h3>{esc(day_label(d))}</h3>'
                f'<span class="day-count">{soon_html}'
                f'{n}{" SHOW" if n == 1 else " SHOWS"}</span></div>'
                f'<div class="cards">{"".join(card_html(e, venues, base) for e in by_day[d])}</div>'
            )
    return "".join(out)


# ---------------------------------------------------------------- structured data

def start_iso(e):
    """ISO start with the Dallas UTC offset. After-midnight shows are filed
    under the night before, so their real start is the next calendar day."""
    m = re.search(r"(\d{1,2})(?::(\d{2}))?\s*([AP])\.?M", e.get("time") or "", re.I)
    d = parse_date(e["date"])
    if not m:
        return d.isoformat()
    hour = int(m.group(1)) % 12 + (12 if m.group(3).upper() == "P" else 0)
    if hour < LATE_NIGHT_CUTOFF_HOUR:
        d += timedelta(days=1)
    return datetime(d.year, d.month, d.day, hour, int(m.group(2) or 0), tzinfo=TZ).isoformat()


def postal_address(addr):
    parts = [p.strip() for p in (addr or "").split(",")]
    if len(parts) < 3:
        return None
    region = parts[2].split()
    a = {"@type": "PostalAddress", "streetAddress": parts[0], "addressLocality": parts[1],
         "addressRegion": region[0] if region else "TX", "addressCountry": "US"}
    if len(region) > 1:
        a["postalCode"] = region[1]
    return a


def event_ld(e, venues):
    v = venues.get(e["venue"]) or {}
    place = {"@type": "Place", "name": v.get("name", e["venue"])}
    address = postal_address(v.get("address"))
    if address:
        place["address"] = address
    item = {
        "@type": "MusicEvent",
        "name": e["artist"],
        "startDate": start_iso(e),
        "eventStatus": "https://schema.org/EventScheduled",
        "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
        "location": place,
        "url": e["direct"],
    }
    image = e.get("image") or v.get("image")
    if image:
        item["image"] = [image if image.startswith("http") else f"{SITE}/{image}"]
    if e.get("genre"):
        item["genre"] = e["genre"]
    if e.get("free"):
        item["isAccessibleForFree"] = True
    offer = {"@type": "Offer", "url": e["direct"]}
    price = re.search(r"\$\s*(\d+(?:\.\d+)?)", e.get("price") or "")
    if e.get("free"):
        offer.update(price="0", priceCurrency="USD")
    elif price:
        offer.update(price=price.group(1), priceCurrency="USD")
    item["offers"] = offer
    return item


def ld_json(obj):
    # "</" can't appear inside a <script> block.
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def head_tags(title, description, path, events, venues, extra_ld=None):
    url = SITE + path
    graph = [
        {"@type": "WebSite", "@id": SITE + "/#website", "url": SITE + "/", "name": "DFW EDM",
         "description": "Dallas-Fort Worth EDM, house, techno and bass events.",
         "publisher": {"@id": SITE + "/#org"}},
        {"@type": "Organization", "@id": SITE + "/#org", "name": "DFW EDM", "url": SITE + "/",
         "logo": SITE + "/logo.png", "sameAs": [INSTAGRAM]},
    ]
    if events:
        graph.append({"@type": "ItemList", "name": title, "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "item": event_ld(e, venues)} for i, e in enumerate(events)]})
    graph += extra_ld or []
    return (
        f"<title>{esc(title)}</title>\n"
        f'<meta name="description" content="{esc(description)}">\n'
        f'<link rel="canonical" href="{url}">\n'
        '<meta property="og:type" content="website">\n'
        '<meta property="og:site_name" content="DFW EDM">\n'
        f'<meta property="og:title" content="{esc(title)}">\n'
        f'<meta property="og:description" content="{esc(description)}">\n'
        f'<meta property="og:url" content="{url}">\n'
        f'<meta property="og:image" content="{SITE}/logo.png">\n'
        '<meta name="twitter:card" content="summary">\n'
        f'<meta name="twitter:title" content="{esc(title)}">\n'
        f'<meta name="twitter:description" content="{esc(description)}">\n'
        f'<script type="application/ld+json">{ld_json({"@context": "https://schema.org", "@graph": graph})}</script>'
    )


# ---------------------------------------------------------------- homepage <head>

HOME_TITLE = "Dallas EDM Shows, DFW House & Techno Events | DFW EDM"


def home_description(venues, dated):
    counts = {}
    for e in dated:
        counts[e["venue"]] = counts.get(e["venue"], 0) + 1
    top = [venues[k]["name"] for k, _ in sorted(counts.items(), key=lambda kv: -kv[1])[:4] if k in venues]
    return ("Upcoming EDM, house, techno, dubstep and bass shows in Dallas-Fort Worth: tonight, this weekend "
            f"and every month{' at ' + ', '.join(top) + ' and more' if top else ''}. Tickets and free events.")


def replace_block(page, name, content):
    pat = re.compile(rf"(<!--{re.escape(name)}-->).*?(<!--/{re.escape(name)}-->)", re.S)
    if not pat.search(page):
        raise SystemExit(f"index.html is missing the <!--{name}--> ... <!--/{name}--> markers")
    return pat.sub(lambda m: m.group(1) + content + m.group(2), page, count=1)


def build_home_head(page, data, today):
    """Only the homepage's <head> SEO block changes -- never its body."""
    dated = upcoming(data["EVENTS"], today)
    return replace_block(page, "seo:head", "\n" + head_tags(
        HOME_TITLE, home_description(data["VENUES"], dated), "/", dated, data["VENUES"]) + "\n")


# ---------------------------------------------------------------- landing pages

def site_css(page):
    return re.search(r"<style>(.*?)</style>", page, re.S).group(1)


LANDING_CSS = """
  .landing h1{font-weight:700;font-size:26px;line-height:1.15;margin:22px 0 6px;letter-spacing:-0.005em;}
  .landing .intro{color:var(--sub);margin:0 0 4px;font-size:15px;}
  .landing .addr{color:var(--tertiary);font-size:13.5px;margin:0;}
  .crumbs{font-size:13px;color:var(--tertiary);margin-top:16px;}
  .crumbs a{color:var(--pink);}
  .link-group{margin-top:30px;}
  .link-group h2{font-size:15px;font-weight:700;margin:0 0 8px;}
  .link-row{display:flex;flex-wrap:wrap;gap:8px;}
  .link-row a{display:inline-flex;align-items:center;height:34px;padding:0 13px;border-radius:999px;
    background:var(--field);border:1px solid var(--border);color:var(--sub);font-size:13.5px;font-weight:500;}
  .link-row a:hover{border-color:var(--pink);color:var(--text);}
  .link-row a[aria-current]{background:var(--pink);border-color:var(--pink);color:var(--on-pink);}
  .legal{max-width:680px;color:var(--sub);font-size:15px;}
  .legal h2{color:var(--text);font-size:17px;font-weight:700;margin:26px 0 6px;}
  .legal p,.legal li{margin:0 0 10px;}
  .legal ul{padding-left:20px;margin:0 0 10px;}
  .legal a{color:var(--pink);text-decoration:underline;text-underline-offset:2px;}
"""


CURRENT = ' aria-current="page"'


def landing_page(page, *, path, title, description, h1, intro, addr, events, venues, today,
                 nav, current_href, fill_months=True, empty_note="", weekly=(), article=""):
    base = "/"
    body_list = (list_html(events, venues, today, base, fill_months) if events
                 else f'<p class="no-results">{esc(empty_note)}</p>')
    weekly_block = (
        '<section class="weekly" aria-label="Every week"><h2 class="section-title">Every week</h2>'
        f'<div class="carousel">{"".join(weekly_html(e, venues, base) for e in weekly)}</div></section>'
        if weekly else "")
    groups = "".join(
        f'<nav class="link-group" aria-label="{esc(label)}"><h2>{esc(label)}</h2><div class="link-row">'
        + "".join(f'<a href="{href}"{CURRENT if href == current_href else ""}>{esc(text)}</a>'
                  for href, text in links)
        + "</div></nav>"
        for label, links in nav if links
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="theme-color" content="#0A0A10">
{head_tags(title, description, path, events, venues)}
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter+Tight:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>{site_css(page)}{LANDING_CSS}</style>
</head>
<body>
<header class="site-header">
  <div class="wrap">
    <a class="brand" href="/">
      <img src="/logo.png" alt="">
      <span class="brand-text">
        <span class="wordmark">DFW EDM</span>
        <span class="tagline">Your home for Dallas-Fort Worth electronic music.</span>
      </span>
    </a>
    <a class="ig-link" href="{INSTAGRAM}" target="_blank" rel="noopener" aria-label="DFW EDM on Instagram (@dfw.edm)" title="@dfw.edm on Instagram">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r="1" fill="currentColor" stroke="none"/></svg>
    </a>
  </div>
</header>
<main class="wrap landing">
  <p class="crumbs"><a href="/">All DFW events</a></p>
  <h1>{esc(h1)}</h1>
  {f'<p class="intro">{esc(intro)}</p>' if intro else ""}
  {f'<p class="addr">{esc(addr)}</p>' if addr else ""}
  {article or weekly_block + f'<section aria-label="Upcoming shows">{body_list}</section>'}
  {groups}
</main>
<footer class="wrap">
  <p class="fine">Refreshed every few days &middot; <a href="/">See every Dallas-Fort Worth EDM event</a></p>
  <p class="fine legal-links">Not affiliated with any venue, promoter, artist or ticket seller. Some ticket links and discount codes may earn us a commission. &middot; <a href="/privacy/">Privacy</a> &middot; <a href="/terms/">Terms</a></p>
</footer>
<script>
// Tap a discount code to copy it.
document.addEventListener("click", function(ev){{
  var btn = ev.target.closest && ev.target.closest(".promo-code");
  if(!btn || !navigator.clipboard) return;
  navigator.clipboard.writeText(btn.getAttribute("data-code")).then(function(){{
    btn.textContent = "Copied!";
    setTimeout(function(){{ btn.textContent = btn.getAttribute("data-code"); }}, 1500);
  }});
}});
function imgFallback(img){{
  var rest = (img.getAttribute("data-fallbacks") || "").split("|").filter(Boolean);
  if(!rest.length){{ img.onerror = null; img.style.visibility = "hidden"; return; }}
  img.style.objectPosition = "";
  img.setAttribute("data-fallbacks", rest.slice(1).join("|"));
  img.src = rest[0];
}}
// Keep each weekly-card detail on one line (same as the homepage).
document.querySelectorAll(".fit").forEach(function(el){{
  var size = parseFloat(getComputedStyle(el).fontSize);
  while(el.scrollWidth > el.clientWidth + 0.5 && size > 10){{ size -= 0.5; el.style.fontSize = size + "px"; }}
}});
</script>
</body>
</html>
"""


def write(rel, content):
    path = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def build_landing_pages(page, data, today):
    venues, events = data["VENUES"], data["EVENTS"]
    dated = upcoming(events, today)
    genres = [g for g in GENRE_COLORS if any(e.get("genre") == g for e in dated)]
    weekly_all = [e for e in events if not e.get("date") and is_weekly(e)]
    venue_counts = {}
    for e in dated + weekly_all:
        venue_counts[e["venue"]] = venue_counts.get(e["venue"], 0) + 1
    venue_keys = sorted((k for k in venue_counts if k in venues and not venues[k].get("closed")),
                        key=lambda k: (-venue_counts[k], venues[k]["name"]))
    nav = [
        ("Calendar", [("/dallas-edm-shows/", "All Dallas EDM shows"), ("/dallas-edm-concerts/", "Dallas EDM concerts"), ("/this-weekend/", "EDM events this weekend")]),
        ("Genres", [(f"/genres/{slugify(g)}/", f"DFW {g}") for g in genres]),
        ("Venues", [(f"/venues/{slugify(venues[k]['name'])}/", venues[k]["name"]) for k in venue_keys]),
    ]
    pages = []

    # Full calendar
    counts = {}
    for e in dated:
        counts[e["venue"]] = counts.get(e["venue"], 0) + 1
    top = [venues[k]["name"] for k, _ in sorted(counts.items(), key=lambda kv: -kv[1])[:4] if k in venues]
    months = list(dict.fromkeys(e["date"][:7] for e in dated))
    period = f"{month_long(months[0])} – {month_long(months[-1])}" if len(months) > 1 else (month_long(months[0]) if months else "")
    pages.append(("dallas-edm-shows/index.html", landing_page(
        page, path="/dallas-edm-shows/",
        title="Dallas EDM Shows & Events – DFW House, Techno & Bass Calendar | DFW EDM",
        description=(f"{len(dated)} upcoming EDM, house, techno, dubstep and bass shows in Dallas-Fort Worth"
                     f"{' at ' + ', '.join(top) + ' and more' if top else ''}, by date with tickets and free events."),
        h1="Dallas EDM shows",
        intro=(f"{len(dated)} upcoming electronic shows across {len(counts)} venues"
               f"{', ' + period if period else ''}, plus {len(weekly_all)} weekly nights."),
        addr="", events=dated, venues=venues, today=today, nav=nav, current_href="/dallas-edm-shows/",
        weekly=weekly_all, empty_note="No upcoming shows are listed right now.")))

    # Concerts: the bigger ticketed shows (concert halls, arenas, pavilions,
    # festivals), not club and after-hours nights -- its own list, so it isn't
    # a copy of the full calendar.
    concerts = [e for e in dated if e["venue"] in CONCERT_VENUES]
    years = sorted({e["date"][:4] for e in concerts}) or [today[:4]]
    c_years = years[0] if len(years) == 1 else f"{years[0]}–{years[-1]}"
    c_venues = list(dict.fromkeys(venues[e["venue"]]["name"] for e in concerts if e["venue"] in venues))
    pages.append(("dallas-edm-concerts/index.html", landing_page(
        page, path="/dallas-edm-concerts/",
        title=f"Dallas EDM Concerts {c_years} – Upcoming Electronic Music Concerts in DFW | DFW EDM",
        description=(f"{len(concerts)} upcoming EDM concerts in Dallas-Fort Worth at "
                     f"{', '.join(c_venues[:4]) or 'SILO, Dickies Arena and more'}: headline DJ tours, "
                     "arena shows and festivals, with dates and tickets."),
        h1="Dallas EDM concerts",
        intro=(f"{len(concerts)} headline electronic concerts at DFW's concert halls, arenas and festivals. "
               "For club nights and after-hours too, see all Dallas EDM shows."),
        addr="", events=concerts, venues=venues, today=today, nav=nav, current_href="/dallas-edm-concerts/",
        empty_note="No concerts are listed right now. See every upcoming show below.")))

    # Privacy policy and terms (linked from every page's footer)
    for slug, title, h1, desc, body in (
        ("privacy", "Privacy Policy | DFW EDM", "Privacy policy",
         "DFW EDM collects no personal information: no accounts, forms, ads, analytics or cookies.", PRIVACY_HTML),
        ("terms", "Terms of Use | DFW EDM", "Terms of use",
         "Terms for using edmdfw.com: listings are informational, tickets are sold by third parties, "
         "no affiliation with venues, and affiliate link disclosure.", TERMS_HTML),
    ):
        pages.append((f"{slug}/index.html", landing_page(
            page, path=f"/{slug}/", title=title, description=desc, h1=h1, intro="", addr="",
            events=[], venues=venues, today=today, nav=nav, current_href=None, article=body)))

    # This weekend
    fri, sun = weekend_range(today)
    wknd = [e for e in dated if fri <= e["date"] <= sun]
    span = f"{day_label(fri)} – {day_label(sun)}" if fri != sun else day_label(fri)
    pages.append(("this-weekend/index.html", landing_page(
        page, path="/this-weekend/",
        title="EDM Events This Weekend in Dallas – House, Techno & Bass Shows | DFW EDM",
        description=(f"{len(wknd)} EDM, house, techno and bass shows in Dallas-Fort Worth this weekend ({span}), "
                     "with times, venues and tickets."),
        h1="EDM events in Dallas this weekend",
        intro=f"{span}: {len(wknd)} show{'s' if len(wknd) != 1 else ''} across Dallas-Fort Worth.",
        addr="", events=wknd, venues=venues, today=today, nav=nav, current_href="/this-weekend/",
        fill_months=False, empty_note="No shows are listed for this weekend yet. See every upcoming show below.")))

    # Genres
    for g in genres:
        evs = [e for e in dated if e.get("genre") == g]
        where = sorted({venue_name(e, venues) for e in evs})
        href = f"/genres/{slugify(g)}/"
        pages.append((f"genres/{slugify(g)}/index.html", landing_page(
            page, path=href,
            title=f"DFW {g} Music – Upcoming {g} Shows in Dallas | DFW EDM",
            description=(f"{len(evs)} upcoming {g.lower()} shows in Dallas-Fort Worth"
                         f"{' at ' + ', '.join(where[:3]) + (' and more' if len(where) > 3 else '') if where else ''}"
                         ", listed by date with tickets."),
            h1=f"{g} shows in Dallas-Fort Worth",
            intro=f"{len(evs)} upcoming {g.lower()} show{'s' if len(evs) != 1 else ''} at {len(where)} venue{'s' if len(where) != 1 else ''}.",
            addr="", events=evs, venues=venues, today=today, nav=nav, current_href=href)))

    # Venues
    for k in venue_keys:
        v = venues[k]
        evs = [e for e in dated if e["venue"] == k]
        wk = [e for e in weekly_all if e["venue"] == k]
        href = f"/venues/{slugify(v['name'])}/"
        city = (postal_address(v.get("address")) or {}).get("addressLocality", "Dallas")
        pages.append((f"venues/{slugify(v['name'])}/index.html", landing_page(
            page, path=href,
            title=f"{v['name']} Events & Tickets – Upcoming EDM Shows in {city} | DFW EDM",
            description=(f"{len(evs)} upcoming EDM, house and techno shows at {v['name']} in {city}, TX"
                         + (", plus " + " and ".join(e["artist"] for e in wk) + " every week" if wk else "")
                         + ", with dates, times and tickets."),
            h1=f"Upcoming shows at {v['name']}",
            intro=(f"{len(evs)} upcoming electronic show{'s' if len(evs) != 1 else ''} at {v['name']}"
                   + (f" and {len(wk)} weekly night{'s' if len(wk) != 1 else ''}." if wk else ".")),
            addr=v.get("address") or "", events=evs, venues=venues, today=today, nav=nav, current_href=href,
            weekly=wk, empty_note=f"No dated shows at {v['name']} right now.")))
    return pages


def remove_stale(dirname, keep):
    """Delete landing pages for genres / venues that no longer have shows."""
    root = os.path.join(ROOT, dirname)
    if not os.path.isdir(root):
        return
    for slug in os.listdir(root):
        if f"{dirname}/{slug}/index.html" not in keep:
            path = os.path.join(root, slug, "index.html")
            if os.path.exists(path):
                os.remove(path)
            try:
                os.rmdir(os.path.join(root, slug))
            except OSError:
                pass


# ---------------------------------------------------------------- legal pages
LEGAL_UPDATED = "November 13, 2026"
CONTACT = f'a direct message to <a href="{INSTAGRAM}">@dfw.edm on Instagram</a>'

PRIVACY_HTML = f"""<article class="legal">
<p>Last updated {LEGAL_UPDATED}.</p>
<h2>What we collect</h2>
<p>Nothing. edmdfw.com has no accounts, sign-ups, forms, comments, ads or analytics, and it sets no
cookies of its own. We don't collect, sell or share personal information.</p>
<h2>Services the site loads</h2>
<ul>
<li><strong>Hosting:</strong> the site is hosted on GitHub Pages. GitHub may log visitors' IP addresses
for security and to keep the service running (<a href="https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement">GitHub's privacy statement</a>).</li>
<li><strong>Fonts:</strong> the typeface loads from Google Fonts, so Google receives your IP address and
browser details (<a href="https://policies.google.com/privacy">Google's privacy policy</a>).</li>
<li><strong>Flyers and logos:</strong> some images load directly from ticketing, venue and promoter
websites, which can see that your browser requested them.</li>
</ul>
<h2>Links to other sites</h2>
<p>Ticket, resale, venue and social media links take you to other companies' sites, which have their own
privacy policies. Some ticket links may be affiliate links: the seller may use cookies to record that you
came from us, so we can earn a commission. We never receive your purchase or payment details.</p>
<h2>Children</h2>
<p>The site isn't directed at children under 13, and many listed events are 18+ or 21+.</p>
<h2>Changes and contact</h2>
<p>If this policy changes, we'll update this page and its date. Questions: send {CONTACT}.</p>
</article>"""

TERMS_HTML = f"""<article class="legal">
<p>Last updated {LEGAL_UPDATED}. By using edmdfw.com you agree to these terms.</p>
<h2>Listings are for information only</h2>
<p>Event listings are gathered automatically from public venue, promoter and ticketing pages and
updated every few days. They can be incomplete, out of date or wrong: dates, times, lineups, prices,
age limits and venues change, and shows get moved or cancelled. Always confirm the details with the
venue or the official ticket seller before you buy tickets or make plans.</p>
<h2>We don't sell tickets</h2>
<p>Buying a ticket happens on the seller's site, between you and that seller. Their terms, prices, fees
and refund policies apply, and questions about orders or refunds go to them. Resale marketplaces set
their own prices, which can be above face value.</p>
<h2>No affiliation</h2>
<p>DFW EDM is an independent calendar. It is not affiliated with, endorsed by or sponsored by any venue,
promoter, artist, festival or ticket seller listed. Their names and logos belong to their owners and
are used only to identify their events.</p>
<h2>Flyers and images</h2>
<p>Event flyers, artwork and logos belong to their creators and are shown only to promote the events
they advertise. If you own an image and want it credited, changed or removed, send {CONTACT} with the
event and the image, and we'll handle it promptly.</p>
<h2>Affiliate links</h2>
<p>Some ticket links, including resale links, may be affiliate links. If you buy through one, we may
earn a commission at no extra cost to you. We also promote some venues' events: discount codes shown on
the site (for example on CTRL Room shows) are our promoter codes, and we may earn from tickets bought with
them. None of this changes which events we list or how they're shown.</p>
<h2>No warranty</h2>
<p>The site is provided "as is", without warranties of any kind. To the extent the law allows, DFW EDM
isn't liable for losses from using it or relying on its listings, including cancelled, moved or
mislisted events, or purchases made on other sites.</p>
<h2>General</h2>
<p>These terms are governed by the laws of the State of Texas. We may update them, and the date above
shows the latest version. Questions: send {CONTACT}.</p>
</article>"""


# Concert halls, arenas, pavilions and festival grounds (the
# /dallas-edm-concerts/ page) -- as opposed to clubs and after-hours rooms.
CONCERT_VENUES = {"silo", "bombfactory", "studiofactory", "deepellumartco", "toyotamusic",
                  "dosequis", "dickies", "fairpark", "pantherisland"}


# Old addresses that now live elsewhere. GitHub Pages can't send real
# redirects, so each gets a tiny page that forwards visitors at once and tells
# Google (canonical) which address to index. Not listed in the sitemap.
MOVED = {
    "dallas-edm-events/": "/dallas-edm-shows/",
}


def forwarding_page(target):
    url = SITE + target
    return (f'<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8">\n'
            f'<title>Moved – DFW EDM</title>\n<link rel="icon" href="/favicon.ico">\n<link rel="canonical" href="{url}">\n'
            f'<meta http-equiv="refresh" content="0; url={target}">\n'
            f'<script>location.replace("{target}" + location.hash)</script>\n'
            f'</head><body><p>This page moved to <a href="{target}">{url}</a>.</p></body></html>\n')


def main():
    data = load_data()
    today = today_str()
    with open(os.path.join(ROOT, "index.html"), encoding="utf-8") as f:
        original = f.read()
    page = build_home_head(original, data, today)
    body = lambda p: p[p.index("</head>"):]
    assert body(page) == body(original), "build must never change the homepage body"
    if page != original:
        write("index.html", page)

    pages = build_landing_pages(page, data, today)
    keep = {rel for rel, _ in pages}
    remove_stale("genres", keep)
    remove_stale("venues", keep)
    for rel, content in pages:
        write(rel, content)
    for old, target in MOVED.items():
        write(old + "index.html", forwarding_page(target))

    lastmod = now_ct().date().isoformat()
    urls = ["/"] + ["/" + rel[: -len("index.html")] for rel, _ in pages]
    write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n'
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
          + "".join(f"  <url><loc>{SITE}{u}</loc><lastmod>{lastmod}</lastmod>"
                    f"<changefreq>daily</changefreq></url>\n" for u in urls)
          + "</urlset>\n")
    write("robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n")
    print(f"Updated the homepage <head>; built {len(pages)} landing page(s), sitemap with {len(urls)} URL(s).")


if __name__ == "__main__":
    main()
