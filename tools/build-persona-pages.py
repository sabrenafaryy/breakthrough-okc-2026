#!/usr/bin/env python3
"""
Builds the five persona landing pages under website/for/.

Run from the repo root:  python3 tools/build-persona-pages.py

Shared chrome (attribution v2, pixel, nav, footer, price-switch, Lead event) is
lifted verbatim out of the live pages so these never drift from the rest of the
site. Persona copy lives in PERSONAS below — edit there, re-run, commit.

House-rule constraints baked in and NOT to be relaxed without a checker pass:
  * No panelist names (Darrell Beavers / Shannon Entz). Their appearance is
    gated on Marty's written OK — say "the expert panel".
  * Every number carries its source link and access date.
  * No attendance number. 250 is venue capacity, never attendance.
  * No investment-return promise.
  * HSP: rural open, urban set-aside paused since Aug 7 2026; 0% for 24 months
    then prime + 4%.
"""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = ROOT / "website"
OUT = SITE / "for"

SPEAKERS = (SITE / "speakers" / "index.html").read_text(encoding="utf-8")
HOME = (SITE / "index.html").read_text(encoding="utf-8")


def slice_between(src, start, end, inclusive=True):
    i = src.index(start)
    j = src.index(end, i) + (len(end) if inclusive else 0)
    return src[i:j]


# --- shared chrome, lifted verbatim -----------------------------------------
HEAD_PRE = SPEAKERS[: SPEAKERS.index('<meta charset="UTF-8" />')]
FONTS = slice_between(SPEAKERS, '<link rel="preconnect"', '/assets/style.css?v=2" />')
CLARITY = slice_between(SPEAKERS, '<script type="text/javascript">(function(c,l,a,r,i,t,y)', "</script>")
PIXEL = slice_between(SPEAKERS, "<!-- Meta Pixel Code -->", "<!-- End Meta Pixel Code -->")
TOPBAR = slice_between(HOME, '<div class="topbar">', "</div>")
NAV = slice_between(HOME, '<header class="nav">', "</header>")
# Lifted from the homepage, so it carries Home's active state. These pages sit under
# no nav item, so nothing should read as current.
NAV = NAV.replace('<a href="/" class="active">Home</a>', '<a href="/">Home</a>')
FOOTER = slice_between(HOME, "<footer>", "</footer>")
CHAT = slice_between(HOME, '<script src="https://widgets.leadconnectorhq.com/loader.js"', "</script>")
PRICE_SWITCH = slice_between(HOME, "<!-- §4 price switch", "</script>")

REG = "https://registration.breakthroughokc.com/contact-info"

# The GHL field-brief form ID. While this is None the opt-in section is OMITTED entirely —
# a 430px card wired to a dead form is worse than no card on pages taking paid spend.
# Set it to the real ID and re-run to switch the section on across all five pages.
# ⚠️ Before switching it on: the field-brief PDF names Darrell Beavers and Shannon Entz, whose
# public naming is gated on Marty's written OK. Produce an un-named variant first.
GHL_FIELD_BRIEF_FORM_ID = None
CLOUD = slice_between(SPEAKERS, '<div class="cloud">', "</div>")

