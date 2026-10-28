#!/usr/bin/env python3
"""
Weekly automated updater for edmdfw.com.

Calls the Claude API (web search + web fetch tools) to research current
DFW EDM / house / bass / techno events across all tracked venues, then
regenerates events.js in the exact format the site expects.

Requires:
  pip install anthropic
  env var ANTHROPIC_API_KEY

Run manually to test:
  ANTHROPIC_API_KEY=sk-ant-... python3 update_events.py
"""

import html
import json
import os
import re
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from urllib.parse import urljoin

import anthropic

MODEL = "claude-sonnet-5"
OUTPUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "events.js")
# Raw JSON snapshot of the last successful run, committed to the repo alongside
# events.js. Read back in on the next run so a transient research miss (a venue
# page that failed to load, an event the model ran out of budget to re-verify)
# doesn't silently delete real, still-upcoming events or downgrade a real event
# image back to null/fallback. See merge_with_previous() below.
EVENTS_DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "events_data.json")
MAX_TOKENS_PER_TURN = 16000

VENUES = {
    "silo": {"name": "SILO Dallas", "address": "1340 Manufacturing St, Dallas, TX", "site": "https://silodallas.com/events"},
    "itlldo": {"name": "It'll Do Club", "address": "4322 Elm St, Dallas, TX", "site": "https://www.itlldoclub.com/"},
    "ctrlroom": {"name": "CTRL Room Dallas", "address": "2511 Swiss Ave, Dallas, TX", "site": "https://www.ctrlroomdallas.com/events"},
    "ductwork": {"name": "Ductwork at SILO", "address": "1340 Manufacturing St, Dallas, TX", "site": "https://linktr.ee/ductworkdallas"},
    "bombfactory": {"name": "The Bomb Factory", "address": "2713 Canton St, Dallas, TX", "site": "https://www.thebombfactory.com/events"},
    "studiofactory": {"name": "The Studio at The Bomb Factory", "address": "2727 Canton St, Dallas, TX", "site": "https://www.thebombfactory.com/events"},
    "greenelephant": {"name": "Green Elephant", "address": "5627 Dyer St, Dallas, TX", "site": "https://www.greenelephantdallas.com/blank"},
    "sounders": {"name": "Sounders", "address": "1211 E Levee St, Dallas, TX", "site": "https://soundersdallas.com/pages/events-tickets"},
    "stereolive": {"name": "Stereo Live Dallas", "address": "N/A - CLOSED", "site": "", "closed": True},
    "deepellumartco": {"name": "Deep Ellum Art Co", "address": "2803 Taylor St, Dallas, TX", "site": "https://www.deepellumart.co/shows"},
    "toyotamusic": {"name": "Toyota Music Factory / The Pavilion", "address": "316 W Las Colinas Blvd, Irving, TX", "site": "https://www.toyotamusicfactory.com/upcoming-events"},
    "dosequis": {"name": "Dos Equis Pavilion", "address": "3839 S Fitzhugh Ave, Dallas, TX", "site": "https://www.dosequispavilion.com/events"},
    "dickies": {"name": "Dickies Arena", "address": "1911 Montgomery St, Fort Worth, TX", "site": "https://dickiesarena.com/events"},
    "fairpark": {"name": "Fair Park Dallas (Festival)", "address": "1300 Robert B Cullum Blvd, Dallas, TX", "site": "https://lightsallnight.com/"},
    "coba": {"name": "Coba (After Hours)", "address": "2800 Canton St, Dallas, TX", "site": "https://www.cobadallas.com/"},
    "villagebeach": {"name": "The Village Beach Club", "address": "5670 Village Glen Dr, Dallas, TX 75206", "site": "https://villagebeachclub.com/event-calendar/"},
    "shyboy": {"name": "Shyboy Hi-Fi", "address": "1313 Main St, Dallas, TX 75202", "site": "https://shyboyhifi.com/"},
}

# Large, mixed-genre venues where a major touring EDM act can easily get lost
# among dozens of non-electronic bookings, or where the calendar page paginates
# by month and doesn't surface far-out shows on the first fetch. These get an
# extra, mandatory cross-check search rather than relying on a single page fetch.
HIGH_RISK_MIXED_GENRE_VENUES = ["dickies", "dosequis", "toyotamusic", "bombfactory", "studiofactory"]

# Venues that book a heavy mix of non-electronic acts (hip hop, country,
# reality-TV-personality "DJ" sets, etc.) alongside real electronic artists.
# These need extra scrutiny in the OTHER direction from HIGH_RISK_MIXED_GENRE_VENUES:
# don't just include every billed "DJ" -- verify the act is a genuine
# electronic/dance music artist before adding them.
SELECTIVE_GENRE_VENUES = ["villagebeach"]

# Some venues' primary website is a slow-moving marketing page that lags behind
# where they actually announce new bookings. It'll Do Club's own homepage confirmed
# this: a Linktree page (which is literally the "TICKETS" link on their homepage)
# had a "Chromeo (DJ set)" show under an "ANNOUNCED THIS WEEK!" section, and a
# TwoFaced show, neither of which had made it onto the homepage's own agenda list
# yet. For venues listed here, ALWAYS fetch this secondary URL in addition to the
# main site -- treat anything under a "this week" / "just announced" / similarly
# freshness-flagged section as high-priority, since it represents bookings the
# venue's main page hasn't caught up to displaying yet.
VENUE_SECONDARY_SOURCES = {
    "itlldo": "https://linktr.ee/itlldoclub",
    # Sounders posts each night as a news post; H.A.M. Promotions (its
    # promoter) and ma.to list them too.
    "sounders": "https://soundersdallas.com/blogs/news + https://www.hampromos.com/blogs/news + https://ma.to/venue/soundersdallas",
}

# Venues whose calendar is built around themed nights / series rather than
# named headliners. Research must list those nights even with no DJ named.
EVENT_CENTERED_VENUES = ["sounders"]

VENUE_FALLBACK_IMAGES = {
    "silo": "https://silodallas.com/og-image.png",
    "ductwork": "https://cdn.vor.us/images/white-label/disco-donnie/2025/silo.png",
    "itlldo": "https://static1.squarespace.com/static/687877d212aabf1aafc5c893/t/687883bae925b43e83551a43/1752728506887/_ITLLDOCLUB.png?format=1500w",
    "greenelephant": "https://static.wixstatic.com/media/608a53_4a8795eff0ef4c958d80635f6a0fd54a~mv2.jpg/v1/fit/w_480,h_641,q_90,enc_avif,quality_auto/608a53_4a8795eff0ef4c958d80635f6a0fd54a~mv2.jpg",
    # CTRL Room's own plain venue logo -- deliberately not any specific event's DJ
    # flyer. Used for the recurring "Haus Sundays" card and any other CTRL Room
    # event missing its own image, since a specific artist's flyer would go stale
    # or look misleading once reused for a different week/act.
    "ctrlroom": "https://cdn.prod.website-files.com/69c17a74a763699ce65b1b8d/69c24f01971e47d2420adc69_CTRL-OpenGraph.png",
    # Coba's own pyramid graphic -- used for the recurring Ritual Fridays /
    # Voltage Saturdays cards and any other Coba event missing its own flyer.
    "coba": "https://static.wixstatic.com/media/37092d_88fc91f3ddb7491d96f5dfa270236b20~mv2.jpg/v1/fit/w_2500,h_1330,al_c/37092d_88fc91f3ddb7491d96f5dfa270236b20~mv2.jpg",
}

# Coba runs two weekly after-hours nights (Ritual Fridays, Voltage Saturdays)
# that the site shows as ONE combined recurring card. Research runs and the
# carry-forward in merge_with_previous() tend to re-add them as separate
# cards, so combine_coba_recurring() drops any separate undated Ritual /
# Voltage entries and always emits exactly this one in their place.
COBA_RECURRING_EVENT = {
    "artist": "Ritual Fridays / Voltage Saturdays",
    "venue": "coba",
    "date": None,
    "time": "2:00 AM - 5:00 AM",
    "genre": "House / Techno",
    "direct": "https://www.cobadallas.com/buytickets",
    "image": None,  # filled from VENUE_FALLBACK_IMAGES["coba"]
    "recurring": "Every Friday & Saturday",
}
COBA_RECURRING_NAMES = ("ritual", "voltage")

