// DFW EDM Events data
// Auto-refreshed weekly by a scheduled Claude task. Last updated: 2026-08-04
// To update: replace this file's EVENTS array and re-upload to GitHub.

const LAST_UPDATED = "2026-08-04";

const VENUES = {
  "silo": { name: "SILO Dallas", address: "1340 Manufacturing St, Dallas, TX", site: "https://silodallas.com/events" },
  "itlldo": { name: "It'll Do Club", address: "4322 Elm St, Dallas, TX", site: "https://www.itlldoclub.com/" },
  "ctrlroom": { name: "CTRL Room Dallas", address: "2511 Swiss Ave, Dallas, TX", site: "https://www.ctrlroomdallas.com/events" },
  "ductwork": { name: "Ductwork at SILO", address: "1340 Manufacturing St, Dallas, TX", site: "https://linktr.ee/ductworkdallas" },
  "bombfactory": { name: "The Bomb Factory", address: "2713 Canton St, Dallas, TX", site: "https://thebombfactory.com/" },
  "studiofactory": { name: "The Studio at The Factory", address: "2727 Canton St, Dallas, TX", site: "https://www.thefactoryindeepellum.com/" },
  "greenelephant": { name: "Green Elephant", address: "5627 Dyer St, Dallas, TX", site: "https://www.greenelephantdallas.com/blank" },
  "sounders": { name: "Sounders", address: "1211 E Levee St, Dallas, TX", site: "https://soundersdallas.com/" },
  "stereolive": { name: "Stereo Live Dallas", address: "2711 Storey Ln, Dallas, TX", site: "https://stereolive.com/", closed: true },
  "deepellumartco": { name: "Deep Ellum Art Co", address: "3200 Commerce St, Dallas, TX", site: "https://deepellumart.co/" },
  "toyotamusic": { name: "Toyota Music Factory (The Pavilion)", address: "300 W Las Colinas Blvd, Irving, TX", site: "https://www.thepaviliontmf.com/" },
  "dosequis": { name: "Dos Equis Pavilion", address: "3839 S Fitzhugh Ave, Dallas, TX", site: "https://www.dosequispavilion.com/" },
  "dickies": { name: "Dickies Arena", address: "1911 Montgomery St, Fort Worth, TX", site: "https://dickiesarena.com/" },
  "fairpark": { name: "Fair Park Dallas (Festival)", address: "1300 Robert B Cullum Blvd, Dallas, TX", site: "https://lightsallnight.com/" },
  "coba": { name: "Coba (After Hours)", address: "2800 Canton St, Dallas, TX", site: "https://www.cobadallas.com/" }
};

function resale(artist, venueCity) {
  const q = encodeURIComponent(`${artist} ${venueCity}`);
  return [
    { site: "StubHub", url: `https://www.stubhub.com/find?q=${q}` },
    { site: "Vivid Seats", url: `https://www.vividseats.com/search?searchTerm=${q}` }
  ];
}

