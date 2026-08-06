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

import json
import os
import re
import sys
from datetime import date

import anthropic

MODEL = "claude-sonnet-5"
OUTPUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "events.js")

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
}

VENUE_FALLBACK_IMAGES = {
    "silo": "https://silodallas.com/og-image.png",
    "ductwork": "https://cdn.vor.us/images/white-label/disco-donnie/2025/silo.png",
    "itlldo": "https://static1.squarespace.com/static/687877d212aabf1aafc5c893/t/687883bae925b43e83551a43/1752728506887/_ITLLDOCLUB.png?format=1500w",
    "greenelephant": "https://static.wixstatic.com/media/608a53_4a8795eff0ef4c958d80635f6a0fd54a~mv2.jpg/v1/fit/w_480,h_641,q_90,enc_avif,quality_auto/608a53_4a8795eff0ef4c958d80635f6a0fd54a~mv2.jpg",
}

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
4. For each event, capture: artist/event name, date (YYYY-MM-DD), time, a short genre label, and the
   direct ticket purchase URL (the venue's own primary ticket link, not a resale site).
5. For each event, try to find a promotional image: visit the individual ticket page and look for an
   og:image meta tag or the event's featured artwork. If you cannot find one, leave image as null --
   the script will apply a venue fallback image automatically.
6. If a venue currently has zero electronic/dance events on sale after this artist-by-artist check,
   do not include it in "events" -- instead add a one-sentence note about it to "monitored_notes"
   (e.g. "No EDM/house shows currently on sale; recent bookings have been rock/comedy. Checked
   weekly."). Do not add this note just because the venue's page labels shows generically -- only
   after checking each listed act.
7. Do not guess or invent events, dates, or URLs. Only include what you can verify by visiting the
   actual page. If a venue's page fails to load or is ambiguous, add it to monitored_notes instead of
   guessing.

OUTPUT FORMAT:
Respond with ONLY a single JSON object between <events_json> and </events_json> tags, no other text
outside those tags. Do not include markdown code fences inside the tags. Structure:

<events_json>
{{
  "last_updated": "YYYY-MM-DD",
  "events": [
    {{
      "artist": "string",
      "venue": "one of the venue keys above",
      "date": "YYYY-MM-DD or null for recurring/undated series",
      "time": "string, e.g. '9:00 PM'",
      "genre": "short string, e.g. 'House' or 'Techno' or 'Bass / Trap'",
      "direct": "https://... direct ticket URL",
      "image": "https://... or null",
      "recurring": "optional string, only for undated recurring series like weekly nights"
    }}
  ],
  "monitored_notes": {{
    "venue_key": "one sentence explaining why this venue has no listed events right now"
  }}
}}
</events_json>

Be thorough but only include venue keys you actually checked. Today's date will be given in the user message.
"""


def build_tools():
    return [
        {"type": "web_search_20250305", "name": "web_search", "max_uses": 60},
        {"type": "web_fetch_20250910", "name": "web_fetch", "max_uses": 60},
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

    for _ in range(8):
        response = client.messages.create(
            model=MODEL,
            max_tokens=8000,
            system=SYSTEM_PROMPT,
            messages=messages,
            tools=tools,
        )

        if response.stop_reason == "pause_turn":
            messages.append({"role": "assistant", "content": response.content})
            continue

        final_text = "".join(
            block.text for block in response.content if getattr(block, "type", None) == "text"
        )
        match = re.search(r"<events_json>(.*?)</events_json>", final_text, re.S)
        if not match:
            raise RuntimeError("Model did not return an <events_json> block. Raw text:\n" + final_text)
        return json.loads(match.group(1).strip())

    raise RuntimeError("Exceeded max turns without a final answer")


def js_str(value):
    if value is None:
        return "null"
    return json.dumps(value, ensure_ascii=False)


def build_events_js(data: dict) -> str:
    events = data["events"]
    monitored_notes = data.get("monitored_notes", {})
    last_updated = data.get("last_updated", date.today().isoformat())

    for e in events:
        if not e.get("image"):
            fallback = VENUE_FALLBACK_IMAGES.get(e["venue"])
            if fallback:
                e["image"] = fallback

    lines = []
    lines.append(f'const LAST_UPDATED = "{last_updated}";')
    lines.append("")
    lines.append("const VENUES = {")
    for key, v in VENUES.items():
        parts = [f'name: {js_str(v["name"])}', f'address: {js_str(v["address"])}', f'site: {js_str(v["site"])}']
        if v.get("closed"):
            parts.append("closed: true")
        lines.append(f'  "{key}": {{ {", ".join(parts)} }},')
    lines.append("};")
    lines.append("")
    lines.append(
        "function resale(artist, venueCity) {\n"
        "  const q = encodeURIComponent(`${artist} ${venueCity}`);\n"
        "  return [\n"
        '    { site: "SeatGeek", url: `https://seatgeek.com/search?search=${q}` },\n'
        '    { site: "Vivid Seats", url: `https://www.vividseats.com/search?searchTerm=${q}` }\n'
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
            f'image: {js_str(e.get("image"))}'
        )
        if e.get("recurring"):
            obj += f', recurring: {js_str(e["recurring"])}'
        obj += f', resale: resale({js_str(e["artist"])}, {js_str(venue_name)}) }},'
        lines.append(obj)
    lines.append("];")
    lines.append("")

    monitored_keys = [k for k in VENUES if not VENUES[k].get("closed") and k in monitored_notes]
    lines.append("const MONITORED_NO_CURRENT_EVENTS = [")
    lines.append("  " + ", ".join(js_str(k) for k in monitored_keys))
    lines.append("];")
    lines.append("")
    lines.append("const MONITORED_NOTES = {")
    for k in monitored_keys:
        lines.append(f"  {k}: {js_str(monitored_notes[k])},")
    lines.append("};")
    lines.append("")
    lines.append(f'const CLOSED_VENUES_NOTE = {js_str(CLOSED_VENUES_NOTE)};')
    lines.append("")
    return "\n".join(lines)


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

    js = build_events_js(data)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(js)

    print(f"Wrote {len(data['events'])} events to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