# Sources. Each link must actually contain the claim it is attached to — a citation that
# does not carry the figure is worse than none. The FRED and Census links below are
# single-metro / single-city series, so they support the OKC figure ONLY: do not hang a
# national comparison on them without adding the matching national series as its own source.
SRC = {
    "pop": (
        "https://fred.stlouisfed.org/series/OKCPOP",
        "U.S. Census Bureau, Vintage 2025 estimates · accessed Aug 27, 2026",
    ),
    "price": (
        "https://fred.stlouisfed.org/series/MEDLISPRI36420",
        "Realtor.com listing data, July 2026 · accessed Aug 27, 2026",
    ),
    "rent": (
        "https://www.census.gov/quickfacts/fact/table/oklahomacitycityoklahoma/PST045225",
        "U.S. Census Bureau, ACS 2020–2024 · accessed Aug 27, 2026",
    ),
    "tif": (
        "https://www.okc.gov/files/assets/city/v/1/economic-development/documents/"
        "tax-increment-financing/fy25_annualtifreport.pdf",
        "City of OKC FY25 TIF Annual Report, as of June 30, 2025 · accessed Aug 27, 2026",
    ),
    "historic": (
        "https://oklahoma.gov/content/dam/ok/en/omes/documents/IECPresentation20241010.pdf",
        "Oklahoma Incentive Evaluation Commission, Oct 2024 (state 20% + federal 26 U.S.C. §47 20%)"
        " · accessed Aug 27, 2026",
    ),
    "hsp": (
        "https://www.ohfa.org/wp-content/uploads/2026/01/HSP-Fact-Sheets-1.pdf",
        "OHFA Housing Stability Program fact sheets, Jan 2026, plus OHFA's Aug 7, 2026 pause notice"
        " · accessed Aug 27, 2026",
    ),
    # OHFA's Aug 7 2026 notice that the HSP urban set-aside is paused. The fact sheets PDF
    # predates the pause and reads as if urban money is open, so the pause needs its own link.
    "hsp_pause": (
        "https://www.ohfa.org/2026/08/urban-set-aside-paused/",
        "OHFA notice: urban set-aside paused, Aug 7, 2026",
    ),
    # OHFA publishes all of this on the OHTF program page and the applications posted there:
    # 120% AMI on the page itself; 2% / 24 months / 95% of TDC in the posted 2024 final
    # application; the 2026 redline shows 95 struck to 90. Verified against
    # 30-Research/Verify-OHFA-2026-08-26.md, which quotes each one.
    "ohtf": (
        "https://www.ohfa.org/oklahoma-housing-trust-fund/",
        "OHFA Oklahoma Housing Trust Fund program page and the applications posted on it — "
        "120% AMI on the page; 2% / 24 months / 95% of TDC in the 2024 final application; "
        "the 2026 redline cuts 95% to 90% · accessed Aug 27, 2026",
    ),
    # The five-year recapture is the half of the flipper caveat the IEC deck does not cover.
    "recapture": (
        "https://www.law.cornell.edu/uscode/text/26/50",
        "26 U.S.C. §50(a) — five-year recapture on the rehabilitation credit · accessed Aug 27, 2026",
    ),
}

SRC_STYLE = (
    "font-family:var(--font-mono);font-size:11px;color:#6b7890;"
    "text-decoration:underline;display:inline-block;margin-top:12px"
)
STAT_STYLE = "font-family:var(--font-head);font-weight:900;font-size:34px;color:var(--navy);line-height:1"


def stat_card(stat, body, *src_keys):
    """A stat card. Pass more than one source key when a claim rests on more than one
    document — every clickable source must actually contain the thing it is cited for."""
    links = "".join(
        f'<a href="{SRC[k][0]}" target="_blank" rel="noopener" style="{SRC_STYLE}">Source: {SRC[k][1]}</a>'
        for k in src_keys
    )
    return (
        f'<div class="fcard"><div style="{STAT_STYLE}">{stat}</div>'
        f'<p style="margin-top:12px">{body}</p>{links}</div>'
    )


def plain_card(title, body):
    return f'<div class="fcard"><h3>{title}</h3><p>{body}</p></div>'


def speaker_card(slug, name, role, cred, body):
    return (
        f'<div class="spk"><div class="ph"><img src="/assets/{slug}.webp" alt="{name}" /></div>'
        f'<div class="b"><div class="r">{role}</div><h3>{name}</h3>'
        f'<div class="cred">{cred}</div><p>{body}</p></div></div>'
    )