const EVENTS = [
  // ---- SILO Dallas ----
  { artist: "Noizu", venue: "silo", date: "2026-08-07", time: "9:00 PM", genre: "House", direct: "https://wl.seetickets.us/event/Noizu-DALLAS/688163?afflky=SILO", resale: resale("Noizu", "Dallas") },
  { artist: "DJ Pauly D", venue: "silo", date: "2026-08-08", time: "9:00 PM", genre: "EDM", direct: "https://wl.seetickets.us/event/DJ-Pauly-D-DALLAS/689157?afflky=SILO", resale: resale("DJ Pauly D", "Dallas") },
  { artist: "Black Tiger Sex Machine", venue: "silo", date: "2026-08-14", time: "9:00 PM", genre: "Bass/Dubstep", direct: "https://wl.seetickets.us/event/Black-Tiger-Sex-Machine-DALLAS/688827?afflky=SILO", resale: resale("Black Tiger Sex Machine", "Dallas") },
  { artist: "Audien — Progressive House Never Died", venue: "silo", date: "2026-08-15", time: "9:00 PM", genre: "Progressive House", direct: "https://wl.seetickets.us/event/PROGRESSIVE-HOUSE-NEVER-DIED-AUDIEN-DALLAS/690226?afflky=SILO", resale: resale("Audien", "Dallas") },
  { artist: "NGHTMRE", venue: "silo", date: "2026-08-21", time: "9:00 PM", genre: "Bass", direct: "https://wl.seetickets.us/event/NGHTMRE-DALLAS/689703?afflky=SILO", resale: resale("NGHTMRE", "Dallas") },
  { artist: "Dr. Fresch — The Bass Operation", venue: "silo", date: "2026-08-22", time: "9:00 PM", genre: "Bass House", direct: "https://wl.seetickets.us/event/DR-FRESCH-PRESENTS-THE-BASS-OPERATION-DALLAS/667517?afflky=SILO", resale: resale("Dr. Fresch", "Dallas") },
  { artist: "ATLiens", venue: "silo", date: "2026-08-28", time: "9:00 PM", genre: "Bass", direct: "https://wl.seetickets.us/event/ATLiens-DALLAS/693872?afflky=SILO", resale: resale("ATLiens", "Dallas") },
  { artist: "Acraze", venue: "silo", date: "2026-08-29", time: "9:00 PM", genre: "House", direct: "https://wl.seetickets.us/event/ACRAZE-DALLAS/691230?afflky=SILO", resale: resale("Acraze", "Dallas") },
  { artist: "I Hate Models", venue: "silo", date: "2026-09-04", time: "9:00 PM", genre: "Techno", direct: "https://wl.seetickets.us/event/I-Hate-Models-DALLAS/691508?afflky=SILO", resale: resale("I Hate Models", "Dallas") },
  { artist: "Ian Asher", venue: "silo", date: "2026-09-05", time: "9:00 PM", genre: "EDM", direct: "https://wl.seetickets.us/event/Ian-Asher-DALLAS/691856?afflky=SILO", resale: resale("Ian Asher", "Dallas") },
  { artist: "Galantis", venue: "silo", date: "2026-09-06", time: "9:00 PM", genre: "Electro Pop/EDM", direct: "https://wl.seetickets.us/event/Galantis-DALLAS/698482?afflky=SILO", resale: resale("Galantis", "Dallas") },
  { artist: "Oguz", venue: "silo", date: "2026-09-06", time: "9:00 PM", genre: "Melodic Techno", direct: "https://wl.seetickets.us/event/OGUZ-DALLAS/692303?afflky=SILO", resale: resale("Oguz", "Dallas") },
  { artist: "Gareth Emery — LSR/CITY X", venue: "silo", date: "2026-09-11", time: "9:00 PM", genre: "Trance", direct: "https://wl.seetickets.us/event/LSRCITY-X-by-Gareth-Emery-DALLAS/690277?afflky=SILO", resale: resale("Gareth Emery", "Dallas") },
  { artist: "Indo Warehouse", venue: "silo", date: "2026-09-12", time: "9:00 PM", genre: "House/Techno", direct: "https://wl.seetickets.us/event/INDO-WAREHOUSE-DALLAS/695177?afflky=SILO", resale: resale("Indo Warehouse", "Dallas") },
  { artist: "Swimming Paul", venue: "silo", date: "2026-09-18", time: "9:00 PM", genre: "House", direct: "https://wl.seetickets.us/event/Swimming-Paul-DALLAS/695230?afflky=SILO", resale: resale("Swimming Paul", "Dallas") },
  { artist: "TroyBoi — Hear2Move", venue: "silo", date: "2026-09-19", time: "9:00 PM", genre: "Bass", direct: "https://wl.seetickets.us/event/TroyBoi-Hear2Move-DALLAS/697913?afflky=SILO", resale: resale("TroyBoi", "Dallas") },
  { artist: "DJ Diesel (Shaquille O'Neal)", venue: "silo", date: "2026-09-20", time: "7:00 PM", genre: "Bass/EDM", direct: "https://wl.seetickets.us/event/DJ-Diesel-DALLAS/699111?afflky=SILO", resale: resale("DJ Diesel", "Dallas") },
  { artist: "Holy Priest", venue: "silo", date: "2026-09-24", time: "9:00 PM", genre: "Techno", direct: "https://wl.seetickets.us/event/Holy-Priest-DALLAS/694030?afflky=SILO", resale: resale("Holy Priest", "Dallas") },
  { artist: "Zack Fox", venue: "silo", date: "2026-09-26", time: "9:00 PM", genre: "Electronic/DJ", direct: "https://wl.seetickets.us/event/Zack-Fox-DALLAS/693394?afflky=SILO", resale: resale("Zack Fox", "Dallas") },
  { artist: "Eli Brown", venue: "silo", date: "2026-10-02", time: "9:00 PM", genre: "Tech House", direct: "https://wl.seetickets.us/event/ELI-BROWN-DALLAS/696655?afflky=SILO", resale: resale("Eli Brown", "Dallas") },
  { artist: "Sasha & John Digweed — SILO 2 Year Anniversary", venue: "silo", date: "2026-10-03", time: "9:00 PM", genre: "Progressive House", direct: "https://wl.seetickets.us/event/Sasha-and-John-Digweed-SILO-2-Year-Anniversary-DALLAS/692671?afflky=SILO", resale: resale("Sasha John Digweed", "Dallas") },
  { artist: "Bob Moses (club set)", venue: "silo", date: "2026-10-16", time: "9:00 PM", genre: "House", direct: "https://wl.seetickets.us/event/Bob-Moses-club-set-DALLAS/700129?afflky=SILO", resale: resale("Bob Moses", "Dallas") },
  { artist: "Odd Mob", venue: "silo", date: "2026-10-17", time: "9:00 PM", genre: "Bass House", direct: "https://wl.seetickets.us/event/ODD-MOB-DALLAS/694826?afflky=SILO", resale: resale("Odd Mob", "Dallas") },
  { artist: "Kettama", venue: "silo", date: "2026-10-23", time: "9:00 PM", genre: "Tech House", direct: "https://wl.seetickets.us/event/KETTAMA-DALLAS/691502?afflky=SILO", resale: resale("Kettama", "Dallas") },

  // ---- It'll Do Club ----
  { artist: "Datsko", venue: "itlldo", date: "2026-08-07", time: "9:00 PM", genre: "House", direct: "https://www.eventbrite.com/e/datsko-at-itll-do-club-tickets-1989420894449", resale: resale("Datsko", "Dallas Itll Do Club") },
  { artist: "Luke Alessi", venue: "itlldo", date: "2026-08-08", time: "9:00 PM", genre: "House", direct: "https://www.eventbrite.com/e/luke-alessi-at-itll-do-club-tickets-1989797526967", resale: resale("Luke Alessi", "Dallas Itll Do Club") },
  { artist: "Moon Boots", venue: "itlldo", date: "2026-08-14", time: "9:00 PM", genre: "House", direct: "https://www.eventbrite.com/e/moon-boots-at-itll-do-club-tickets-1987578928078", resale: resale("Moon Boots", "Dallas Itll Do Club") },
  { artist: "Josh Wink", venue: "itlldo", date: "2026-08-15", time: "9:00 PM", genre: "Techno/House", direct: "https://www.eventbrite.com/e/josh-wink-at-itll-do-club-tickets-1992100764011", resale: resale("Josh Wink", "Dallas Itll Do Club") },
  { artist: "HNTR", venue: "itlldo", date: "2026-08-21", time: "9:00 PM", genre: "House", direct: "https://www.eventbrite.com/e/hntr-at-itll-do-club-tickets-1989036370327", resale: resale("HNTR", "Dallas Itll Do Club") },
  { artist: "Ragie Ban", venue: "itlldo", date: "2026-08-22", time: "9:00 PM", genre: "House", direct: "https://www.eventbrite.com/e/ragie-ban-at-itll-do-club-tickets-1987945829490", resale: resale("Ragie Ban", "Dallas Itll Do Club") },
  { artist: "Loco Dice", venue: "itlldo", date: "2026-08-28", time: "9:00 PM", genre: "Techno/House", direct: "https://www.eventbrite.com/e/loco-dice-at-itll-do-club-tickets-1990509331995", resale: resale("Loco Dice", "Dallas Itll Do Club") },
  { artist: "Nora En Pure", venue: "itlldo", date: "2026-08-29", time: "9:00 PM", genre: "Deep House", direct: "https://www.eventbrite.com/e/nora-en-pure-at-itll-do-club-tickets-1990897307440", resale: resale("Nora En Pure", "Dallas Itll Do Club") },
  { artist: "ObskÜr", venue: "itlldo", date: "2026-09-04", time: "9:00 PM", genre: "Techno", direct: "https://www.eventbrite.com/e/obskur-at-itll-do-club-tickets-1987276288876", resale: resale("Obskur", "Dallas Itll Do Club") },
  { artist: "Chris Avantgarde", venue: "itlldo", date: "2026-09-05", time: "9:00 PM", genre: "Progressive House", direct: "https://www.eventbrite.com/e/chris-avantgarde-at-itll-do-club-tickets-1990995590407", resale: resale("Chris Avantgarde", "Dallas Itll Do Club") },
  { artist: "Bushbaby", venue: "itlldo", date: "2026-09-11", time: "9:00 PM", genre: "House", direct: "https://www.eventbrite.com/e/bushbaby-at-itll-do-club-tickets-1991580970294", resale: resale("Bushbaby", "Dallas Itll Do Club") },
  { artist: "The Knocks", venue: "itlldo", date: "2026-09-12", time: "9:00 PM", genre: "Electro Pop/House", direct: "https://www.eventbrite.com/e/the-knocks-at-itll-do-club-tickets-1990995973553", resale: resale("The Knocks", "Dallas Itll Do Club") },
  { artist: "Rinse FM x Ben UFO", venue: "itlldo", date: "2026-09-18", time: "9:00 PM", genre: "House/Techno", direct: "https://www.eventbrite.com/e/rinse-fm-x-ben-ufo-at-itll-do-club-tickets-1989797687447", resale: resale("Ben UFO", "Dallas Itll Do Club") },
  { artist: "Justin Martin", venue: "itlldo", date: "2026-09-19", time: "9:00 PM", genre: "House", direct: "https://www.eventbrite.com/e/justin-martin-at-itll-do-club-tickets-1988280581743", resale: resale("Justin Martin", "Dallas Itll Do Club") },
  { artist: "Jamback", venue: "itlldo", date: "2026-09-25", time: "9:00 PM", genre: "House", direct: "https://www.eventbrite.com/e/jamback-at-itll-do-club-tickets-1991319944559", resale: resale("Jamback", "Dallas Itll Do Club") },
  { artist: "Dreya V b2b Cole Knight", venue: "itlldo", date: "2026-09-26", time: "9:00 PM", genre: "House", direct: "https://www.eventbrite.com/e/dreya-v-b2b-cole-knight-at-itll-do-club-tickets-1995609780574", resale: resale("Dreya V", "Dallas Itll Do Club") },
  { artist: "Kilimanjaro", venue: "itlldo", date: "2026-10-02", time: "9:00 PM", genre: "House", direct: "https://www.eventbrite.com/e/kilimanjaro-at-itll-do-club-tickets-1993959751292", resale: resale("Kilimanjaro DJ", "Dallas Itll Do Club") },
  { artist: "Matt Sassari", venue: "itlldo", date: "2026-10-03", time: "9:00 PM", genre: "Tech House", direct: "https://www.eventbrite.com/e/matt-sassari-at-itll-do-club-tickets-1992580746652", resale: resale("Matt Sassari", "Dallas Itll Do Club") },
  { artist: "Jack Marlow", venue: "itlldo", date: "2026-10-09", time: "9:00 PM", genre: "House", direct: "https://www.eventbrite.com/e/jack-marlow-at-itll-do-club-tickets-1993480905050", resale: resale("Jack Marlow", "Dallas Itll Do Club") },
  { artist: "Biscits", venue: "itlldo", date: "2026-10-10", time: "9:00 PM", genre: "Tech House", direct: "https://www.eventbrite.com/e/biscits-at-itll-do-club-tickets-1993029460768", resale: resale("Biscits", "Dallas Itll Do Club") },
  { artist: "Tobiahs", venue: "itlldo", date: "2026-10-16", time: "9:00 PM", genre: "House", direct: "https://www.eventbrite.com/e/tobiahs-at-itll-do-club-tickets-1994878700895", resale: resale("Tobiahs", "Dallas Itll Do Club") },
  { artist: "Jazzy", venue: "itlldo", date: "2026-10-17", time: "9:00 PM", genre: "House", direct: "https://www.eventbrite.com/e/jazzy-at-itll-do-club-tickets-1990745154346", resale: resale("Jazzy DJ", "Dallas Itll Do Club") },
  { artist: "Baauer", venue: "itlldo", date: "2026-10-23", time: "9:00 PM", genre: "Trap/Bass", direct: "https://www.eventbrite.com/e/baauer-at-itll-do-club-tickets-1992533335845", resale: resale("Baauer", "Dallas Itll Do Club") },
  { artist: "Satin Jackets", venue: "itlldo", date: "2026-10-24", time: "9:00 PM", genre: "Nu-Disco/House", direct: "https://www.eventbrite.com/e/satin-jackets-at-itll-do-club-tickets-1992007118916", resale: resale("Satin Jackets", "Dallas Itll Do Club") },

  // ---- CTRL Room Dallas ----
  { artist: "Rick Wonder", venue: "ctrlroom", date: "2026-08-07", time: "10:00 PM", genre: "House", direct: "https://speakeasygo.com/CTRL-Room-Dallas/Rick-Wonder-at-CTRL-Room-8.7.26?eid=EVE-YZIN4M", resale: resale("Rick Wonder", "Dallas") },
  { artist: "Rafael Cerato", venue: "ctrlroom", date: "2026-08-08", time: "10:00 PM", genre: "Melodic Techno", direct: "https://speakeasygo.com/CTRL-Room-Dallas/Rafael-Cerato-at-CTRL-Room-8.8.26?eid=EVE-181E9V", resale: resale("Rafael Cerato", "Dallas") },
  { artist: "Haus Sundays", venue: "ctrlroom", date: "2026-08-09", time: "10:00 PM", genre: "House", direct: "https://speakeasygo.com/CTRL-Room-Dallas/Haus-Sundays-8.9.26?eid=EVE-OBA65L", resale: resale("Haus Sundays", "Dallas CTRL Room") },
  { artist: "Local Access", venue: "ctrlroom", date: "2026-08-14", time: "10:00 PM", genre: "House", direct: "https://speakeasygo.com/CTRL-Room-Dallas/Local-Access-at-CTRL-Room-8.14.26?eid=EVE-GUKQ1E", resale: resale("Local Access", "Dallas CTRL Room") },
  { artist: "WAKYIN", venue: "ctrlroom", date: "2026-08-15", time: "10:00 PM", genre: "House", direct: "https://speakeasygo.com/CTRL-Room-Dallas/WAKYIN-at-CTRL-Room-8.15.26?eid=EVE-WASUCS", resale: resale("WAKYIN", "Dallas") },
  { artist: "Haus Sundays", venue: "ctrlroom", date: "2026-08-16", time: "10:00 PM", genre: "House", direct: "https://speakeasygo.com/CTRL-Room-Dallas/Haus-Sundays-8.16.26?eid=EVE-1T3LUS", resale: resale("Haus Sundays", "Dallas CTRL Room") },
  { artist: "BONTAN", venue: "ctrlroom", date: "2026-08-22", time: "10:00 PM", genre: "Melodic House", direct: "https://speakeasygo.com/CTRL-Room-Dallas/BONTAN-at-CTRL-Room-8.22.26?eid=EVE-BJHZLH", resale: resale("Bontan", "Dallas") },
  { artist: "Haus Sundays", venue: "ctrlroom", date: "2026-08-23", time: "10:00 PM", genre: "House", direct: "https://speakeasygo.com/CTRL-Room-Dallas/Haus-Sundays-8.23.26?eid=EVE-OYPD6B", resale: resale("Haus Sundays", "Dallas CTRL Room") },
  { artist: "Zillamatic", venue: "ctrlroom", date: "2026-08-28", time: "10:00 PM", genre: "House", direct: "https://speakeasygo.com/CTRL-Room-Dallas/Zillamatic-at-CTRL-Room-8.28.26?eid=EVE-0S55NU", resale: resale("Zillamatic", "Dallas") },
  { artist: "LOCKLEAD", venue: "ctrlroom", date: "2026-09-04", time: "10:00 PM", genre: "Techno", direct: "https://speakeasygo.com/CTRL-Room-Dallas/LOCKLEAD-at-CTRL-Room-9.4.26?eid=EVE-LKQRVZ", resale: resale("Locklead", "Dallas") },
  { artist: "Joshwa", venue: "ctrlroom", date: "2026-09-05", time: "10:00 PM", genre: "Tech House", direct: "https://speakeasygo.com/CTRL-Room-Dallas/Joshwa-at-CTRL-Room-9.5.26?eid=EVE-RU66OE", resale: resale("Joshwa", "Dallas") },
  { artist: "OGUZ", venue: "ctrlroom", date: "2026-09-06", time: "9:00 PM", genre: "Melodic Techno", direct: "https://speakeasygo.com/CTRL-Room-Dallas/OGUZ-at-CTRL-Room-9.6.26?eid=EVE-KXKDLB", resale: resale("Oguz", "Dallas CTRL Room") },
  { artist: "EVAN GIIA", venue: "ctrlroom", date: "2026-09-11", time: "10:00 PM", genre: "House", direct: "https://speakeasygo.com/CTRL-Room-Dallas/EVAN-GIIA-at-CTRL-Room-9.11.26?eid=EVE-KJZYL9", resale: resale("Evan Giia", "Dallas") },
  { artist: "DARCO", venue: "ctrlroom", date: "2026-09-12", time: "10:00 PM", genre: "House", direct: "https://speakeasygo.com/CTRL-Room-Dallas/DARCO-at-CTRL-Room-9.12.26?eid=EVE-1N1XR5", resale: resale("Darco", "Dallas") },
  { artist: "Fleur Shore", venue: "ctrlroom", date: "2026-09-18", time: "10:00 PM", genre: "House", direct: "https://speakeasygo.com/CTRL-Room-Dallas/Fleur-Shore-at-CTRL-Room-9.18.26?eid=EVE-TDTO9D", resale: resale("Fleur Shore", "Dallas") },
  { artist: "Benjamin Lloyd", venue: "ctrlroom", date: "2026-09-19", time: "10:00 PM", genre: "House", direct: "https://speakeasygo.com/CTRL-Room-Dallas/Benjamin-Lloyd-at-CTRL-Room-9.19.26?eid=EVE-ICGQTJ", resale: resale("Benjamin Lloyd", "Dallas") },
  { artist: "Skream", venue: "ctrlroom", date: "2026-09-25", time: "10:00 PM", genre: "Dubstep/House", direct: "https://speakeasygo.com/CTRL-Room-Dallas/Skream-at-CTRL-Room-9.25.26?eid=EVE-WCBFQV", resale: resale("Skream", "Dallas") },
  { artist: "GABSS", venue: "ctrlroom", date: "2026-10-02", time: "10:00 PM", genre: "House", direct: "https://speakeasygo.com/CTRL-Room-Dallas/GABSS-at-CTRL-Room-10.2.26?eid=EVE-ZBQUB5", resale: resale("Gabss", "Dallas") },
  { artist: "BRADEAZY", venue: "ctrlroom", date: "2026-10-17", time: "10:00 PM", genre: "House", direct: "https://speakeasygo.com/CTRL-Room-Dallas/BRADEAZY-at-CTRL-Room-10.17.26?eid=EVE-TLTU2O", resale: resale("Bradeazy", "Dallas") },
  { artist: "Classmatic", venue: "ctrlroom", date: "2026-10-24", time: "10:00 PM", genre: "House", direct: "https://speakeasygo.com/CTRL-Room-Dallas/Classmatic-at-CTRL-Room-10.24.26?eid=EVE-E8O8HF", resale: resale("Classmatic", "Dallas") },
  { artist: "OMRI.", venue: "ctrlroom", date: "2026-11-13", time: "10:00 PM", genre: "House", direct: "https://speakeasygo.com/CTRL-Room-Dallas/OMRI.-at-CTRL-Room-11.13.26?eid=EVE-XRUS06", resale: resale("Omri", "Dallas") },

  // ---- Ductwork at SILO ----
  { artist: "MeSo", venue: "ductwork", date: "2026-08-06", time: "9:00 PM", genre: "Techno", direct: "https://wl.seetickets.us/event/MeSo-DALLAS/698570?afflky=DiscoPresents-Ductwork", resale: resale("MeSo", "Dallas") },
  { artist: "Gravedgr", venue: "ductwork", date: "2026-08-13", time: "9:00 PM", genre: "Bass/Techno", direct: "https://wl.seetickets.us/event/GRAVEDGR-DALLAS/693876?afflky=DiscoPresents-Ductwork", resale: resale("Gravedgr", "Dallas") },
  { artist: "Rebuke", venue: "ductwork", date: "2026-08-20", time: "9:00 PM", genre: "Techno", direct: "https://wl.seetickets.us/event/REBUKE-DALLAS/691745?afflky=DiscoPresents-Ductwork", resale: resale("Rebuke", "Dallas") },
  { artist: "Morgan Page", venue: "ductwork", date: "2026-08-23", time: "5:00 PM", genre: "House/EDM", direct: "https://wl.seetickets.us/event/Morgan-Page-DALLAS/692381?afflky=DiscoPresents-Ductwork", resale: resale("Morgan Page", "Dallas") },
  { artist: "Feed Me", venue: "ductwork", date: "2026-08-27", time: "9:00 PM", genre: "Bass/Dubstep", direct: "https://wl.seetickets.us/event/Feed-Me-DALLAS/693234?afflky=DiscoPresents-Ductwork", resale: resale("Feed Me", "Dallas") },
  { artist: "Desert Hearts", venue: "ductwork", date: "2026-08-30", time: "7:00 PM", genre: "House/Techno", direct: "https://wl.seetickets.us/event/Desert-Hearts-DALLAS/692383?afflky=DiscoPresents-Ductwork", resale: resale("Desert Hearts", "Dallas") },
  { artist: "Infekt", venue: "ductwork", date: "2026-09-03", time: "9:00 PM", genre: "Techno", direct: "https://wl.seetickets.us/event/INFEKT-DALLAS/693880?afflky=DiscoPresents-Ductwork", resale: resale("Infekt", "Dallas") },
  { artist: "Calcium", venue: "ductwork", date: "2026-09-10", time: "9:00 PM", genre: "Techno", direct: "https://wl.seetickets.us/event/Calcium-DALLAS/694650?afflky=DiscoPresents-Ductwork", resale: resale("Calcium", "Dallas") },
  { artist: "Elijah Wood + Zach Cowie — Wooden Wisdom", venue: "ductwork", date: "2026-09-13", time: "7:00 PM", genre: "House", direct: "https://wl.seetickets.us/event/WOODEN-WISDOM-Elijah-Wood-Zach-Cowie-DALLAS/682118?afflky=DiscoPresents-Ductwork", resale: resale("Wooden Wisdom", "Dallas") },
  { artist: "Bassjackers", venue: "ductwork", date: "2026-09-17", time: "9:00 PM", genre: "Big Room/EDM", direct: "https://wl.seetickets.us/event/BASSJACKERS-DALLAS/694795?afflky=DiscoPresents-Ductwork", resale: resale("Bassjackers", "Dallas") },
  { artist: "SampliFire", venue: "ductwork", date: "2026-12-03", time: "9:00 PM", genre: "Techno", direct: "https://wl.seetickets.us/event/SampliFire-DALLAS/693792?afflky=DiscoPresents-Ductwork", resale: resale("SampliFire", "Dallas") },

  // ---- Dickies Arena (Fort Worth) — big arena show ----
  { artist: "John Summit — CTRL Escape Arena Tour", venue: "dickies", date: "2026-11-07", time: "7:00 PM", genre: "House/EDM", direct: "https://dickiesarena.com/event/2026-11-07-john-summit/", resale: [
      { site: "StubHub", url: "https://www.stubhub.com/john-summit-fort-worth-tickets-11-7-2026/event/161190829/" },
      { site: "Vivid Seats", url: "https://www.vividseats.com/john-summit-tickets-fort-worth-dickies-arena-11-8-2026/production/7096323" }
    ] },

  // ---- Festivals ----
  { artist: "Lights All Night 2026 — Tiësto, Chris Lake, Subtronics, Gryffin, Kettama, I Hate Models + more", venue: "fairpark", date: "2026-12-30", time: "TBA (2-day festival, Dec 30–31)", genre: "Festival / All Genres", direct: "https://lightsallnight.com/", resale: [
      { site: "StubHub", url: "https://www.stubhub.com/find?q=Lights+All+Night+Dallas" },
      { site: "Vivid Seats", url: "https://www.vividseats.com/search?searchTerm=Lights%20All%20Night%20Dallas" }
    ] },

  // ---- Green Elephant ----
  { artist: "Dallas DJam", venue: "greenelephant", date: "2026-08-05", time: "9:00 PM", genre: "Electronic/DJ", direct: "https://www.instagram.com/dallasdjam", resale: resale("Dallas DJam", "Dallas Green Elephant") },
  { artist: "Mighty Dux Takeover", venue: "greenelephant", date: "2026-08-07", time: "9:00 PM", genre: "House/Bass", direct: "https://events.ticketleap.com/tickets/wdd-tx/mighty-dux-takeover-at-ge", resale: resale("Mighty Dux Takeover", "Dallas Green Elephant") },
  { artist: "SUPERFUTURE'D TX 2026 (Full Grind Ent)", venue: "greenelephant", date: "2026-08-08", time: "9:00 PM", genre: "Bass/Dubstep", direct: "https://loop1tickets.com/FullGrindEnt/superfuturedtx2026/", resale: resale("Superfutured TX", "Dallas Green Elephant") },
  { artist: "BFF (Bottomfeeders)", venue: "greenelephant", date: "2026-09-05", time: "9:00 PM", genre: "Bass/Dubstep", direct: "https://www.tickettailor.com/events/bottomfeedersbff/2324106", resale: resale("Bottomfeeders BFF", "Dallas Green Elephant") },
  { artist: "Fred V", venue: "greenelephant", date: "2026-09-09", time: "9:00 PM", genre: "Drum & Bass", direct: "https://www.eventbrite.com/e/fred-v-tickets-1989276410293?aff=oddtdtcreator", resale: resale("Fred V", "Dallas Green Elephant") },

  // ---- Coba (After Hours, every Fri & Sat 2–5 AM) ----
  { artist: "Ritual Fridays", venue: "coba", date: "2026-08-07", time: "2:00 AM – 5:00 AM", genre: "House/Techno", direct: "https://www.cobadallas.com/buytickets", resale: resale("Coba Ritual Fridays", "Dallas") },
  { artist: "Voltage Saturdays", venue: "coba", date: "2026-08-08", time: "2:00 AM – 5:00 AM", genre: "House/Techno", direct: "https://www.cobadallas.com/buytickets", resale: resale("Coba Voltage Saturdays", "Dallas") },
  { artist: "Ritual Fridays", venue: "coba", date: "2026-08-14", time: "2:00 AM – 5:00 AM", genre: "House/Techno", direct: "https://www.cobadallas.com/buytickets", resale: resale("Coba Ritual Fridays", "Dallas") },
  { artist: "Voltage Saturdays", venue: "coba", date: "2026-08-15", time: "2:00 AM – 5:00 AM", genre: "House/Techno", direct: "https://www.cobadallas.com/buytickets", resale: resale("Coba Voltage Saturdays", "Dallas") },
  { artist: "Ritual at Coba After Hours", venue: "coba", date: "2026-08-21", time: "2:00 AM – 5:00 AM", genre: "House/Techno", direct: "https://www.cobadallas.com/buytickets", resale: resale("Coba Ritual Fridays", "Dallas") },
  { artist: "Voltage Saturdays", venue: "coba", date: "2026-08-22", time: "2:00 AM – 5:00 AM", genre: "House/Techno", direct: "https://www.cobadallas.com/buytickets", resale: resale("Coba Voltage Saturdays", "Dallas") },
  { artist: "Ritual Fridays", venue: "coba", date: "2026-08-28", time: "2:00 AM – 5:00 AM", genre: "House/Techno", direct: "https://www.cobadallas.com/buytickets", resale: resale("Coba Ritual Fridays", "Dallas") },
  { artist: "Voltage Saturdays", venue: "coba", date: "2026-08-29", time: "2:00 AM – 5:00 AM", genre: "House/Techno", direct: "https://www.cobadallas.com/buytickets", resale: resale("Coba Voltage Saturdays", "Dallas") }
];

// Venues being monitored with no confirmed EDM/house shows in the current window.
// They'll populate automatically once new shows are announced and the weekly refresh runs.
const MONITORED_NO_CURRENT_EVENTS = [
  "sounders",        // Active bass/techno venue running weekly series (Techno & Tequila Fridays, Riddim of the Night Saturdays, Dubstep & Dogs) — no specific dates confirmed yet for this window, check soundersdallas.com/pages/events-tickets or Instagram directly
  "bombfactory",     // Mostly indie/rock bookings currently; watched for EDM crossover shows
  "studiofactory",   // Mostly indie/rock bookings currently; watched for EDM crossover shows
  "deepellumartco",  // Mostly indie/alt bookings currently; watched for EDM crossover shows
  "toyotamusic",     // Next confirmed EDM show (Martin Garrix, May 2026) falls outside this window
  "dosequis"         // No confirmed EDM/house show in this window yet
];

const CLOSED_VENUES_NOTE = "Stereo Live Dallas closed permanently in early 2026 and is no longer booking shows. Kept here for reference only.";