# Card images must be real: the event's own promotional flyer, or failing that
# the venue's own logo/brand graphic. Never a made-up or generic placeholder.
# fill_event_images() pulls each event's flyer straight from its ticket page
# (og:image) -- SILO / Ductwork (SeeTickets) and It'll Do (Eventbrite) publish
# one for virtually every show -- and only uses the venue logo when the ticket
# page genuinely has none. Venues missing from VENUE_FALLBACK_IMAGES get their
# logo from their own website's og:image (see venue_logo_images()).
OG_FETCH_TIMEOUT = 20
OG_FETCH_WORKERS = 8

# Event cards are a short, wide strip, so tall flyers are cropped top and
# bottom. detect_face_focus() finds faces in each event flyer and stores an
# object-position ("x% y%") so the visible strip lands on the face. The image
# itself is never modified -- only which part of it the card shows.
FACE_IMAGE_MAX_BYTES = 15_000_000
FACE_DETECT_MAX_SIDE = 900

# StubHub resale inventory realistically only exists for shows happening soon --
# searching for it on events 3+ months out mostly wastes budget on dead ends. This
# caps the dedicated StubHub lookup pass (see run_stubhub_lookup()) to events within
# this many days, which keeps it well inside a single run's search budget while still
# catching the vast majority of events that actually have real listings.
STUBHUB_LOOKUP_WINDOW_DAYS = 30

# The only genre labels the site shows. Every event is filed under exactly
# one of these (see main_genre()), so visitors get a short, consistent genre
# filter instead of dozens of one-off subgenre strings.
MAIN_GENRES = [
    "House", "Techno", "Trance", "Drum & Bass", "Dubstep", "Bass",
    "UK Bass / Garage", "Downtempo", "Hard Dance", "Trap",
]

# (pattern, main genre), checked in order against each part of a raw label
# like "Melodic Dubstep/Future Bass". The first part that matches decides, so
# the act's leading genre wins; parts that are just "Electronic", "EDM",
# "Dance", "DJ Set" etc. match nothing and are skipped.
_GENRE_RULES = [
    (r"hard ?style|hard ?dance|hardcore|gabber|frenchcore|uptempo", "Hard Dance"),
    (r"drum ?(&|and|n'?) ?bass|\bdnb\b|\bd&b\b|jungle|liquid", "Drum & Bass"),
    (r"uk ?garage|\bukg\b|garage|2-?step|uk ?bass|grime|bassline", "UK Bass / Garage"),
    (r"trance", "Trance"),
    (r"dubstep|riddim|brostep|tearout", "Dubstep"),
    (r"downtempo|chill|lo-?fi|ambient|trip ?hop", "Downtempo"),
    (r"techno", "Techno"),
    (r"house|disco|funk|big ?room|electro(?!nic|-? ?pop)|eurodance|guarachero|latin", "House"),
    (r"trap|phonk", "Trap"),
    (r"bass|moombah|future|wave|midtempo|glitch", "Bass"),
]


# Genre calls made by hand that always win over research, matched as a
# lowercase substring of the artist name. Add an entry when the site owner
# corrects an act's genre so later runs can't flip it back.
GENRE_OVERRIDES = {
    "whethan": "Bass",
    # Reviewed when Trap was added (Oct 2026): trap-first acts, plus two
    # acts research had filed under Bass.
    "rl grime": "Trap",
    "flosstradamus": "Trap",
    "valentino khan": "Trap",
    "barnacle boi": "Trap",
    "hex cougar": "Trap",
    "josh baker": "House",
    "level up - the ritual": "Dubstep",
    # Full review (Oct 2026), judged on each act's current sound.
    "ayybo": "House",            # bass house
    "riordan": "UK Bass / Garage",
    "omnom": "House",            # bass house
    "awen": "House",             # afro / melodic house
    "maddix": "Techno",          # hard techno
    "crankdat": "Dubstep",
    "layz": "Dubstep",
    "riot w/": "Dubstep",        # RIOT w/ SPAG, HEKLER
}


def specific_genre(raw):
    """The main genre a label names, or None for vague labels such as
    "Electronic", "EDM", "Dance / DJ Set" or "Electropop"."""
    for part in re.split(r"[/,|()]", (raw or "").lower()):
        for pattern, genre in _GENRE_RULES:
            if re.search(pattern, part):
                return genre
    return None


def main_genre(raw):
    """Map any genre label to one of MAIN_GENRES (House if it's vague)."""
    return specific_genre(raw) or "House"


def override_genre(artist):
    name = (artist or "").lower()
    return next((g for key, g in GENRE_OVERRIDES.items() if key in name), None)


# Cost controls. Shows that were searched and had no StubHub listing / no
# findable flyer aren't searched again for this many days (tracked per event
# as stubhub_checked / image_checked in events_data.json), instead of being
# re-searched on every 3-day run.
STUBHUB_RECHECK_DAYS = 7
IMAGE_LOOKUP_RECHECK_DAYS = 7

# Thinking depth per pass. Research needs judgment (which acts count as
# electronic, finding every venue's shows); the two lookup passes are simple
# "find this link" jobs.
RESEARCH_EFFORT = "medium"
LOOKUP_EFFORT = "low"

# Per-token prices for MODEL (USD per million tokens), only used to print an
# estimated cost per run. Web searches are billed per search on top of this.
PRICE_INPUT_PER_MTOK = 2.00
PRICE_CACHE_WRITE_PER_MTOK = 2.50   # 1.25x input (5-minute cache)
PRICE_CACHE_READ_PER_MTOK = 0.20    # 0.1x input
PRICE_OUTPUT_PER_MTOK = 10.00

# Running token / tool totals per pass, printed at the end of each run.
USAGE = {}


def tracked_create(pass_name, client, **kwargs):
    """Create a message and add the response's usage to USAGE[pass_name]."""
    response = client.messages.create(**kwargs)
    u = response.usage
    totals = USAGE.setdefault(pass_name, {
        "requests": 0, "input": 0, "cache_write": 0, "cache_read": 0, "output": 0,
        "web_searches": 0, "web_fetches": 0,
    })
    totals["requests"] += 1
    totals["input"] += getattr(u, "input_tokens", 0) or 0
    totals["cache_write"] += getattr(u, "cache_creation_input_tokens", 0) or 0
    totals["cache_read"] += getattr(u, "cache_read_input_tokens", 0) or 0
    totals["output"] += getattr(u, "output_tokens", 0) or 0
    tools = getattr(u, "server_tool_use", None)
    if tools:
        totals["web_searches"] += getattr(tools, "web_search_requests", 0) or 0
        totals["web_fetches"] += getattr(tools, "web_fetch_requests", 0) or 0
    return response


def print_usage_summary():
    grand = 0.0
    print("API usage this run (estimated token cost; web searches billed separately per search):")
    for name, t in USAGE.items():
        cost = (
            t["input"] * PRICE_INPUT_PER_MTOK
            + t["cache_write"] * PRICE_CACHE_WRITE_PER_MTOK
            + t["cache_read"] * PRICE_CACHE_READ_PER_MTOK
            + t["output"] * PRICE_OUTPUT_PER_MTOK
        ) / 1_000_000
        grand += cost
        print(
            f"  {name}: {t['requests']} request(s), input {t['input']:,}, cache write {t['cache_write']:,}, "
            f"cache read {t['cache_read']:,}, output {t['output']:,} tokens, "
            f"{t['web_searches']} web search(es), {t['web_fetches']} web fetch(es) -> ~${cost:.2f}"
        )
    print(f"  total: ~${grand:.2f} in tokens")


def checked_recently(e, field, days, today_str):
    last = e.get(field)
    if not last:
        return False
    return last >= (date.fromisoformat(today_str) - timedelta(days=days)).isoformat()

