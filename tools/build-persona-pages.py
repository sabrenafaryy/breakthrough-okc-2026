#!/usr/bin/env python3
"""
Builds the five persona landing pages under website/for/.

Run from the repo root:  python3 tools/build-persona-pages.py

Shared chrome (attribution v2, pixel, nav, footer, price-switch, Lead event) is
lifted verbatim out of the live pages so these never drift from the rest of the
site. Persona copy lives in PERSONAS below — edit there, re-run, commit.

House-rule constraints baked in and NOT to be relaxed without a checker pass:
  * Darrell Beavers and Shannon Entz were CLEARED for public use 2026-08-27 and
    may be named. Still say "the expert panel", never "city leaders", and never
    overstate Shannon — she implements, she does not control city funds.
  * Program terms stay OFF the site (option 3, settled 2026-08-30). A static page
    cannot qualify a claim: "0% interest" is true for a builder and false for the
    landlord adding door seven. Sell the room, the people and the manual.
    MARKET figures stay — they describe the city, not a program's eligibility.
  * Every number carries its source link and access date.
  * No attendance number. 250 is venue capacity, never attendance.
  * No investment-return promise.
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

LOGO_ROW = slice_between(HOME, '<div class="logo-row">', "</div>\n  </div>")
MARQUEE = slice_between(HOME, '<div class="marquee">', "</div></div>")

REG = "https://registration.breakthroughokc.com/check-out"

# The GHL field-brief form ID. While this is None the opt-in section is OMITTED entirely —
# a 430px card wired to a dead form is worse than no card on pages taking paid spend.
# Set it to the real ID and re-run to switch the section on across every page.
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
    # ⚠️ RETIRED FROM THE SITE by option 3 (2026-08-30). These describe PROGRAM ELIGIBILITY,
    # which a static page cannot qualify to a reader. Kept only so the values stay traceable.
    # Do NOT attach any of the five below to a card. They are the panel's material.
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


def person_stat_card(stat, body):
    """A big-number card for a fact about a PERSON — no source link, because these are
    biographical facts from Darrell's own material, not program eligibility claims.
    Do NOT put program terms in one of these; that is what option 3 removed."""
    return (
        f'<div class="fcard"><div style="{STAT_STYLE}">{stat}</div>'
        f'<p style="margin-top:12px">{body}</p></div>'
    )


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
        "slug": "builders",
        "floor_line": "The lenders, title people and trades you need on a build are standing on the floor all day. You can ask a lender what they will actually lend on before you need them on a clock.",
        "utm": "persona-builder",
        "nav": "Builders",
        "title": "For Small Builders | Breakthrough OKC 2026",
        "desc": "The bank wants 30% down. Oklahoma runs seven housing finance programs, and the man "
                "who administers all seven takes questions on September 26 in Oklahoma City.",
        "eyebrow": "// For Small Builders &amp; Developers",
        "h1": 'The Bank Wants 30% Down. <span class="r">There Are Six Other Doors.</span>',
        "lede": "Oklahoma runs seven housing finance programs. Most builders in this state have never had "
                "them laid out in one place — which one funds what, who actually qualifies, and which "
                "window is open this month. On September 26 the man who administers all seven is in the "
                "room, and he takes questions.",
        "problem_head": "One Build At A Time Is A Ceiling",
        "problems": [
            plain_card(
                "The down payment is the whole constraint",
                "Your deal pencils. Your equity doesn't stretch to the next one until this one closes. "
                "That's a financing problem wearing a deal problem's coat.",
            ),
            plain_card(
                "Public money looks like it's for someone else",
                "Bigger developers, nonprofits, syndicators. Some of it is. Some of it was written for a "
                "builder putting up five houses, and nobody tells you which is which.",
            ),
            plain_card(
                "The window matters more than the program",
                "Some programs take applications continuously. Some pause. Some have one deadline a year. "
                "Which door is open in which month is most of the game, and it changes.",
            ),
        ],
        "proof_head": "The Man Who Administers Them",
        "proof_lede": "Not a summary of the programs — the person responsible for them, in the room, "
                      "answering the question you actually have about the build you're actually planning.",
        # Facts about Darrell, not eligibility claims about programs. That is why they survive
        # option 3. Do not add program terms to these.
        "proof": [
            person_stat_card(
                "Seven programs",
                "Darrell Beavers has administrative responsibility for seven of Oklahoma's housing finance "
                "programs. Four federal, three state. Different income rules, different cycles, different "
                "qualification bars.",
            ),
            person_stat_card(
                "Since 1991",
                "He has been at the Oklahoma Housing Finance Agency for over three decades, and he wrote "
                "<i>The Affordable Housing Handbook</i>. He is also an active real estate broker and "
                "investor, which is why he explains this in deal terms rather than agency terms.",
            ),
            person_stat_card(
                "48,000+ units",
                "Affordable housing units financed through the programs he administers.",
            ),
        ],
        "speakers_head": "The Two People Who Run Oklahoma's Housing Money — And A Builder Who Scaled",
        "speakers": [
            speaker_card(
                "darrell", "Darrell Beavers", "Expert Panel · Oklahoma Housing Finance Agency",
                "Housing Development Director · at OHFA since 1991 · 48,000+ affordable housing units financed",
                "He administers seven of Oklahoma's housing finance programs and is an active real estate broker and investor himself, which is why he explains them in deal terms. On September 26 he walks the room through all seven — what each funds, who qualifies, what to say when you call — and takes live questions.",
            ),
            speaker_card(
                "shannon", "Shannon Entz", "Expert Panel · City of Oklahoma City",
                "Housing Strategy Implementation Manager · 29 years in city planning",
                "She implements Oklahoma City's housing strategy — what the city is actually doing on housing, block by block, inside the city limits. If your lot is in OKC she is the person to ask, and on September 26 she takes live questions too.",
            ),
            speaker_card(
                "cameron", "Cameron Burke", "Keynote · Leverage",
                "4 companies · 75+ units · 150+ home sales a year · Oklahoma City, OK",
                "He did every job in the business himself for two years before he could afford anyone else. His keynote is the structure underneath running more than one thing at a time: what he hired first, what he systemized, and the order he did it in.",
            ),
        ],
        "takehome": "Bring one lot and one build you can't start yet. Leave with the seven programs "
                    "written down in the Oklahoma Investor Funding Manual, the deadline calendar, direct "
                    "contacts — and the answer to the question you asked out loud.",
    },
    {
        "slug": "agents",
        "floor_line": "The lenders, title people and contractors your investor clients already use &mdash; and the ones you will want to be able to name when a client asks you for a referral.",
        "utm": "persona-agent",
        "nav": "Agents",
        "title": "For Real Estate Agents | Breakthrough OKC 2026",
        "desc": "A retail client transacts once. An investor transacts, refers and comes back — for the "
                "agent who can read a deal. September 26, Oklahoma City.",
        "eyebrow": "// For Real Estate Agents",
        "h1": 'An Investor Works Out In <span class="r">One Conversation</span> Whether You Can Read A Deal.',
        "lede": "Cap rate. ARV. What the rehab actually costs here. Which lenders close in Oklahoma. Miss "
                "on that and they stop replying. Hit it and you're the one they call next time — and the "
                "one they name when someone in their group asks who to use. September 26 is a day among "
                "the people who decide that.",
        "problem_head": "Why Investors Don't Call You Back",
        "problems": [
            plain_card(
                "A retail client transacts once",
                "Then disappears for five years. An investor transacts, refers, sells and comes back. Same "
                "license, completely different business, and almost nobody makes the switch on purpose.",
            ),
            plain_card(
                "You're sending listings",
                "They already have alerts. They already ran the numbers. Forwarding inventory they've seen "
                "is the exact behavior that says you're not in this with them.",
            ),
            plain_card(
                "You have nothing they don't have",
                "They read the market. They know their lenders. The gap you can fill is the thing they "
                "don't have time to go find — and nobody's shown you where that is either.",
            ),
        ],
        "proof_head": "Three Things You Can Say On Monday",
        "proof_lede": "Every figure below is published, dated and linked. Learn the sources, not just the "
                      "numbers — knowing where a figure comes from is what separates an agent who reads "
                      "the market from one who repeats it.",
        "proof": [
            stat_card(
                "+13,700",
                "Metro residents added in a year, 0.9% growth. The demand side of whatever strategy your "
                "client is running, and the first thing they'll test you on.",
                "pop",
            ),
            stat_card(
                "$316,450",
                "Median metro listing price, July 2026. The low basis is why out-of-state money keeps "
                "arriving, and it's behind half the questions you'll get from a client who doesn't live here.",
                "price",
            ),
            stat_card(
                "41%",
                "Of Oklahoma City households rent. The tenant pool behind every buy-and-hold conversation "
                "you'll have this year.",
                "rent",
            ),
            plain_card(
                "Thirty programs they've never heard of",
                "Every seat includes the Oklahoma Investor Funding Manual: 30 public funding programs "
                "across city, state and federal layers, verified against the agencies' own documents, "
                "with the deadline calendar and direct contacts. Being the agent who knows this exists is "
                "the kind of thing an investor client remembers.",
            ),
        ],
        "speakers_head": "The Three Sessions That Change The Conversation",
        "speakers": [
            speaker_card(
                "cameron", "Cameron Burke", "Keynote · Leverage",
                "4 companies · 75+ units · 150+ home sales a year · Oklahoma City, OK",
                "He sits on both sides of your table: a team selling 150+ homes a year, and 75+ rental units he owns himself. The clearest look you'll get at how an investor actually decides.",
            ),
            speaker_card(
                "darrell", "Darrell Beavers", "Expert Panel · Oklahoma Housing Finance Agency",
                "Housing Development Director · at OHFA since 1991 · 48,000+ affordable housing units financed",
                "The state layer, and the session you'll be quoting to clients for the next year — what money exists in Oklahoma, who qualifies, and how someone gets from interested to funded. He takes live questions.",
            ),
            speaker_card(
                "shannon", "Shannon Entz", "Expert Panel · City of Oklahoma City",
                "Housing Strategy Implementation Manager · 29 years in city planning",
                "The city layer. She implements Oklahoma City's housing strategy, so what the city is working on in housing is a question you can put to her directly — and stop guessing at when a client asks.",
            ),
        ],
        "takehome": "Bring the client conversation you keep losing. Leave able to have it — with the "
                    "funding manual, the vocabulary, and a day's worth of introductions to people who buy "
                    "for a living.",
    },
    {
        "slug": "buy-and-hold",
        "floor_line": "Property managers, lenders and contractors, in person, all day. The three hires that quietly decide whether door seven performs or eats your weekends.",
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
        "proof_head": "The Man Who Runs The State's Housing Money",
        "proof_eyebrow": "// Who Answers It",
        "proof_lede": "There are around thirty public funding programs in this state and almost nobody has "
                      "had them laid out in one place. We are not going to tell you which one fits your "
                      "building — a webpage can't do that honestly. The man who administers seven of them "
                      "can, and he takes questions.",
        "proof": [
            person_stat_card(
                "Seven programs",
                "Darrell Beavers has administrative responsibility for seven of Oklahoma's housing finance "
                "programs. Whether any of them fits a building you already own depends on what you're doing "
                "with it — which is exactly the kind of question the panel exists to answer out loud.",
            ),
            stat_card(
                "$39.7M",
                "Of the NE Renaissance TIF districts' $50M project budget, $39.7M is still unallocated per "
                "the city's FY25 report. That is budget capacity against future increment, not cash at "
                "closing — but where a district's boundary sits is worth knowing before you buy near one.",
                "tif",
            ),
            plain_card(
                "Thirty programs, written down",
                "Every seat includes the Oklahoma Investor Funding Manual — 30 public funding programs "
                "across city, state and federal layers, verified against the agencies' own documents, with "
                "the deadline calendar and direct contacts. The manual is the map; the day is the guided tour.",
            ),
        ],
        "speakers_head": "The Panel That Answers The Money Question — And Two Operators Who Live It",
        "speakers": [
            speaker_card(
                "darrell", "Darrell Beavers", "Expert Panel · Oklahoma Housing Finance Agency",
                "Housing Development Director · at OHFA since 1991 · 48,000+ affordable housing units financed",
                "He administers seven of Oklahoma's housing finance programs and is an active broker and investor himself. On September 26 he takes live questions about the building you actually own.",
            ),
            speaker_card(
                "shannon", "Shannon Entz", "Expert Panel · City of Oklahoma City",
                "Housing Strategy Implementation Manager · 29 years in city planning",
                "She implements Oklahoma City's housing strategy, so what the city is doing in the neighborhoods you already own in is a question she can answer directly. She takes live questions on the day.",
            ),
            speaker_card(
                "cameron", "Cameron Burke", "Keynote · Leverage",
                "4 companies · 75+ units · 150+ home sales a year · Oklahoma City, OK",
                "Runs 75+ rentals alongside three other companies. His keynote is the systems and delegation that let a portfolio grow without swallowing your week — the answer if the ceiling you hit was time rather than capital.",
            ),
            speaker_card(
                "katie", "Katie Neason", "Keynote · Redevelopment",
                "$15M portfolio · downtown redeveloper · Bryan, TX",
                "The other way to add doors: buy the tired building on the tired street and hold it while the street turns. Her Redevelopment Advantage Framework is how she reads which street does.",
            ),
        ],
        "takehome": "Bring one building or one target. Leave knowing which capital door to test first, what "
                    "deadline you're working against, and which agency to call on Monday.",
    },
    {
        "slug": "fix-and-flip",
        "floor_line": "Lenders who fund rehabs and the trades who finish them &mdash; on the floor all day, so you can have the conversation before the next one is under contract.",
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
                "It is a problem — until you can read which street turns next and what public money is "
                "<i>planned</i> for turning it. Then it's the only cheap thing left.",
            ),
            plain_card(
                "You've never priced the hold",
                "Some of the buildings you pass on are worth keeping rather than selling — and the money that "
                "rewards holding is a different set of doors than the hard money you already know.",
            ),
        ],
        "proof_head": "Reading The Block Before The Comps Move",
        "proof_eyebrow": "// What Katie Teaches",
        "proof_lede": "Straight answer on public money: most of it is affordable and workforce housing "
                      "finance, and a short-hold flip does not qualify. What is useful to you is knowing "
                      "where it is planned — because that is a signal about a street, months before it "
                      "shows up in a comp.",
        "proof": [
            plain_card(
                "The Redevelopment Advantage Framework",
                "Katie Neason's method for looking at a tired building on a tired street and reading what "
                "it becomes. She has been buying that way for years and teaches the framework itself on "
                "September 26 — the method, not the highlight reel.",
            ),
            stat_card(
                "$39.7M",
                "Of the NE Renaissance TIF districts' $50M project budget, $39.7M is still unallocated per "
                "the city's FY25 report — budget capacity against future increment, not cash at closing, "
                "and not money you can apply for on a flip. It is a map of where the city has <b>planned</b> "
                "to spend, and district boundaries are public.",
                "tif",
            ),
            stat_card(
                "$316,450",
                "The median home listing price in the OKC metro in July 2026. A low basis is why the rehab "
                "math still works in this market — and why the margin is worth defending with better "
                "sourcing rather than a higher bid.",
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
                "cameron", "Cameron Burke", "Keynote · Leverage",
                "4 companies · 75+ units · 150+ home sales a year · Oklahoma City, OK",
                "He runs flips in this metro alongside a sales team doing 150+ homes a year — so he sees "
                "both what the finished product sells for and what it costs to get there. The closest read "
                "you'll get on margin in this market.",
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
        "floor_line": "The exhibitor hall runs the length of the day. Lenders, title people and the buyers they work with are all in the same room, and nobody is gatekeeping the introductions.",
        "utm": "persona-wholesale",
        "nav": "Wholesalers",
        "title": "For Wholesalers | Breakthrough OKC 2026",
        "desc": "You have the deal. You don't have the buyer. September 26 puts you in a room of flippers, "
                "landlords, builders and the lenders funding them — vendor floor open all day.",
        "eyebrow": "// For Wholesalers",
        "h1": 'A List You Haven\'t Called In A Year <span class="r">Isn\'t A List.</span>',
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
        "proof_head": "The Shape Of The Day",
        "proof_eyebrow": "// Where The Room Is Open",
        "proof_lede": "The reason to come is the time between things. Here is where the day actually "
                      "leaves room to work — and who is standing in it.",
        "proof": [
            plain_card(
                "The exhibitor floor, open all day",
                "Not a corridor you pass through twice. It runs the length of the day, so a conversation "
                "that starts at the coffee table can finish properly at lunch.",
            ),
            plain_card(
                "Real gaps between the keynotes",
                "Three keynotes and an expert panel, deliberately not stacked end to end. The gaps are "
                "where a card changes hands.",
            ),
            plain_card(
                "Who is standing in them",
                "Flippers sourcing their next project, landlords adding doors, builders looking for lots, "
                "and the lenders and title people they already work with.",
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
        "floor_line": "Lenders, contractors, title and property managers &mdash; the team you will eventually need, in one room, where you can ask a beginner question without it costing you anything.",
        "utm": "persona-new",
        "nav": "New Investors",
        "title": "New To Investing? | Breakthrough OKC 2026",
        "desc": "Where do you even find the first deal? September 26 is a full day with operators who've done "
                "it — plus the complete Oklahoma funding map with your seat.",
        "eyebrow": "// If You're New To This",
        "h1": 'You\'ve Known Enough To Start <span class="r">For Two Years.</span>',
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
                "You've read enough",
                "Reading more is the thing that feels like progress. Another podcast, another thread, "
                "another course — none of it is the step you haven't taken, and some of it is a way of "
                "not taking it.",
            ),
            plain_card(
                "You've never met anyone who's done it",
                "The fastest way past deal one is proximity to people on deal fifty — close enough to ask the "
                "small question you would never post publicly.",
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
                "cameron", "Cameron Burke", "Keynote · Leverage",
                "4 companies · 75+ units · 150+ home sales a year · Oklahoma City, OK",
                "He started at 18 with no sphere and no capital, and did every job himself for two years "
                "before he could afford anyone else. If the question is where you begin with nothing, he "
                "is the closest answer in the room.",
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
        "floor_line": "This is the part you cannot do from a thousand miles away: meet the lender, the contractor and the property manager face to face before you hire any of them.",
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
                "You can't read the room from a listing site",
                "Which builders actually deliver, which lenders actually close here, which property manager "
                "answers the phone in February. None of that publishes, and all of it decides your return.",
            ),
        ],
        "proof_head": "The Three Relationships Your Return Rests On",
        "proof_eyebrow": "// The Part You Can't Do Remotely",
        "proof_lede": "The market figures already work or you wouldn't be reading this — <b>+13,700 metro "
                      "residents added in a year</b>, a <b>$316,450</b> median list price, <b>41%</b> of "
                      "households renting, all sourced below. What a spreadsheet can't hand you is the "
                      "three relationships your return actually rests on. Those are standing on the "
                      "exhibitor floor all day.",
        "proof": [
            plain_card(
                "Lenders who close in Oklahoma",
                "Not a national call center. People who fund deals in this metro, who you can ask directly "
                "what they will and won't lend on — before you need them on a clock.",
            ),
            plain_card(
                "Contractors and property managers",
                "The two hires that quietly decide whether a remote rental performs or slowly bleeds. You "
                "get to meet them in person instead of picking from reviews a thousand miles away.",
            ),
            stat_card(
                "+13,700 · $316,450 · 41%",
                "Metro residents added in a year (0.9% growth) · median metro listing price, July 2026 · "
                "share of Oklahoma City households that rent. Every one published, dated and linked — "
                "check them yourself before you book anything.",
                "pop", "price", "rent",
            ),
        ],
        "speakers_head": "The Locals You'd Otherwise Be Guessing About",
        "speakers": [
            speaker_card(
                "cameron", "Cameron Burke", "Keynote · Leverage",
                "4 companies · 75+ units · 150+ home sales a year · Oklahoma City, OK",
                "He operates in this metro every day — flips, 75+ rentals, and a sales team doing 150+ homes a year. If you want the local operator's read, he is it.",
            ),
            speaker_card(
                "ben", "Ben Allgeyer", "Keynote · Scaling",
                "500+ deals in 8 years · all 50 states · Kansas City, MO",
                "500+ deals across all 50 states — he has bought in markets he didn't live in, and closes the day on the systems that make remote ownership survivable.",
            ),
            speaker_card(
                "darrell", "Darrell Beavers", "Expert Panel · Oklahoma Housing Finance Agency",
                "Housing Development Director · at OHFA since 1991 · 48,000+ affordable housing units financed",
                "The state layer. He administers seven of Oklahoma's housing finance programs, and if you are weighing whether to buy here at all, he is the person to ask what money exists and who qualifies — live, not from a website.",
            ),
            speaker_card(
                "shannon", "Shannon Entz", "Expert Panel · City of Oklahoma City",
                "Housing Strategy Implementation Manager · 29 years in city planning",
                "The city layer, and the thing you genuinely cannot read from a thousand miles away. She implements Oklahoma City's housing strategy and takes live questions — including about the specific part of town you have been looking at.",
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
            "\n<!-- opt-in pending -->"
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


def floor_block(p):
    """Sponsors + exhibitor floor. Logos are lifted from the live homepage, so this page
    can never name a partner the homepage doesn't already name. Do not hand-add names here."""
    return f"""
<section class="block"><div class="wrap">
  <div class="sec-head center"><div class="eyebrow">// Partners</div><h2>Sponsors &amp; The Exhibitor Hall</h2>
    <p>{p.get('floor_line', 'Contractors, lenders and partners are in the exhibitor hall all day &mdash; not a corridor you pass through twice.')}</p></div>
  {LOGO_ROW}
  <p class="center" style="color:#9aa3b5;font-family:var(--font-mono);font-size:12px;margin-top:22px">More partners announced soon.</p>
</div>
{MARQUEE}
<div class="wrap"><div class="center" style="margin-top:26px"><a href="/sponsors/" class="btn btn-ghost">Exhibit Or Sponsor</a></div></div>
</section>"""