# --- persona content ---------------------------------------------------------
# "utm" is the utm_content slug the matching ad should use.
PERSONAS = [
    {
        "slug": "buy-and-hold",
        "utm": "persona-buyhold",
        "nav": "Buy & Hold",
        "title": "For Buy & Hold Investors | Breakthrough OKC 2026",
        "desc": "You own the doors. September 26 is the day you find the money that scales them — "
                "30 verified Oklahoma funding programs and an expert panel to ask about your building.",
        "eyebrow": "// For Buy &amp; Hold Investors",
        "h1": 'You Own The Doors. The Next Ten <span class="r">Need Different Money.</span>',
        "lede": "The financing that got you your first few rentals is not the financing that gets you to sixty. "
                "September 26 maps the layer most landlords in this state have never used — and puts the people "
                "who run it in the room.",
        "problem_head": "The Wall Every Landlord Hits",
        "problems": [
            plain_card(
                "Conventional lending thins out",
                "It gets harder exactly where your portfolio starts getting interesting. The public programs "
                "built for that jump exist, and most landlords in this state have never looked at them.",
            ),
            plain_card(
                "Nobody can tell you who decides",
                "You can find a program page. What you can't find is who reads the application, what "
                "they score, and whether your project is even the right shape for it.",
            ),
            plain_card(
                "Every program has strings",
                "Rent caps, affordability periods, income limits, deed restrictions. The strings are the "
                "whole decision — and they are never on the front page.",
            ),
        ],
        "proof_head": "The Money That Works When You're Adding Doors",
        "proof_lede": "Two state programs worth knowing before your next build or substantial rehab. "
                      "<b>The Housing Stability Program funds new construction and adaptive reuse only</b> — "
                      "check the Trust Fund's own eligible-activities list, linked below, before assuming a "
                      "project qualifies. Both carry conditions worth reading before you plan around either.",
        "proof": [
            stat_card(
                "2% / 24 months",
                "The state's construction loan through the Oklahoma Housing Trust Fund reaches up to 95% of "
                "total development cost under current rules, for households up to 120% of area median income. "
                "It is a small and largely committed pool, and the posted 2026 draft would cut coverage to 90% "
                "— which is exactly why timing and application order matter.",
                "ohtf",
            ),
            stat_card(
                "0% interest",
                "The Housing Stability Program lends <b>construction</b> money at zero percent on a 24-month "
                "collateralised recourse loan — construction has to start within 180 days, and the rate goes "
                "to prime + 4% if it is not repaid in the term. <b>Rural applications are open now; the urban "
                "set-aside has been paused since Aug 7, 2026</b> until repayments replenish the fund.",
                "hsp", "hsp_pause",
            ),
            stat_card(
                "$39.7M",
                "Of the NE Renaissance TIF districts' $50M project budget, $39.7M is still unallocated per the "
                "city's own FY25 report. That is budget capacity against future increment, not cash at closing — "
                "and the distinction is worth understanding before you plan around it.",
                "tif",
            ),
        ],
        "speakers_head": "Who You'll Learn It From",
        "speakers": [
            speaker_card(
                "cameron", "Cameron Burke", "Keynote · Leverage",
                "4 companies · 75+ units · 150+ home sales/yr · Oklahoma City, OK",
                "Runs 75+ rentals alongside three other companies. His keynote is the systems and delegation "
                "that let a portfolio grow without swallowing your week.",
            ),
            speaker_card(
                "ben", "Ben Allgeyer", "Keynote · Scaling",
                "500+ deals in 8 years · all 50 states · Kansas City, MO",
                "He scaled, learned what doing it wrong costs, and rebuilt lean. He closes the day on the real "
                "price of scaling and how to build a portfolio that holds.",
            ),
        ],
        "takehome": "Bring one building or one target. Leave knowing which capital door to test first, what "
                    "deadline you're working against, and which agency to call on Monday.",
    },
    {
        "slug": "fix-and-flip",
        "utm": "persona-flip",
        "nav": "Fix & Flip",
        "title": "For Fix & Flip Investors | Breakthrough OKC 2026",
        "desc": "Everyone bidding on the same finished listing? September 26, Katie Neason teaches buying the "
                "tired building two years before the street turns.",
        "eyebrow": "// For Fix &amp; Flip Investors",
        "h1": 'Everyone Else Is Bidding <span class="r">On The Finished One.</span>',
        "lede": "Same listings, same bidders, same margin getting thinner every year. There is a different way "
                "to source, and September 26 is where it gets taught.",
        "problem_head": "Why The Margin Keeps Shrinking",
        "problems": [
            plain_card(
                "You're shopping where everyone shops",
                "Finished, listed, and visible to every investor with the same alerts you have. Competing on "
                "price is the only lever left when you're all looking at the same inventory.",
            ),
            plain_card(
                "The tired building looks like a problem",
                "It is a problem — until you can read which street turns next and what public money is already "
                "committed to turning it. Then it's the only cheap thing left.",
            ),
            plain_card(
                "You've never priced the hold",
                "Some of the buildings you pass on are worth keeping rather than selling — and the money that "
                "rewards holding is a different set of doors than the hard money you already know.",
            ),
        ],
        "proof_head": "What The Map Actually Says To A Flipper",
        "proof_lede": "Straight answer: most public housing money in this state is development and "
                      "affordable-housing finance, and a short-hold flip does not qualify for it. What the day "
                      "gives you is the map of which doors are real for you — and which one is worth changing "
                      "your exit for.",
        "proof": [
            stat_card(
                "6 people",
                "That's how many claimants statewide were approved for the historic rehab credit in 2023 — a "
                "credit worth a combined 40% of qualified rehab costs when Oklahoma's 20% is stacked with the "
                "federal 20%. <b>Read the catch before you get excited: it requires an income-producing use "
                "and carries a five-year federal recapture, so a short-hold flip forfeits it.</b> This is the "
                "number that makes people run the rehab-and-hold version of a deal for the first time.",
                "historic", "recapture",
            ),
            stat_card(
                "$39.7M",
                "Of the NE Renaissance TIF districts' $50M project budget, $39.7M is still unallocated per the "
                "city's FY25 report — budget capacity against future increment, not cash at closing. You are "
                "unlikely to tap it on a flip, but knowing where a district's boundary sits is part of reading "
                "which street turns next.",
                "tif",
            ),
            stat_card(
                "$316,450",
                "The median home listing price in the OKC metro in July 2026. A low basis is why the rehab "
                "math still works in this market — and why the margin is worth defending with better sourcing "
                "rather than a higher bid.",
                "price",
            ),
        ],
        "speakers_head": "Who You'll Learn It From",
        "speakers": [
            speaker_card(
                "katie", "Katie Neason", "Keynote · Redevelopment",
                "Downtown redeveloper · Bryan, TX",
                "She buys the tired building on the tired street two years before it turns. She opens the day "
                "teaching the Redevelopment Advantage Framework — the method, not the story.",
            ),
            speaker_card(
                "ben", "Ben Allgeyer", "Keynote · Scaling",
                "500+ deals in 8 years · all 50 states · Kansas City, MO",
                "500+ deals across all 50 states, and a hard lesson in scaling the wrong way. He closes on "
                "building a deal flow that doesn't depend on you hunting every week.",
            ),
        ],
        "takehome": "Bring one street or one building you keep driving past. Leave with the framework to read "
                    "it, an honest read on whether it is a flip or a hold, and the people to call about both.",
    },
    {
        "slug": "wholesalers",
        "utm": "persona-wholesale",
        "nav": "Wholesalers",
        "title": "For Wholesalers | Breakthrough OKC 2026",
        "desc": "You have the deal. You don't have the buyer. September 26 puts you in a room of flippers, "
                "landlords, builders and the lenders funding them — vendor floor open all day.",
        "eyebrow": "// For Wholesalers",
        "h1": 'You Have The Deal. <span class="r">You Don\'t Have The Buyer.</span>',
        "lede": "That's the whole business — and a list you haven't spoken to in a year isn't a list. "
                "September 26 is built for buyers: flippers sourcing inventory, landlords adding doors, "
                "builders looking for lots, and the lenders who fund them.",
        "problem_head": "The Only Problem You Actually Have",
        "problems": [
            plain_card(
                "Your list has gone cold",
                "Names in a spreadsheet aren't buyers. Buyers are people who took your card, remember your "
                "face, and pick up when you call about a property that fits what they told you they want.",
            ),
            plain_card(
                "You don't know what they're buying now",
                "Buy boxes move. The flipper who wanted cosmetic rehabs last year wants lots this year, and "
                "you find that out in conversation, not in a blast email.",
            ),
            plain_card(
                "The lenders decide what closes",
                "A buyer who can't fund can't close. The lenders working this metro are in the same building — "
                "knowing who actually funds what changes which deals you chase.",
            ),
        ],
        "proof_head": "Who's Actually In The Room",
        "proof_lede": "Not a number. A composition — the people who buy what you find, and the ones who fund them.",
        "proof": [
            plain_card(
                "Flippers who need inventory",
                "The whole day is built for investors sourcing their next project. Inventory is their bottleneck "
                "and you are holding it.",
            ),
            plain_card(
                "Landlords adding doors &amp; builders looking for lots",
                "Buy-and-hold operators scaling their portfolios, and builders who need dirt. Two different buy "
                "boxes, both in the room, both worth a card.",
            ),
            plain_card(
                "The lenders funding all of it",
                "A sponsor and exhibitor hall open the entire day — contractors, lenders and title people, "
                "working the floor rather than sitting through slides.",
            ),
        ],
        "speakers_head": "The Stage, Between The Handshakes",
        "speakers": [
            speaker_card(
                "katie", "Katie Neason", "Keynote · Redevelopment",
                "Downtown redeveloper · Bryan, TX",
                "Opens the day on the Redevelopment Advantage Framework — which tells you what the buyers in "
                "this room will be hunting next.",
            ),
            speaker_card(
                "cameron", "Cameron Burke", "Keynote · Leverage",
                "4 companies · 75+ units · 150+ home sales/yr · Oklahoma City, OK",
                "Runs a 150+ homes-a-year sales operation in this metro. His keynote is the marketing and "
                "systems side — directly useful if finding sellers is your other half.",
            ),
        ],
        "takehome": "Bring your buy box questions and a stack of cards. The vendor floor is open all day and the "
                    "room is built around the people who buy what you find.",
    },
    {
        "slug": "new-investors",
        "utm": "persona-new",
        "nav": "New Investors",
        "title": "New To Investing? | Breakthrough OKC 2026",
        "desc": "Where do you even find the first deal? September 26 is a full day with operators who've done "
                "it — plus the complete Oklahoma funding map with your seat.",
        "eyebrow": "// If You're New To This",
        "h1": 'Where Do You Even Find <span class="r">The First Deal?</span>',
        "lede": "September 26 puts you in a room of operators who are past deal one. You get their systems, "
                "the funding map, and a full day to ask the questions you can't Google.",
        "problem_head": "What Actually Stops People At Deal One",
        "problems": [
            plain_card(
                "Advice is everywhere and none of it is local",
                "The strategy that works in a coastal market doesn't survive contact with Oklahoma pricing, "
                "Oklahoma rents, or Oklahoma programs. Local is the only version that matters to you.",
            ),
            plain_card(
                "You don't know what you don't know",
                "Not the strategy — the mechanics. Who lends, what a deal looks like on paper, what the "
                "paperwork asks for, and which questions signal that you've done this before.",
            ),
            plain_card(
                "You've never met anyone who's done it",
                "The fastest way past deal one is proximity to people on deal fifty. That is the part a course "
                "cannot sell you and a room can.",
            ),
        ],
        "proof_head": "Why Oklahoma City, In Three Numbers",
        "proof_lede": "You don't need a thesis to start. You do need to understand the market you're starting in.",
        "proof": [
            stat_card(
                "+13,700",
                "Metro residents added in a year, 0.9% growth. More people is the demand side of every "
                "strategy you might pick.",
                "pop",
            ),
            stat_card(
                "$316,450",
                "Median home listing price in the OKC metro, July 2026 — a low entry price, which matters "
                "more on your first deal than on any deal after it.",
                "price",
            ),
            stat_card(
                "41%",
                "Of Oklahoma City households rent — the tenant pool behind any buy-and-hold strategy you're "
                "considering.",
                "rent",
            ),
        ],
        "speakers_head": "Who You'll Learn It From",
        "speakers": [
            speaker_card(
                "ben", "Ben Allgeyer", "Keynote · Scaling",
                "500+ deals in 8 years · all 50 states · Kansas City, MO",
                "He scaled, learned the hard way what doing it wrong costs, and rebuilt smaller — simpler "
                "operations, fewer moving parts, systems that surface deals without him hunting. You get the "
                "rebuilt version, the one that's already been stress-tested.",
            ),
            speaker_card(
                "katie", "Katie Neason", "Keynote · Redevelopment",
                "Downtown redeveloper · Bryan, TX",
                "She buys what nobody else can see yet. Her framework is the clearest answer in the room to "
                "\"how do I find a deal nobody's bidding on?\"",
            ),
        ],
        "takehome": "Bring the question you're most embarrassed to ask. Leave with a first capital door to test, "
                    "a timing window to work against, and the name of a person to contact next.",
    },
    {
        "slug": "out-of-state",
        "utm": "persona-oos",
        "nav": "Out-Of-State",
        "title": "For Out-Of-State Investors | Breakthrough OKC 2026",
        "desc": "You've run Oklahoma City on a spreadsheet. You've never stood in it. September 26 you meet "
                "the lenders, property managers and contractors who actually operate here.",
        "eyebrow": "// For Out-Of-State Investors",
        "h1": 'You\'ve Run Oklahoma City On A Spreadsheet. <span class="r">You\'ve Never Stood In It.</span>',
        "lede": "The numbers work from a thousand miles away. What they can't tell you is who to trust on "
                "the ground. September 26 is one Saturday in the room with the people who operate here.",
        "problem_head": "What A Spreadsheet Can't Price",
        "problems": [
            plain_card(
                "You can't tell the streets apart",
                "Two addresses a mile apart can be completely different investments. That knowledge is local, "
                "it's held by people, and it doesn't publish.",
            ),
            plain_card(
                "Your team is your whole return",
                "Property manager, contractor, lender. Out of state, those three relationships are the "
                "difference between a performing asset and a slow bleed — and you're hiring them sight unseen.",
            ),
            plain_card(
                "You're late to what's already funded",
                "Public money commits years before it shows up in a price. Reading the layer takes local "
                "context that a listing site will never give you.",
            ),
        ],
        "proof_head": "Why The Spreadsheet Keeps Pointing Here",
        "proof_lede": "Every figure below is published, dated and linked to its source — check them yourself "
                      "before you book anything.",
        "proof": [
            stat_card(
                "+13,700",
                "Metro residents added in a year, 0.9% growth. That is the demand under every rent roll "
                "you're modelling.",
                "pop",
            ),
            stat_card(
                "41%",
                "Of Oklahoma City households rent — a structurally large tenant pool, and the part of your "
                "model most sensitive to being wrong.",
                "rent",
            ),
            stat_card(
                "$316,450",
                "Median metro listing price in July 2026 — the low basis that put this market on your list "
                "in the first place.",
                "price",
            ),
        ],
        "speakers_head": "Who You'll Learn It From",
        "speakers": [
            speaker_card(
                "cameron", "Cameron Burke", "Keynote · Leverage",
                "4 companies · 75+ units · 150+ home sales/yr · Oklahoma City, OK",
                "He operates in this metro every day — flips, 75+ rentals, and a sales team doing 150+ homes a "
                "year. If you want the local operator's read, he is it.",
            ),
            speaker_card(
                "ben", "Ben Allgeyer", "Keynote · Scaling",
                "500+ deals in 8 years · all 50 states · Kansas City, MO",
                "500+ deals across all 50 states — he has bought in markets he didn't live in, and closes the "
                "day on the systems that make remote ownership survivable.",
            ),
        ],
        "takehome": "Bring the market questions your spreadsheet can't settle. Leave with the operators' read on "
                    "this metro, a shortlist of people who actually operate here, and much better questions than the "
                    "ones your spreadsheet can answer.",
    },
]