CLOSED_VENUES_NOTE = "Stereo Live Dallas closed permanently in early 2026 and is no longer booking shows. Kept here for reference only."

SYSTEM_PROMPT = f"""You maintain the event data for edmdfw.com, a site tracking electronic/house/bass/techno
shows across Dallas-Fort Worth. Your job each run is to produce a fresh, accurate events list.

VENUES TO CHECK (use each venue's ticketing/events page as the source of truth):
{json.dumps({k: v for k, v in VENUES.items() if not v.get("closed")}, indent=2)}

TASK:
1. For each venue above, visit its events/ticketing page and list EVERY act on the calendar for the
   next ~5 months from today -- do not pre-filter by reading the venue's own genre tag or category
   label. Venues like The Bomb Factory / The Studio at The Bomb Factory book a mix of genres on the
   same calendar, so genre must be judged per-artist, not per-venue.
1a. PAGINATION -- many venue calendars (SILO Dallas via do214, and similar list-style pages) only show
   ~20-25 events on the first page and require clicking "Next Page" / a page=2 link to see events
   further out. A single fetch of page 1 is NOT enough -- you MUST keep following "next page" /
   pagination links (page=2, page=3, etc.) until you either reach a page with no further "Next Page"
   link, or you've gone past the ~5 month lookahead window. This is a known, previously-confirmed
   failure mode: an entire second page of SILO Dallas events (12+ shows including major headliners
   like Adriatique, ZHU, San Holo, Eric Prydz) was missed in a prior run because only page 1 was
   fetched. Treat "the calendar looked short" as a signal to check for pagination, not a signal that
   the venue has nothing more booked.
2. For each act you don't immediately recognize, treat the name as a lead, not a dead end: if it's
   ambiguous whether the act is electronic/dance music, do a quick web search on the artist name
   (e.g. "<artist> genre" or "<artist> dubstep OR house OR techno OR EDM") before deciding. Only skip
   an act once you've confirmed it is not electronic/dance (e.g. confirmed rock band, comedian,
   sports event).
3. Include an act if it fits ANY of these electronic/dance subgenres, including hybrid/crossover acts
   that blend electronic production with other genres: house, tech house, deep house, techno, trance,
   dubstep, riddim, bass, trap, future bass, drum and bass/jungle, hardstyle, electropop, EDM-pop
   crossover, hyperpop-adjacent electronic acts, and DJ sets generally. When in doubt because an act
   straddles electronic and another genre (e.g. an "electropop" or "pop-EDM" artist), err on the side
   of including them with an accurate genre label rather than skipping them.
3a. GENRE LABEL -- "genre" must be exactly ONE of: {", ".join(MAIN_GENRES)}. Judge each act by
   what they play NOW -- their releases and tour billing from roughly the last two years -- not
   older hits, the venue's category tag, or a generic word like "Electronic", "EDM", "Dance" or
   "Pop" (never answer with one of those). Search the artist if you aren't sure. Pick the act's main
   style (tech house, afro house, disco, big room -> House; melodic/hard techno -> Techno; riddim ->
   Dubstep; trap, phonk -> Trap; bass house -> House; future bass, melodic bass -> Bass; hardstyle, hardcore -> Hard Dance; jungle ->
   Drum & Bass; UK garage, speed garage, bassline, grime -> UK Bass / Garage; chill / ambient -> Downtempo).
4. HIGH-RISK VENUES -- {", ".join(VENUES[k]["name"] for k in HIGH_RISK_MIXED_GENRE_VENUES)}: these are
   large arenas/amphitheaters that book mostly non-electronic acts (country, rock, family shows,
   comedy, sports), which makes it easy to skim past the one big EDM headliner buried in a long
   calendar, and their calendar pages often paginate by month so a single fetch of the main events
   page may not surface shows that are several months out. For each of these venues you MUST, in
   addition to fetching the venue's own events page, run at least one supplementary web_search
   specifically like "<venue name> 2026 EDM OR electronic OR house OR techno OR dance tour" to catch
   major touring electronic artists (the kind who play arenas -- e.g. John Summit, Kaskade, ILLENIUM,
   Zedd, Marshmello, Excision, Zeds Dead, Empire of the Sun, etc.) that the calendar page alone might not have surfaced. A missed
   headline arena show is a much worse error than a missed small club night, so err heavily on the
   side of extra searching for these venues specifically.
5. SELECTIVE-GENRE VENUES -- {", ".join(VENUES[k]["name"] for k in SELECTIVE_GENRE_VENUES)}: unlike
   the high-risk venues above, this is the OPPOSITE failure mode -- these venues book heavily mixed
   lineups where NOT every billed act is electronic music (hip hop artists, country artists, reality
   TV personalities doing novelty "DJ" sets, etc. all get billed alongside genuine house/dance DJs).
   Do NOT include an act here just because they're labeled "DJ" on the venue's site. Verify each act
   is a real, dedicated electronic/dance music artist (check their genre via search if you don't
   recognize them) before including. A reality-TV personality or a rapper doing a one-off pool party
   DJ set does not count -- only include artists whose actual career/discography is electronic/dance
   music. Be conservative here: when genuinely unsure whether an act counts, leave them out rather
   than include them.
5a. SECONDARY SOURCES -- for venues listed in VENUE_SECONDARY_SOURCES ({", ".join(VENUES[k]["name"] + " -> " + VENUE_SECONDARY_SOURCES[k] for k in VENUE_SECONDARY_SOURCES)}),
   fetch that URL IN ADDITION to the venue's main site -- it's a real page the venue itself
   directs ticket buyers to, not a workaround. Treat anything flagged there as newly announced
   (e.g. under a "this week" / "just announced" heading) as high-priority: the venue's main
   page has a track record of lagging behind it, so an event you only see on the secondary
   source is not a lower-confidence find -- add it the same as anything from the main site.
6. For each event, capture: artist/event name, date (YYYY-MM-DD), time, a short genre label, and the
   direct ticket purchase URL (the venue's own primary ticket link, not a resale site).
6c. EVENT-CENTERED VENUES -- {", ".join(VENUES[k]["name"] for k in EVENT_CENTERED_VENUES)}: these book
   themed nights and series (e.g. Sounders' "House on Levee St.", "Hard Wired", "Techno & Tequila",
   "Freakquency") more than named headliners. Include every upcoming electronic/dance night even when
   no DJ is named: use the night's own title as "artist", pick the genre from how the night is billed
   (a house night -> House; hardstyle / hard dance -> Hard Dance; techno incl. hard techno -> Techno), and set
   "free": true when the listing says free entry / free with RSVP. Check every source listed for them
   in 5a -- their news posts are where new nights appear first.
6b. SHYBOY HI-FI -- a downtown hi-fi listening bar that books DJ nights and residencies, many of them
   FREE (no ticket). Include its DJ / dance-music nights (house, techno, disco, dance, electronic) whether
   free or ticketed; besides its own site, check its Resident Advisor (ra.co) and ma.to listings. For a
   free event set "free": true and use the event's own listing page (venue site, RA or ma.to event page,
   copied verbatim) as "direct". Only set "free" when the listing actually says free / no cover.
6a. Coba's weekly after-hours nights (Ritual Fridays and Voltage Saturdays) are added by the script
   as a single combined recurring card -- do not include them in "events". Specific dated Coba shows
   (a named guest DJ on a particular night) should still be included as normal.
7. For each event, find its promotional image: the event-specific flyer/artwork, normally the og:image
   meta tag of the individual ticket page. Never use a venue logo, a generic site banner, or an image
   from a different event. If you cannot find the event's own image, leave image as null -- the
   script re-checks every ticket page itself and only then falls back to the venue's logo.
8. If a venue currently has zero electronic/dance events on sale, simply don't include it in "events"
   -- there's no need to explain why or report on venues with nothing booked, just omit them.
9. Do not guess or invent events, dates, or URLs. Every "direct" URL must be copied exactly from an
   actual tool result (a link you saw verbatim in a web_search result or a web_fetch response) --
   never construct one by pattern-matching, e.g. assuming an artist's ticket link follows a template
   like "https://<artist-name><year>.eventbrite.com". Real ticketing URLs are irregular (Eventbrite
   links look like eventbrite.com/e/some-slug-1234567890 with a numeric ID; AXS, SeeTickets, etc each
   have their own real path structure) -- if you notice yourself generating a suspiciously uniform,
   templated URL across many events, stop and re-fetch the actual page instead. If a venue's page
   fails to load or a specific event's ticket link is ambiguous, skip that specific event rather than
   guessing.
10. STUBHUB RESALE LINK -- do NOT search for StubHub links in this pass. Always set "stubhub" to null
    for every event here. StubHub lookups are handled by a separate, dedicated follow-up pass (with its
    own search budget) that only checks events happening soon, where resale inventory is actually likely
    to exist -- searching for it here would just compete with your venue-research budget for no benefit.

OUTPUT FORMAT:
Your final message must contain ONLY a single JSON object between <events_json> and </events_json>
tags -- no preamble sentences, no commentary, no markdown code fences, nothing before the opening
tag or after the closing tag. Structure:

<events_json>
{{
  "last_updated": "YYYY-MM-DD",
  "events": [
    {{
      "artist": "string",
      "venue": "one of the venue keys above",
      "date": "YYYY-MM-DD or null for recurring/undated series",
      "time": "string, e.g. '9:00 PM'",
      "genre": "exactly one of the main genres listed above, e.g. 'House' or 'Techno'",
      "direct": "https://... direct ticket URL",
      "image": "https://... or null",
      "stubhub": "https://www.stubhub.com/.../event/<id>/ real verified listing URL, or null if not found",
      "free": "optional, true only when the listing says the event is free / no cover",
      "price": "optional, the ticket price exactly as the listing shows it (e.g. '$25' or '$20-$45'), else null -- never estimate",
      "recurring": "optional string, only for undated recurring series like weekly nights"
    }}
  ]
}}
</events_json>

Be thorough but only include venue keys you actually checked. Today's date will be given in the user message.
Keep the JSON compact (no extra whitespace/indentation) to conserve output tokens -- there are 16
venues to cover and the full list can run to 100+ events, so verbose formatting risks running out of
room before you finish.
"""