def build(p):
    # 3 cards look wrong in a 2-col grid (orphan on row 2); 4 look wrong in a 3-col grid.
    spk_cls = "" if len(p["speakers"]) == 3 else " two"
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
  <div class="sec-head center"><div class="eyebrow">{p.get('proof_eyebrow', '// The Evidence')}</div><h2>{p['proof_head']}</h2><p>{p['proof_lede']}</p></div>
  <div class="grid3">
    {chr(10).join('    ' + c for c in p['proof'])}
  </div>
</div></section>

<section class="block"><div class="wrap">
  <div class="sec-head center"><div class="eyebrow">// The Lineup</div><h2>{p['speakers_head']}</h2></div>
  <div class="spk-grid{spk_cls}">
    {chr(10).join('    ' + c for c in p['speakers'])}
  </div>
  <div class="center" style="margin-top:32px"><a href="/speakers/" class="btn btn-ghost">Meet All The Speakers</a></div>
</div></section>

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

{floor_block(p)}

<section class="block"><div class="wrap">
  <div class="sec-head center"><div class="eyebrow">// Your Ticket</div><h2>Everything Included</h2></div>
  <div class="grid3">
    <div class="fcard"><h3>The Full Day</h3><p>Three keynotes — see the deal, leverage it, scale it — plus the
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