# NOTE: the fine print is not injected here — it arrives inside the lifted FOOTER, which already
# carries it. Do not add a second copy.


def optin(slug):
    """Field-brief capture. Returns empty until a real GHL form ID exists — see
    GHL_FIELD_BRIEF_FORM_ID above."""
    if not GHL_FIELD_BRIEF_FORM_ID:
        return (
            "\n<!-- Field-brief opt-in omitted: no form ID configured. "
            "See GHL_FIELD_BRIEF_FORM_ID in tools/build-persona-pages.py. -->"
        )
    fid = GHL_FIELD_BRIEF_FORM_ID
    return f"""
<section class="block fr-sec" id="fieldbrief">
  <style>
    .fr-sec{{background:var(--navy);color:var(--white);padding:60px 0 66px}}
    .fr-grid{{display:grid;grid-template-columns:1.05fr .95fr;gap:52px;align-items:start}}
    .fr-sec .eyebrow{{color:var(--red);margin-bottom:14px}}
    .fr-sec h2{{font-family:var(--font-display);color:var(--white);
      font-size:clamp(26px,3.2vw,40px);line-height:1.08;margin:0 0 16px}}
    .fr-lede{{font-family:var(--font-body);font-size:17px;line-height:1.6;
      color:#D6DBE6;margin:0 0 26px;max-width:52ch}}
    .fr-free{{display:inline-block;font-family:var(--font-mono);font-size:12px;
      letter-spacing:.12em;text-transform:uppercase;color:var(--white);
      border:1px solid rgba(255,255,255,.28);border-radius:2px;padding:7px 12px}}
    .fr-card{{background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.14);
      border-radius:10px;padding:26px 24px 18px}}
    .fr-card h3{{font-family:var(--font-head);font-weight:800;color:var(--white);
      font-size:19px;line-height:1.25;margin:0 0 6px}}
    .fr-card p{{font-family:var(--font-body);font-size:14px;line-height:1.5;
      color:#C3CAD8;margin:0 0 16px}}
    /* GHL parks the iframe offscreen until it loads, so the wrapper reserves the space. */
    .fr-formwrap{{min-height:430px;display:block}}
    .fr-form{{width:100%;border:0;border-radius:8px;display:block;min-height:430px}}
    .fr-note{{font-family:var(--font-body);font-size:12.5px;line-height:1.5;
      color:#9AA4B8;margin:12px 0 0;text-align:center}}
    @media (max-width:900px){{.fr-grid{{grid-template-columns:1fr;gap:34px}}.fr-lede{{max-width:none}}}}
  </style>
  <div class="wrap"><div class="fr-grid">
    <div>
      <div class="eyebrow">// Free Field Brief</div>
      <h2>Not Ready For A Seat? Take The Field Brief.</h2>
      <p class="fr-lede">The free short version of the funding map — ten programs, the next deadlines,
        and the three lookups to run before your next offer. PDF, straight to your inbox.</p>
      <span class="fr-free">Free · No ticket required</span>
    </div>
    <div class="fr-card">
      <h3>Send me the field brief</h3>
      <p>Enter your email and we'll send it over. That's the whole ask.</p>
      <!-- GHL form embed.
           GHL source value for this form: "BOKC — Funding Brief opt-in ({slug})". -->
      <div class="fr-formwrap">
      <iframe
        src="https://api.leadconnectorhq.com/widget/form/{fid}"
        id="inline-{fid}"
        class="fr-form"
        style="width:100%;border:none;border-radius:8px;display:block"
        data-layout="{{'id':'INLINE'}}"
        data-trigger-type="alwaysShow"
        data-activation-type="alwaysActivated"
        data-deactivation-type="neverDeactivate"
        data-form-name="BOKC — Funding Brief opt-in ({slug})"
        data-layout-iframe-id="inline-{fid}"
        title="Funding Field Brief opt-in"></iframe>
      </div>
      <script src="https://link.msgsndr.com/js/form_embed.js"></script>
      <p class="fr-note">We'll email the field brief straight over. No spam, unsubscribe anytime.</p>
    </div>
  </div></div>
</section>"""