def build_tools():
    return [
        {"type": "web_search_20250305", "name": "web_search", "max_uses": 50},
        # Cap how much of each page gets pulled into context. Set generously
        # (not too tight) since some venue calendar pages -- especially large
        # arenas with long, mixed-genre listings -- need more than a couple
        # thousand tokens to reach every event, and missing a major act is far
        # more costly than a bit of extra token spend. This still avoids
        # pulling truly bloated pages (nav/footer/bundled JS) in full.
        {"type": "web_fetch_20250910", "name": "web_fetch", "max_uses": 50, "max_content_tokens": 10000},
    ]


def run_research(client: anthropic.Anthropic) -> dict:
    today = date.today().isoformat()
    messages = [
        {
            "role": "user",
            "content": f"Today's date is {today}. Research and return the current events JSON as instructed.",
        }
    ]
    tools = build_tools()
    accumulated_text = ""

    for _ in range(14):
        response = tracked_create(
            "research",
            client,
            model=MODEL,
            max_tokens=MAX_TOKENS_PER_TURN,
            output_config={"effort": RESEARCH_EFFORT},
            system=SYSTEM_PROMPT,
            messages=messages,
            tools=tools,
            # Automatic prompt caching: the system prompt + tool defs + the
            # growing message history (every venue page fetched so far) get
            # cached and reused across turns instead of being billed at full
            # price every single API call. Cache reads are ~10% of the normal
            # input token price, which matters a lot for a loop like this that
            # resends the whole accumulated research history each turn.
            cache_control={"type": "ephemeral"},
        )

        turn_text = "".join(
            block.text for block in response.content if getattr(block, "type", None) == "text"
        )

        if response.stop_reason == "pause_turn":
            # Server-side tool (web_search/web_fetch) needs another round-trip.
            messages.append({"role": "assistant", "content": response.content})
            continue

        if response.stop_reason == "max_tokens":
            # Hit the per-turn output cap mid-JSON. Keep what was written and
            # ask the model to resume from exactly where it stopped rather
            # than failing outright.
            accumulated_text += turn_text
            messages.append({"role": "assistant", "content": response.content})
            messages.append({
                "role": "user",
                "content": (
                    "Continue exactly where you left off. Do not repeat any earlier "
                    "text and do not restart the JSON object -- just keep writing from "
                    "the exact character you stopped at, and still end with the closing "
                    "</events_json> tag once the object is complete."
                ),
            })
            continue

        final_text = accumulated_text + turn_text
        match = re.search(r"<events_json>(.*?)</events_json>", final_text, re.S)
        if not match:
            raise RuntimeError("Model did not return an <events_json> block. Raw text:\n" + final_text)
        return json.loads(match.group(1).strip())

    raise RuntimeError("Exceeded max turns without a final answer")


STUBHUB_SYSTEM_PROMPT = """You find real StubHub resale listing URLs for a batch of specific
electronic/dance music events in Dallas-Fort Worth. You will be given a numbered list of events
(artist, venue, date).

For each event, do a web_search like "<artist> <venue city> <date> stubhub tickets" and, if needed,
follow through to the actual event page with web_fetch to confirm it is the right artist/venue/date.
StubHub does NOT have a generic text-search URL you can template from an artist's name -- every real
StubHub link is tied to a specific numeric event ID, e.g. stubhub.com/<slug>/event/123456789/. Only
report a URL for an event if you found and can verify (from an actual search result or fetched page)
that specific numeric-ID event page matches the right artist, venue, AND date. If you can't find a
confident match within a quick search (1-2 searches), report null for that event rather than guessing
or reusing another event's URL -- a missing link is fine, a wrong one is not.

Work through the list efficiently -- these are a nice-to-have second resale option, not worth
exhaustive searching per event. If you're running low on search budget before reaching the end of the
list, prioritize whichever events happen soonest and report null for the rest rather than leaving the
JSON incomplete.

Your final message must contain ONLY a single JSON object between <stubhub_json> and </stubhub_json>
tags -- no preamble, no commentary, nothing before the opening tag or after the closing tag. Structure:

<stubhub_json>
{"results": [{"i": 0, "stubhub": "https://www.stubhub.com/.../event/<id>/ or null"}]}
</stubhub_json>

Include exactly one result object per numbered event, using the same "i" index given in the input list.
"""


def build_stubhub_tools():
    return [
        {"type": "web_search_20250305", "name": "web_search", "max_uses": 90},
        {"type": "web_fetch_20250910", "name": "web_fetch", "max_uses": 40, "max_content_tokens": 4000},
    ]


def run_stubhub_lookup(client: anthropic.Anthropic, events_needing_lookup: list) -> dict:
    """Dedicated second pass, separate from run_research()'s venue/event research, with
    its own tool budget. Only called for events within STUBHUB_LOOKUP_WINDOW_DAYS that
    don't already have a stubhub link (either found this run or carried forward by
    merge_with_previous()). Returns {index: url} for events where a confident match was
    found; any failure here is non-fatal -- it just means those events keep stubhub=null,
    same as if the lookup pass had never run.
    """
    if not events_needing_lookup:
        return {}

    listing = "\n".join(
        f'{i}. "{e["artist"]}" at {VENUES.get(e["venue"], {}).get("name", e["venue"])}, {e.get("date")}'
        for i, e in enumerate(events_needing_lookup)
    )
    messages = [
        {
            "role": "user",
            "content": f"Find StubHub links for these {len(events_needing_lookup)} events:\n\n{listing}",
        }
    ]
    tools = build_stubhub_tools()
    accumulated_text = ""

    for _ in range(10):
        try:
            response = tracked_create(
                "stubhub_lookup",
                client,
                model=MODEL,
                max_tokens=MAX_TOKENS_PER_TURN,
                output_config={"effort": LOOKUP_EFFORT},
                system=STUBHUB_SYSTEM_PROMPT,
                messages=messages,
                tools=tools,
                cache_control={"type": "ephemeral"},
            )
        except Exception as exc:
            print(f"StubHub lookup pass hit an API error, skipping (non-fatal): {exc}", file=sys.stderr)
            return None

        turn_text = "".join(
            block.text for block in response.content if getattr(block, "type", None) == "text"
        )

        if response.stop_reason == "pause_turn":
            messages.append({"role": "assistant", "content": response.content})
            continue

        if response.stop_reason == "max_tokens":
            accumulated_text += turn_text
            messages.append({"role": "assistant", "content": response.content})
            messages.append({
                "role": "user",
                "content": (
                    "Continue exactly where you left off. Do not repeat any earlier text and do not "
                    "restart the JSON object -- just keep writing from the exact character you stopped "
                    "at, and still end with the closing </stubhub_json> tag once complete."
                ),
            })
            continue

        final_text = accumulated_text + turn_text
        match = re.search(r"<stubhub_json>(.*?)</stubhub_json>", final_text, re.S)
        if not match:
            print("StubHub lookup pass did not return a parseable result, skipping (non-fatal).", file=sys.stderr)
            return None
        try:
            parsed = json.loads(match.group(1).strip())
        except Exception as exc:
            print(f"StubHub lookup pass returned invalid JSON, skipping (non-fatal): {exc}", file=sys.stderr)
            return None
        return {r["i"]: r["stubhub"] for r in parsed.get("results", []) if r.get("stubhub")}

    print("StubHub lookup pass exceeded max turns, skipping (non-fatal).", file=sys.stderr)
    return None


def js_str(value):
    if value is None:
        return "null"
    return json.dumps(value, ensure_ascii=False)


def build_events_js(data: dict) -> str:
    events = data["events"]
    last_updated = data.get("last_updated", date.today().isoformat())

    venue_images = data.get("venue_images", VENUE_FALLBACK_IMAGES)

    lines = []
    lines.append(f'const LAST_UPDATED = "{last_updated}";')
    lines.append("")
    lines.append("const VENUES = {")
    for key, v in VENUES.items():
        parts = [f'name: {js_str(v["name"])}', f'address: {js_str(v["address"])}', f'site: {js_str(v["site"])}']
        # Venue-level image the page swaps in if an event's own flyer fails to load.
        parts.append(f'image: {js_str(venue_images.get(key))}')
        if v.get("closed"):
            parts.append("closed: true")
        lines.append(f'  "{key}": {{ {", ".join(parts)} }},')
    lines.append("};")
    lines.append("")
    lines.append(
        "function resale(artist, venueCity) {\n"
        "  const q = encodeURIComponent(`${artist} ${venueCity}`);\n"
        "  return [\n"
        '    { site: "SeatGeek", url: `https://seatgeek.com/search?search=${q}` }\n'
        "  ];\n"
        "}"
    )
    lines.append("")
    lines.append("const EVENTS = [")
    for e in events:
        venue_key = e["venue"]
        venue_name = VENUES.get(venue_key, {}).get("name", venue_key)
        obj = (
            f'  {{ artist: {js_str(e["artist"])}, venue: {js_str(venue_key)}, '
            f'date: {js_str(e.get("date"))}, time: {js_str(e.get("time"))}, '
            f'genre: {js_str(e.get("genre"))}, direct: {js_str(e["direct"])}, '
            f'image: {js_str(e.get("image") or venue_images.get(venue_key))}'
        )
        if e.get("focus") and e.get("image"):
            obj += f', focus: {js_str(e["focus"])}'
        if e.get("recurring"):
            obj += f', recurring: {js_str(e["recurring"])}'
        resale_expr = f'resale({js_str(e["artist"])}, {js_str(venue_name)})'
        if e.get("free") is True:
            obj += ", free: true"
        elif e.get("price"):
            obj += f', price: {js_str(str(e["price"]))}'
        if not e.get("date") or e.get("free") is True:
            # Free events and recurring series (Haus Sundays, Ritual Fridays / Voltage
            # Saturdays) only ever link to the venue directly -- no resale.
            resale_expr = "[]"
        elif e.get("stubhub"):
            resale_expr += f'.concat([{{ site: "StubHub", url: {js_str(e["stubhub"])} }}])'
        obj += f', resale: {resale_expr} }},'
        lines.append(obj)
    lines.append("];")
    lines.append("")
    lines.append(f'const CLOSED_VENUES_NOTE = {js_str(CLOSED_VENUES_NOTE)};')
    lines.append("")
    return "\n".join(lines)


# Markers that typically introduce a support act, collab partner, or subtitle
# rather than a different headliner -- e.g. "Luke Alessi" and "Luke Alessi +
# Red Eye" are the same booking, one run just found more detail than the
# other. Truncating the name at the first marker before normalizing keeps the
# match key anchored to the headliner instead of the full string, which is
# what actually varies between runs.
_CORE_NAME_MARKERS = [
    " + ", " presents", " Presents", " PRESENTS", "(", " — ", " - ",
    " b2b ", " B2B ", " x ", " X ", ": ", " w/ ", " W/ ",
]


def normalize_key(artist, venue, event_date):
    """Loose match key so minor renames/punctuation drift between runs (e.g. an
    added '+ Red Eye' support-act suffix, an em-dash vs hyphen, a "Presents:"
    prefix) still count as the same event for merge purposes -- otherwise the
    merge safety net backfires: instead of preventing a dropped event, it
    creates a duplicate every time a run phrases the same booking slightly
    differently, which is worse than the problem it was meant to solve."""
    core = artist or ""
    for marker in _CORE_NAME_MARKERS:
        idx = core.find(marker)
        if idx != -1:
            core = core[:idx]
    norm_artist = re.sub(r"[^a-z0-9]", "", core.lower())[:40]
    return (venue, event_date, norm_artist)


def load_previous_events():
    if not os.path.exists(EVENTS_DATA_PATH):
        return []
    try:
        with open(EVENTS_DATA_PATH, "r", encoding="utf-8") as f:
            payload = json.load(f)
        return payload.get("events", [])
    except Exception as exc:
        print(f"Could not read previous {EVENTS_DATA_PATH}, skipping merge safety net: {exc}", file=sys.stderr)
        return []


def is_upcoming_or_recurring(event_date_str, today_str):
    if not event_date_str:
        return True  # undated recurring series -- always eligible to carry forward
    return event_date_str >= today_str


def merge_with_previous(new_events, previous_events, today_str):
    """Script-side safety net, independent of whether the model followed its
    research instructions this run. Two failure modes this guards against,
    both observed in production:

    1. A whole venue gets silently dropped from the output because its page
       failed to load / the run ran out of turn or token budget before
       reaching it -- NOT because the venue actually has zero events. If a
       previously-known, still-upcoming event isn't present in this run's
       results at all, keep it rather than deleting it from the site.
    2. A per-event image regresses from a real, previously-found image back
       to null (which then falls back to a generic venue image) because this
       run's research didn't re-find/re-fetch it. If this run has an event
       but with a null image and a previous run had a real image for the
       same event, keep the old image instead of losing it.

    Events are matched by (venue, date, normalized artist). Anything from the
    previous run that has already passed (date before today) is never carried
    forward, so this can't resurrect expired shows.
    """
    prev_by_key = {}
    for e in previous_events:
        if not is_upcoming_or_recurring(e.get("date"), today_str):
            continue
        prev_by_key[normalize_key(e.get("artist"), e.get("venue"), e.get("date"))] = e

    new_by_key = {
        normalize_key(e.get("artist"), e.get("venue"), e.get("date")): e for e in new_events
    }

    for key, e in new_by_key.items():
        prev = prev_by_key.get(key)
        if not prev:
            continue
        if not e.get("image") and prev.get("image"):
            e["image"] = prev["image"]
        if not e.get("stubhub") and prev.get("stubhub"):
            e["stubhub"] = prev["stubhub"]
        for field in ("stubhub_checked", "image_checked"):
            if not e.get(field) and prev.get(field):
                e[field] = prev[field]
        if e.get("image") == prev.get("image") and prev.get("focus_src"):
            e["focus"] = prev.get("focus")
            e["focus_src"] = prev["focus_src"]
        if specific_genre(e.get("genre")) is None and prev.get("genre") in MAIN_GENRES:
            e["genre"] = prev["genre"]  # vague label this run; keep the genre already worked out

    merged = list(new_events)
    carried = [prev for key, prev in prev_by_key.items() if key not in new_by_key]
    if carried:
        by_venue = {}
        for e in carried:
            by_venue.setdefault(e.get("venue"), []).append(e.get("artist"))
        summary = "; ".join(f'{v}: {", ".join(a)}' for v, a in by_venue.items())
        print(
            f"Carried forward {len(carried)} previously-known event(s) not present in this "
            f"run's research ({summary}) -- these were kept from the last successful run "
            f"rather than dropped. Verify they still look right if this persists across runs.",
            file=sys.stderr,
        )
        merged.extend(carried)

    return merged