def build(p):
    url = f"https://breakthroughokc.com/for/{p['slug']}/"
    ld = (
        '{"@context":"https://schema.org","@type":"Event",'
        '"name":"BREAKTHROUGH OKC: The 2026 Real Estate Investors Wealth Building Summit",'
        '"startDate":"2026-09-26T08:00:00-05:00","endDate":"2026-09-26T18:00:00-05:00",'
        '"eventAttendanceMode":"https://schema.org/OfflineEventAttendanceMode",'
        '"eventStatus":"https://schema.org/EventScheduled",'
        '"location":{"@type":"Place","name":"Champion Convention Center","address":{"@type":"PostalAddress",'
        '"streetAddress":"737 S Meridian Ave","addressLocality":"Oklahoma City","addressRegion":"OK",'
        '"postalCode":"73108","addressCountry":"US"}},'
        '"image":["https://breakthroughokc.com/assets/og-image.jpg"],'
        f'"description":"{p["desc"]}",'
        '"offers":{"@type":"Offer","price":"175","priceCurrency":"USD",'
        '"availability":"https://schema.org/InStock","validThrough":"2026-09-05",'
        '"url":"https://breakthroughokc.com/tickets/"},'
        '"organizer":{"@type":"Organization",'
        '"name":"Oklahoma City Real Estate Investors Association (OKC REIA)",'
        '"url":"https://breakthroughokc.com"}}'
    )

    return f"""{HEAD_PRE}<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>{p['title']}</title>
<meta name="description" content="{p['desc']}" />
<link rel="canonical" href="{url}" />
<link rel="icon" type="image/png" sizes="32x32" href="/assets/favicon-32.png" />
<link rel="icon" type="image/png" sizes="16x16" href="/assets/favicon-16.png" />
<link rel="apple-touch-icon" href="/assets/favicon-180.png" />
<meta name="theme-color" content="#1A2540" />
<meta property="og:type" content="website" />
<meta property="og:site_name" content="Breakthrough OKC 2026" />
<meta property="og:title" content="{p['title']}" />
<meta property="og:description" content="{p['desc']}" />
<meta property="og:url" content="{url}" />
<meta property="og:image" content="https://breakthroughokc.com/assets/og-image.jpg" />
<meta property="og:image:width" content="1200" />
<meta property="og:image:height" content="630" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="{p['title']}" />
<meta name="twitter:description" content="{p['desc']}" />
<meta name="twitter:image" content="https://breakthroughokc.com/assets/og-image.jpg" />
{FONTS}
<script type="application/ld+json">{ld}</script>
{CLARITY}
{PIXEL}
</head>
<body>
{TOPBAR}
{NAV}

<section class="hero bg"><div class="wrap in">
  <div class="eyebrow">{p['eyebrow']}</div>
  <h1>{p['h1']}</h1>
  <p>{p['lede']}</p>
  <p class="presented">September 26, 2026 · Champion Convention Center, Oklahoma City</p>
  <div class="cta2"><a href="{REG}" class="btn btn-lg">Claim Your Seat — $175 →</a><a href="/agenda/" class="btn btn-lg btn-ghost">See The Full Day</a></div>
</div>
{CLOUD}
</section>

<section class="block"><div class="wrap">
  <div class="sec-head center"><div class="eyebrow">// The Problem</div><h2>{p['problem_head']}</h2></div>
  <div class="grid3">
    {chr(10).join('    ' + c for c in p['problems'])}
  </div>
</div></section>

<section class="block tint"><div class="wrap">
  <div class="sec-head center"><div class="eyebrow">// The Evidence</div><h2>{p['proof_head']}</h2><p>{p['proof_lede']}</p></div>
  <div class="grid3">
    {chr(10).join('    ' + c for c in p['proof'])}
  </div>
</div></section>

<section class="block"><div class="wrap">
  <div class="sec-head center"><div class="eyebrow">// The Lineup</div><h2>{p['speakers_head']}</h2></div>
  <div class="spk-grid two">
    {chr(10).join('    ' + c for c in p['speakers'])}
  </div>
  <div class="center" style="margin-top:32px"><a href="/speakers/" class="btn btn-ghost">Meet All The Speakers</a></div>
</div></section>

<!-- FUNDING MANUAL — UNGATED VERSION. Do NOT add panelist names here; the named
     copy is gated on Marty's written OK (see PR #7 and the build brief §2d). -->
<section class="block tint"><div class="wrap">
  <div class="sec-head center"><div class="eyebrow">// With Your Seat</div><h2>The Complete Oklahoma Investor Funding Manual</h2>
    <p>30 public funding programs across city, state and federal layers, verified against the agencies' own
    documents, with the deadline calendar and direct program contacts — included with your seat. The expert
    panel takes questions on it in person.</p></div>
  <div style="border:2px solid var(--navy);border-radius:14px;padding:32px 28px;max-width:900px;margin:0 auto;text-align:center">
    <h3 style="margin-bottom:12px">What You'll Leave With</h3>
    <p style="max-width:66ch;margin:0 auto">{p['takehome']}</p>
  </div>
  <div class="center" style="margin-top:30px"><a href="{REG}" class="btn btn-lg">Claim Your Seat — $175 →</a>
    <div class="js-pre-rise" style="font-family:var(--font-mono);font-size:12px;color:#6b7890;margin-top:12px">$175 until September 5, 11:59 p.m. · $197 from September 6</div>
  </div>
</div></section>

<section class="block"><div class="wrap">
  <div class="sec-head center"><div class="eyebrow">// Your Ticket</div><h2>Everything Included</h2></div>
  <div class="grid3">
    <div class="fcard"><h3>The Full Day</h3><p>Three keynotes — see the deal, fund it, scale it — plus the
      expert panel Q&amp;A on the Oklahoma City market.</p></div>
    <div class="fcard"><h3>The Funding Manual</h3><p>30 verified programs, 12 dated funding windows into 2027,
      application paths, direct contacts and a glossary.</p></div>
    <div class="fcard"><h3>The Room</h3><p>Curated networking, a sponsor and exhibitor hall of contractors and
      lenders, plus light breakfast and lunch — served.</p></div>
  </div>
</div></section>
{optin(p['slug'])}
<section class="block ctaband"><div class="wrap">
  <div class="eyebrow" style="color:#ffd8d3">// One Saturday</div>
  <h2>Ready To Claim Your Seat?</h2><p>Tickets $175<span class="js-pre-rise"> — price rises to $197 on September 6</span>.</p>
  <a href="{REG}" class="btn btn-lg">Register Now →</a>
</div></section>
{FOOTER}
{CHAT}
{PRICE_SWITCH}
<!-- Meta pixel: ViewContent on load, Lead on registration-CTA click. Value follows the current
     price. Delegated so attribution v2's stamped links are never rewritten. -->
<script>
  if (typeof fbq === "function") fbq("track","ViewContent",{{content_name:"Breakthrough OKC 2026 — {p['slug']}",content_category:"Event",value:(window.btokcTicketPrice||175),currency:"USD"}});
  document.addEventListener("click", function(e){{
    var a = e.target && e.target.closest ? e.target.closest("a") : null;
    if (!a || !a.href || a.href.indexOf("registration.breakthroughokc.com") === -1) return;
    if (typeof fbq === "function") fbq("track", "Lead", {{value: window.btokcTicketPrice || 175, currency: "USD"}});
  }}, true);
</script>
</body>
</html>
"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    written = []
    for p in PERSONAS:
        d = OUT / p["slug"]
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(build(p), encoding="utf-8")
        written.append(f"website/for/{p['slug']}/index.html")

    # sitemap
    sm = SITE / "sitemap.xml"
    xml = sm.read_text(encoding="utf-8")
    for p in PERSONAS:
        loc = f"https://breakthroughokc.com/for/{p['slug']}/"
        if loc in xml:
            continue
        entry = f"  <url>\n    <loc>{loc}</loc>\n    <changefreq>weekly</changefreq>\n    <priority>0.8</priority>\n  </url>\n"
        xml = xml.replace("</urlset>", entry + "</urlset>")
    sm.write_text(xml, encoding="utf-8")
    written.append("website/sitemap.xml")

    print("\n".join(written))
    print(f"\n{len(PERSONAS)} persona pages built.")
    print("Ad utm_content slugs:")
    for p in PERSONAS:
        print(f"  /for/{p['slug']}/  ->  utm_content={p['utm']}")


if __name__ == "__main__":
    main()