def _ticket_id(url):
    """Ticket URL without tracking query/fragment, for duplicate matching."""
    return re.sub(r"[?#].*$", "", (url or "").strip().lower()).rstrip("/")


def are_duplicate_events(a, b, generic_images):
    """Same venue and date, plus any one of: the same ticket link, the same
    event flyer, or names where one contains the other ("AWEN Hybrid" vs
    "AWEN (Hybrid Set)"). Runs and carry-forward often word the same show
    differently ("me n u on New Years Eve" vs "NYE with me n u") -- but the
    ticket link or flyer gives it away."""
    if a.get("venue") != b.get("venue") or a.get("date") != b.get("date") or not a.get("date"):
        return False
    if a.get("direct") and _ticket_id(a.get("direct")) == _ticket_id(b.get("direct")):
        return True
    img_a, img_b = a.get("image"), b.get("image")
    if img_a and img_a == img_b and img_a not in generic_images:
        return True
    name_a = re.sub(r"[^a-z0-9]", "", (a.get("artist") or "").lower())
    name_b = re.sub(r"[^a-z0-9]", "", (b.get("artist") or "").lower())
    short, long_ = sorted((name_a, name_b), key=len)
    if len(short) >= 4 and short in long_:
        return True
    # Same acts billed in a different order ("Ben Nicky + Vini Vici" vs
    # "Vini Vici + Ben Nicky").
    return len(_name_words(a.get("artist"))) >= 2 and _name_words(a.get("artist")) == _name_words(b.get("artist"))


_BILLING_WORDS = {"x", "b2b", "and", "w", "with", "feat", "ft", "presents", "vs"}


def _name_words(artist):
    words = re.findall(r"[a-z0-9]+", (artist or "").lower())
    return frozenset(w for w in words if w not in _BILLING_WORDS)


def dedupe_events(events, generic_images):
    """Drop duplicate listings of the same show, keeping the first one (this
    run's research comes before carried-forward events) and filling any
    fields it's missing (flyer, StubHub link, face focus) from the others."""
    kept = []
    dropped = []
    for e in events:
        match = next((k for k in kept if are_duplicate_events(k, e, generic_images)), None)
        if not match:
            kept.append(e)
            continue
        for field in ("image", "stubhub", "focus", "focus_src", "stubhub_checked", "image_checked"):
            if not match.get(field) and e.get(field):
                match[field] = e[field]
        dropped.append(f'{e.get("artist")} (dup of {match.get("artist")}, {e.get("venue")} {e.get("date")})')
    if dropped:
        print(f"Removed {len(dropped)} duplicate listing(s): " + "; ".join(dropped))
    return kept


def combine_coba_recurring(events):
    """Replace any separate undated Ritual Fridays / Voltage Saturdays cards
    with the single combined COBA_RECURRING_EVENT card. Dated Coba shows (a
    specific guest DJ on a given night) are left alone."""
    def is_coba_weekly(e):
        name = (e.get("artist") or "").lower()
        return (
            e.get("venue") == "coba"
            and not e.get("date")
            and any(n in name for n in COBA_RECURRING_NAMES)
        )

    kept = [e for e in events if not is_coba_weekly(e)]
    kept.append(dict(COBA_RECURRING_EVENT))
    return kept


_OG_PATTERNS = [
    re.compile(r'<meta[^>]+(?:property|name)=["\'](?:og:image(?::secure_url)?|twitter:image)["\'][^>]*?content=["\']([^"\']+)["\']', re.I),
    re.compile(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]*?(?:property|name)=["\'](?:og:image(?::secure_url)?|twitter:image)["\']', re.I),
]


# SeeTickets (SILO, Ductwork) ticket links end in a numeric event ID, and that
# show's flyer is hosted under the same ID: wl.seetickets.us/event/RL-GRIME-DALLAS/702474
# -> cdn.vor.us/event/702474/og/....png. Matching on the ID finds the right flyer
# even when the page's og:image is a generic venue banner, and guarantees a
# flyer never gets attached to the wrong show.
SEETICKETS_EVENT_ID = re.compile(r"seetickets\.us/event/[^/?#]+/(\d+)", re.I)
# Venue pages that list their SeeTickets shows with flyers, scanned as a
# fallback when an individual ticket page can't be read.
SEETICKETS_LISTING_PAGES = [
    "https://silodallas.com/events",
    "https://silodallas.com/",
    "https://wl.seetickets.us/SILO",
    "https://wl.seetickets.us/DiscoPresents-Ductwork",
]


def seetickets_event_id(url):
    m = SEETICKETS_EVENT_ID.search(url or "")
    return m.group(1) if m else None


def vor_images_by_event_id(page):
    """{seetickets event id: flyer url} for every cdn.vor.us event image on a page."""
    found = {}
    for m in re.finditer(r'https?:(?:\\?/){2}cdn\.vor\.us(?:\\?/)event(?:\\?/)(\d+)(?:\\?/)[^"\'\s<>]+', page):
        url = html.unescape(m.group(0).replace("\\/", "/"))
        while url.endswith(")") and url.count(")") > url.count("("):
            url = url[:-1]
        event_id = m.group(1)
        # Prefer the og/share render of the flyer when a page has several sizes.
        if event_id not in found or ("/og/" in url and "/og/" not in found[event_id]):
            found[event_id] = url
    return found


def fetch_html(url):
    """Return (html, final_url) for a page, or (None, None) on failure."""
    if not url:
        return None, None
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/126.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
        })
        with urllib.request.urlopen(req, timeout=OG_FETCH_TIMEOUT) as resp:
            return resp.read(3_000_000).decode("utf-8", "replace"), resp.geturl()
    except Exception as exc:
        print(f"Page fetch failed for {url}: {exc}", file=sys.stderr)
        return None, None


def og_image_from_html(page, final_url):
    for pattern in _OG_PATTERNS:
        m = pattern.search(page)
        if m:
            return urljoin(final_url, html.unescape(m.group(1).strip()))
    return None


def fetch_og_image(url):
    """Return the og:image (or twitter:image) URL of a page, or None."""
    page, final_url = fetch_html(url)
    return og_image_from_html(page, final_url) if page else None


def find_event_flyer(e):
    """Best flyer URL for one event from its own ticket page, or None."""
    page, final_url = fetch_html(e.get("direct"))
    event_id = seetickets_event_id(e.get("direct"))
    if event_id:
        if not page:
            return None
        return vor_images_by_event_id(page).get(event_id)
    return og_image_from_html(page, final_url) if page else None


def is_acceptable_flyer(e, img, generic):
    """A flyer must not be a venue logo / generic banner, and a SeeTickets
    image (cdn.vor.us) for a SeeTickets show must be under that show's own
    event ID -- otherwise it's another show's flyer or a site banner."""
    if not img or img in generic:
        return False
    event_id = seetickets_event_id(e.get("direct"))
    if event_id and "cdn.vor.us" in img:
        return f"/event/{event_id}/" in img
    return True


def venue_logo_images():
    """Venue key -> logo/brand image. Hardcoded VENUE_FALLBACK_IMAGES win;
    any other open venue gets its own website's og:image."""
    images = dict(VENUE_FALLBACK_IMAGES)
    missing = [k for k, v in VENUES.items() if k not in images and v.get("site") and not v.get("closed")]
    with ThreadPoolExecutor(OG_FETCH_WORKERS) as pool:
        for key, img in zip(missing, pool.map(lambda k: fetch_og_image(VENUES[k]["site"]), missing)):
            if img:
                images[key] = img
            else:
                print(f"No logo image found for venue {key}", file=sys.stderr)
    return images


def detect_face_focus(image_url):
    """Return "x% y%" centred on the faces in an image, or None if there are
    no faces (or OpenCV isn't installed / the image can't be loaded)."""
    try:
        import cv2
        import numpy as np
    except ImportError:
        return None
    try:
        req = urllib.request.Request(image_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=OG_FETCH_TIMEOUT) as resp:
            raw = resp.read(FACE_IMAGE_MAX_BYTES)
        img = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_GRAYSCALE)
    except Exception as exc:
        print(f"Face check: could not load {image_url}: {exc}", file=sys.stderr)
        return None
    if img is None:
        return None

    h, w = img.shape[:2]
    scale = min(1.0, FACE_DETECT_MAX_SIDE / max(h, w))
    if scale < 1.0:
        img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
        h, w = img.shape[:2]
    img = cv2.equalizeHist(img)
    min_side = max(24, int(min(h, w) * 0.06))

    faces = []
    for cascade_name in ("haarcascade_frontalface_default.xml", "haarcascade_profileface.xml"):
        cascade = cv2.CascadeClassifier(os.path.join(cv2.data.haarcascades, cascade_name))
        found = cascade.detectMultiScale(img, scaleFactor=1.1, minNeighbors=6, minSize=(min_side, min_side))
        faces = [tuple(int(v) for v in f) for f in found]
        if faces:
            break
    if not faces:
        return None

    # Frame the main face(s): the largest one plus any others at least half its
    # size (e.g. a b2b duo), ignoring tiny background faces / false positives.
    largest = max(fw * fh for _, _, fw, fh in faces)
    main = [f for f in faces if f[2] * f[3] >= largest / 2]
    left = min(x for x, _, _, _ in main)
    top = min(y for _, y, _, _ in main)
    right = max(x + fw for x, _, fw, _ in main)
    bottom = max(y + fh for _, y, _, fh in main)
    cx = round(100 * (left + right) / 2 / w)
    cy = round(100 * (top + bottom) / 2 / h)
    return f"{cx}% {cy}%"


def fill_face_focus(events, venue_images):
    """Set each event's "focus" for its current flyer. Only re-checks events
    whose image changed since the focus was computed (tracked in focus_src)."""
    generic = set(venue_images.values())
    todo = [
        e for e in events
        if e.get("image") and e["image"] not in generic and e.get("focus_src") != e["image"]
    ]
    if not todo:
        return
    with ThreadPoolExecutor(OG_FETCH_WORKERS) as pool:
        results = list(pool.map(lambda e: detect_face_focus(e["image"]), todo))
    for e, focus in zip(todo, results):
        e["focus"] = focus
        e["focus_src"] = e["image"]
    print(f"Face check: found faces in {sum(1 for f in results if f)} of {len(todo)} new flyer(s).")


def needs_flyer(e, generic):
    return bool(e.get("date")) and not is_acceptable_flyer(e, e.get("image"), generic)


def fill_event_images(events, venue_images):
    """Make sure each event shows its own flyer when one exists.

    Events whose image is missing, a venue logo, or (for SeeTickets) not
    under the show's own event ID are re-checked against their ticket page,
    then against the venues' SeeTickets listing pages. Whatever is still
    missing is returned for run_image_lookup(). Recurring series are skipped."""
    generic = set(venue_images.values())
    todo = [e for e in events if needs_flyer(e, generic)]
    if not todo:
        return []
    with ThreadPoolExecutor(OG_FETCH_WORKERS) as pool:
        found = list(pool.map(find_event_flyer, todo))
    # The same image turning up for several different shows is a ticketing
    # site's generic banner, not a flyer.
    counts = {}
    for img in found:
        if img:
            counts[img] = counts.get(img, 0) + 1
    generic |= {img for img, n in counts.items() if n >= 3}

    listing = {}
    if any(seetickets_event_id(e.get("direct")) for e, img in zip(todo, found) if not img):
        with ThreadPoolExecutor(OG_FETCH_WORKERS) as pool:
            for page, _ in pool.map(fetch_html, SEETICKETS_LISTING_PAGES):
                if page:
                    listing.update(vor_images_by_event_id(page))

    filled, still_missing = 0, []
    for e, img in zip(todo, found):
        if not is_acceptable_flyer(e, img, generic):
            img = listing.get(seetickets_event_id(e.get("direct")) or "")
        if is_acceptable_flyer(e, img, generic):
            e["image"] = img
            filled += 1
        else:
            e["image"] = None  # stored as null; build_events_js shows the venue logo
            still_missing.append(e)
    print(f"Filled {filled} of {len(todo)} event flyer(s) from ticket and listing pages.")
    return still_missing


GENRE_LOOKUP_SYSTEM_PROMPT = f"""You classify electronic music acts playing in Dallas-Fort Worth.
For each numbered act, decide which ONE of these genres best describes what they play NOW:
{", ".join(MAIN_GENRES)}.

Be analytical: search the artist and weigh their releases, tour billing and DJ sets from roughly the
last two years over older hits or how they were known years ago. Use the event name for context
(e.g. a "(DJ Set)" or a festival lineup). If an act truly spans two, pick the one their current
headline sets lean toward. Answer with a genre from the list exactly as written.

Your final message must contain ONLY a JSON object between <genres_json> and </genres_json>:
<genres_json>{{"results": [{{"i": 0, "genre": "Bass"}}]}}</genres_json>
Keep it compact (no indentation)."""


def run_genre_lookup(client, events_vague):
    """Dedicated pass for events whose research label was too vague to map
    (e.g. "Electronic / Electropop"). Returns {index: genre}; None on failure."""
    if not events_vague:
        return {}
    listing = "\n".join(
        f'{i}. "{e["artist"]}" at {VENUES.get(e["venue"], {}).get("name", e["venue"])}, {e.get("date")}'
        f' (research labeled it "{e.get("genre")}")'
        for i, e in enumerate(events_vague)
    )
    messages = [{"role": "user", "content": f"Classify these {len(events_vague)} acts:\n\n{listing}"}]
    tools = [{"type": "web_search_20250305", "name": "web_search", "max_uses": min(30, len(events_vague) * 3)}]
    for _ in range(8):
        try:
            response = tracked_create(
                "genre_lookup",
                client,
                model=MODEL,
                max_tokens=MAX_TOKENS_PER_TURN,
                output_config={"effort": RESEARCH_EFFORT},
                system=GENRE_LOOKUP_SYSTEM_PROMPT,
                messages=messages,
                tools=tools,
                cache_control={"type": "ephemeral"},
            )
        except Exception as exc:
            print(f"Genre lookup pass hit an API error, skipping (non-fatal): {exc}", file=sys.stderr)
            return None
        if response.stop_reason == "pause_turn":
            messages.append({"role": "assistant", "content": response.content})
            continue
        text = "".join(b.text for b in response.content if getattr(b, "type", None) == "text")
        match = re.search(r"<genres_json>(.*?)</genres_json>", text, re.S)
        if not match:
            print("Genre lookup pass did not return a parseable result, skipping (non-fatal).", file=sys.stderr)
            return None
        try:
            parsed = json.loads(match.group(1).strip())
        except Exception as exc:
            print(f"Genre lookup pass returned invalid JSON, skipping (non-fatal): {exc}", file=sys.stderr)
            return None
        return {
            r["i"]: r["genre"] for r in parsed.get("results", [])
            if isinstance(r.get("i"), int) and r.get("genre") in MAIN_GENRES
        }
    print("Genre lookup pass exceeded max turns, skipping (non-fatal).", file=sys.stderr)
    return None


IMAGE_LOOKUP_SYSTEM_PROMPT = """You find the official promotional flyer image for specific
events. For each numbered event, use web_fetch on its ticket URL (and the venue's own event page
if needed) and return the URL of THAT event's flyer/artwork image, copied exactly from the fetched
content -- never constructed or guessed. SeeTickets shows (wl.seetickets.us/event/<name>/<id>)
host their flyer at https://cdn.vor.us/event/<id>/... using the same numeric <id>. Never return a
venue logo, a generic site banner, or another event's image; use null if you can't find the real one.

Your final message must contain ONLY a JSON object between <images_json> and </images_json>:
<images_json>{"results": [{"i": 0, "image": "https://... or null"}]}</images_json>
Keep it compact (no indentation)."""


def run_image_lookup(client, events_missing):
    """Dedicated pass, using the model's web_fetch (which can read ticket pages
    that block plain scripted requests), for event flyers fill_event_images()
    couldn't find. Returns {index: image url}; failures are non-fatal."""
    if not events_missing:
        return {}
    listing = "\n".join(
        f'{i}. "{e["artist"]}" at {VENUES.get(e["venue"], {}).get("name", e["venue"])}, {e.get("date")} -- {e.get("direct")}'
        for i, e in enumerate(events_missing)
    )
    messages = [{"role": "user", "content": f"Find the flyer image for these {len(events_missing)} events:\n\n{listing}"}]
    tools = [
        {"type": "web_search_20250305", "name": "web_search", "max_uses": 20},
        {"type": "web_fetch_20250910", "name": "web_fetch", "max_uses": min(80, len(events_missing) * 2 + 10), "max_content_tokens": 6000},
    ]
    accumulated_text = ""
    for _ in range(10):
        try:
            response = tracked_create(
                "image_lookup",
                client,
                model=MODEL,
                max_tokens=MAX_TOKENS_PER_TURN,
                output_config={"effort": LOOKUP_EFFORT},
                system=IMAGE_LOOKUP_SYSTEM_PROMPT,
                messages=messages,
                tools=tools,
                cache_control={"type": "ephemeral"},
            )
        except Exception as exc:
            print(f"Image lookup pass hit an API error, skipping (non-fatal): {exc}", file=sys.stderr)
            return None
        turn_text = "".join(b.text for b in response.content if getattr(b, "type", None) == "text")
        if response.stop_reason == "pause_turn":
            messages.append({"role": "assistant", "content": response.content})
            continue
        if response.stop_reason == "max_tokens":
            accumulated_text += turn_text
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": (
                "Continue exactly where you left off without repeating anything, and still end "
                "with the closing </images_json> tag once complete."
            )})
            continue
        match = re.search(r"<images_json>(.*?)</images_json>", accumulated_text + turn_text, re.S)
        if not match:
            print("Image lookup pass did not return a parseable result, skipping (non-fatal).", file=sys.stderr)
            return None
        try:
            parsed = json.loads(match.group(1).strip())
        except Exception as exc:
            print(f"Image lookup pass returned invalid JSON, skipping (non-fatal): {exc}", file=sys.stderr)
            return None
        return {r["i"]: r["image"] for r in parsed.get("results", []) if isinstance(r.get("i"), int) and r.get("image")}
    print("Image lookup pass exceeded max turns, skipping (non-fatal).", file=sys.stderr)
    return None


def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ANTHROPIC_API_KEY is not set", file=sys.stderr)
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)
    data = run_research(client)

    if not data.get("events"):
        print("No events returned, refusing to overwrite events.js with an empty file", file=sys.stderr)
        sys.exit(1)

    today_str = date.today().isoformat()
    previous_events = load_previous_events()
    data["events"] = merge_with_previous(data["events"], previous_events, today_str)
    data["events"] = combine_coba_recurring(data["events"])
    data["venue_images"] = venue_logo_images()
    missing = fill_event_images(data["events"], data["venue_images"])
    skipped = [e for e in missing if checked_recently(e, "image_checked", IMAGE_LOOKUP_RECHECK_DAYS, today_str)]
    missing = [e for e in missing if not checked_recently(e, "image_checked", IMAGE_LOOKUP_RECHECK_DAYS, today_str)]
    if skipped:
        print(f"Skipping image lookup for {len(skipped)} event(s) already searched in the last {IMAGE_LOOKUP_RECHECK_DAYS} days.")
    if missing:
        print(f"Running dedicated image lookup pass for {len(missing)} event(s) still missing a flyer...")
        generic = set(data["venue_images"].values())
        found = 0
        results = run_image_lookup(client, missing)
        if results is None:
            results = {}
            missing = []  # pass failed: don't mark these as checked
        for i, img in results.items():
            if 0 <= i < len(missing) and is_acceptable_flyer(missing[i], img, generic):
                missing[i]["image"] = img
                found += 1
        for e in missing:
            if not e.get("image"):
                e["image_checked"] = today_str
        print(f"Image lookup pass found {found} of {len(missing)} missing flyer(s).")
    fill_face_focus(data["events"], data["venue_images"])
    data["events"] = dedupe_events(data["events"], set(data["venue_images"].values()))
    # Genres: hand overrides win; vague research labels get a dedicated,
    # artist-by-artist check instead of a blind default; everything else maps
    # to its main genre.
    vague = [
        e for e in data["events"]
        if not override_genre(e.get("artist")) and specific_genre(e.get("genre")) is None
    ]
    if vague:
        print(f"Running genre lookup for {len(vague)} event(s) with a vague genre label...")
        for i, genre in (run_genre_lookup(client, vague) or {}).items():
            if 0 <= i < len(vague):
                vague[i]["genre"] = genre
    for e in data["events"]:
        e["genre"] = override_genre(e.get("artist")) or main_genre(e.get("genre"))

    cutoff_str = (date.today() + timedelta(days=STUBHUB_LOOKUP_WINDOW_DAYS)).isoformat()
    needs_lookup = [
        e for e in data["events"]
        if not e.get("stubhub") and e.get("date") and today_str <= e["date"] <= cutoff_str
        and e.get("free") is not True
        and not checked_recently(e, "stubhub_checked", STUBHUB_RECHECK_DAYS, today_str)
    ]
    recently_checked = sum(
        1 for e in data["events"]
        if not e.get("stubhub") and checked_recently(e, "stubhub_checked", STUBHUB_RECHECK_DAYS, today_str)
    )
    if recently_checked:
        print(f"Skipping StubHub lookup for {recently_checked} event(s) already searched in the last {STUBHUB_RECHECK_DAYS} days.")
    if needs_lookup:
        print(
            f"Running dedicated StubHub lookup pass for {len(needs_lookup)} event(s) within "
            f"{STUBHUB_LOOKUP_WINDOW_DAYS} days..."
        )
        results = run_stubhub_lookup(client, needs_lookup)
        if results is None:
            results = {}
            needs_lookup = []  # pass failed: don't mark these as checked
        for i, url in results.items():
            if 0 <= i < len(needs_lookup):
                needs_lookup[i]["stubhub"] = url
        for e in needs_lookup:
            if not e.get("stubhub"):
                e["stubhub_checked"] = today_str
        found = sum(1 for e in needs_lookup if e.get("stubhub"))
        print(f"StubHub lookup pass found {found} link(s) out of {len(needs_lookup)} near-term event(s) checked.")

    js = build_events_js(data)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(js)

    with open(EVENTS_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(
            {"last_updated": data.get("last_updated", today_str), "events": data["events"]},
            f,
            ensure_ascii=False,
            indent=None,
        )

    print(f"Wrote {len(data['events'])} events to {OUTPUT_PATH}")
    print_usage_summary()


if __name__ == "__main__":
    main()
