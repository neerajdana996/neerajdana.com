"""Builds neerajdana.com into dist/ (deploy) and preview/ (in-chat preview).

    npm install        # Tailwind CLI + GSAP (CI does this automatically)
    python3 build.py

Content lives in pages/, styles in src/input.css, scripts in static/js/.
Titles, descriptions, FAQs, glossary, structured data, sitemap, robots.txt and llms.txt are generated here.
"""
import html, json, os, re, shutil, subprocess, sys
from datetime import date
from pathlib import Path

SITE = "https://neerajdana.com"
EMAIL = "ndana@profract.com"
LINKEDIN = "https://linkedin.com/in/neeraj-dana"
GITHUB = "https://github.com/neerajdana996"
PUBLISHED = "2026-10-09"
UPDATED = "2026-10-09"
INDEXNOW_KEY = "0d5aa270e45be7b2b3529240ac7bfdfa"

ROOT = Path(__file__).parent
DIST, PREVIEW = ROOT / "dist", ROOT / "preview"

TAILWIND_BROWSER = "https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4.1.11"   # preview only
GSAP_VERSION = "3.13.0"
GSAP_FILES = ["gsap.min.js", "ScrollTrigger.min.js", "MotionPathPlugin.min.js", "DrawSVGPlugin.min.js"]
GSAP_CDN = f"https://cdnjs.cloudflare.com/ajax/libs/gsap/{GSAP_VERSION}/"
FONTS = ("https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500..700"
         "&family=Source+Serif+4:opsz,wght@8..60,400..600&family=JetBrains+Mono:wght@400;500&display=swap")

def human_date(d):
    return date.fromisoformat(d).strftime("%-d %B %Y")

PERSON = {
    "@type": "Person",
    "@id": f"{SITE}/#person",
    "name": "Neeraj Dana",
    "url": f"{SITE}/",
    "image": f"{SITE}/og.png",
    "jobTitle": "Founder, Profract",
    "description": "Founder of Profract and staff-level software engineer with 11+ years building distributed systems, real-time platforms and production AI at companies including Atlassian, ServiceNow and Egnyte. Profract helps startups build products from idea to production and helps growing companies scale their systems.",
    "founder": None,
    "email": f"mailto:{EMAIL}",
    "sameAs": [LINKEDIN, GITHUB],
    "address": {"@type": "PostalAddress", "addressLocality": "Bengaluru", "addressCountry": "IN"},
    "knowsAbout": [
        "Distributed systems", "Event-driven architecture", "Apache Kafka", "Microservices",
        "Real-time data synchronization", "Redis caching", "Incident response", "Engineering leadership",
        "Large language model orchestration", "Retrieval-augmented generation", "AI agents", "AI agent evaluation",
        "TypeScript", "Node.js", "Python", "Go", "React", "GraphQL",
    ],
}

PERSON.pop("founder")
ORG = {"@type": "Organization", "@id": "https://profract.com/#org", "name": "Profract", "url": "https://profract.com",
       "founder": {"@id": f"{SITE}/#person"},
       "description": "Engineering studio founded by Neeraj Dana that builds MVPs for startups, scales systems for growing companies and takes AI features to production."}
PERSON["affiliation"] = {"@id": "https://profract.com/#org"}

# ------------------------------------------------------------------ FAQs (HTML and schema from one source)
FAQS = {
    "index": [
        ("Who is Neeraj Dana?",
         "Neeraj Dana is the founder of Profract and a staff-level software engineer based in Bengaluru, India, with 11+ years of experience building production systems at companies including Atlassian, ServiceNow and Egnyte. He specialises in distributed and event-driven systems, real-time data sync and production AI systems."),
        ("What does Neeraj specialise in?",
         "Distributed and event-driven systems (Kafka, microservices), real-time synchronisation and caching, production LLM systems (orchestration, RAG, agents, output validation and evaluation), and engineering leadership, including incident command."),
        ("What is Profract?",
         "Profract is the engineering studio founded by Neeraj Dana. It helps startups build products from idea to production, helps startups and mid-size companies scale their architecture and reliability, and takes AI features and agents to production. Neeraj leads every engagement personally."),
        ("What services does Neeraj offer through Profract?",
         "MVP to production for startups, architecture and scaling for startups and mid-size companies (reviews, fractional technical leadership, reliability and performance work), and production AI (orchestration, RAG, agents, output validation and evals). Engagements are remote and worldwide."),
        ("What has Neeraj built?",
         "Checkout, billing and provisioning flows for enterprise customers at Atlassian; the LLM orchestration and validation layers of ServiceNow's prompt-to-app generative AI product; real-time two-way sync between Egnyte and Google Workspace; an event-driven telemetry platform at Trianz; and core banking and anti-money-laundering systems earlier in his career.",
         "case-studies.html", "Read the case studies"),
        ("Can we contract through a company and sign an NDA?",
         "Yes. Engagements are contracted through Profract, and NDAs are signed before any code or data is shared."),
        ("Which time zones does Neeraj work with?",
         "He is based in India (UTC+5:30). His working day overlaps fully with European business hours, and he schedules calls in US mornings or evenings as needed."),
        ("How does an engagement with Neeraj start?",
         "With a free 30-minute call to understand the system and the goal, followed by a written proposal with a fixed scope. Email works best for the first contact, and he replies within one business day."),
    ],
    "ai": [
        ("What is an RL environment for a coding agent?",
         "It is a sandboxed software project, usually a repository running in a container, that an AI agent works in to complete a task. A verifier then checks the result automatically, which produces the reward signal used in reinforcement learning or the score used in an evaluation."),
        ("What makes a good verifier for a coding task?",
         "It checks behaviour rather than matching a reference diff, runs outside the agent's reach, fails every known wrong-but-plausible fix, and gives the same result every time it runs. For timing bugs, that means fault injection and fixed seeds."),
        ("How do you stop agents from gaming a task?",
         "Hidden tests run in a clean step after the agent finishes, the agent's diff is checked for edits to tests and fixtures, the answer is kept out of git history and comments, and shortcuts such as sleeps, retries or hard-coded outputs are confirmed to fail."),
        ("Can you work inside our existing harness and formats?",
         "Yes. I can author tasks and verifiers in your tooling and formats, under your confidentiality terms, part-time or full-time."),
    ],
    "kafka": [
        ("Is exactly-once delivery possible with Kafka?",
         "Kafka's exactly-once semantics cover read-process-write loops that stay inside Kafka, where consumed offsets and produced records are committed in one transaction. They do not cover side effects in databases or external APIs. For those, you need idempotent processing."),
        ("Should I turn off enable.auto.commit?",
         "If you process records synchronously in the poll loop, auto-commit still gives at-least-once delivery. If you process records on other threads or asynchronously, turn it off and commit explicitly after the work is done, or a crash can lose records."),
        ("Doesn't the deduplication table grow forever?",
         "Delete rows older than the longest window in which a message could be redelivered, such as your topic retention or maximum replay period, plus a margin. If you might replay a topic from the beginning, keep keys as long as that data exists, or use natural keys with upserts."),
        ("Does cooperative rebalancing stop duplicates?",
         "It reduces them, because consumers only give up the partitions that move. It does not stop them: crashes and slow batches still cause redelivery. Only idempotent processing removes the effect of duplicates."),
    ],
    "tasks": [
        ("What is a verifier in AI agent evaluation?",
         "A verifier is the automated check that decides whether an agent completed a task, for example a hidden test suite, an invariant check or a comparison of system state. Its result becomes the reward in reinforcement learning or the score in an evaluation."),
        ("Why not grade agents against a reference solution?",
         "Matching a reference diff rejects correct fixes that take a different route and can accept wrong ones that look similar. Checking behaviour, such as what ends up in the database or what calls were made, measures what matters."),
        ("How do you make race-condition tasks reproducible?",
         "Add fault-injection hooks to the environment, such as restarting a consumer after a side effect, and run the scenario across a fixed set of seeds so the same interleavings are tested every time."),
    ],
}

KAFKA = "notes/kafka-consumer-duplicate-messages-rebalance.html"
TASKS = "notes/designing-verifiable-coding-tasks-for-ai-agents.html"
GLOSSARY = [
    ("at-least-once-delivery", "At-least-once delivery",
     "A delivery guarantee where every message is processed one or more times, so nothing is lost but duplicates are possible. It is the default for most Kafka consumers, because a consumer that fails before committing its offset will receive the same messages again.", KAFKA),
    ("bidirectional-sync", "Bidirectional sync",
     "Keeping data consistent between two systems where changes can start on either side. It needs a clear owner for each field, version-aware updates so a system ignores echoes of its own writes, and a periodic reconcile job to catch drift.", None),
    ("cache-invalidation", "Event-driven cache invalidation",
     "Removing or refreshing cached data when the event that changes it happens, rather than waiting for a timer to expire. It keeps caches fast without serving stale values for long.", None),
    ("consumer-lag", "Consumer lag",
     "The number of messages a consumer group still has to process in a partition: the gap between the latest offset written and the group's committed offset. Rising lag means consumers are falling behind producers.", None),
    ("consumer-rebalance", "Consumer rebalance",
     "The process in which a Kafka consumer group reassigns partitions among its members, triggered when a consumer joins, leaves or stops responding. Messages processed but not yet committed before a rebalance are delivered again to the new owner.", KAFKA),
    ("exactly-once-semantics", "Exactly-once semantics (Kafka)",
     "Kafka's guarantee that a read-process-write loop within Kafka takes effect once, by committing consumed offsets and produced records in a single transaction. It does not extend to side effects in external databases or APIs.", KAFKA),
    ("flaky-test", "Flaky test",
     "A test that passes and fails on the same code without any change. Most flakiness comes from shared test data, timing assumptions, environment dependencies or real race conditions in the product.", "case-studies.html#flaky-tests"),
    ("idempotent-consumer", "Idempotent consumer",
     "A consumer whose processing has the same effect whether a message arrives once or several times. It is usually built by storing a unique message key in the same transaction as the side effect and skipping keys it has already seen.", KAFKA),
    ("llm-output-validation", "LLM output validation",
     "Checking a language model's response before it is used, typically against a schema and business rules, and retrying or falling back when it fails. It stops one malformed response from breaking every step after it.", "case-studies.html#llm-orchestration"),
    ("rl-environment", "RL environment (for coding agents)",
     "A sandboxed software project, usually a repository in a container, where an AI agent attempts a task and a verifier scores the result. The score becomes the reward signal for reinforcement learning or the result of an evaluation.", TASKS),
    ("static-membership", "Static membership (Kafka)",
     "A Kafka consumer setting, group.instance.id, that gives each consumer a stable identity. A consumer that restarts within the session timeout rejoins with its old partitions and does not trigger a rebalance.", KAFKA),
    ("transactional-outbox", "Transactional outbox",
     "A pattern where a service writes an outgoing message to an outbox table in the same database transaction as its state change, and a separate process delivers it. It prevents changes that are saved but never announced, or announced but never saved.", KAFKA),
    ("verifier", "Verifier (AI evaluation)",
     "The automated check that decides whether an AI agent completed a task, such as hidden tests or invariant checks run after the agent finishes. A good verifier checks behaviour, cannot be edited by the agent, and fails plausible but wrong fixes.", TASKS),
]

def faq_html(key, r):
    out = []
    for i, it in enumerate(FAQS[key]):
        link = f' <a href="{r}{it[2]}">{it[3]} →</a>' if len(it) > 3 else ""
        out.append(f'<details{" open" if i == 0 else ""}><summary>{html.escape(it[0])}</summary>'
                   f'<div class="answer"><p>{html.escape(it[1])}{link}</p></div></details>')
    return "\n      ".join(out)

def faq_schema(key):
    return {"@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": it[0], "acceptedAnswer": {"@type": "Answer", "text": it[1]}} for it in FAQS[key]]}

def glossary_html(r):
    az = " ".join(f'<a href="#{slug}">{html.escape(name)}</a>' for slug, name, _, _ in GLOSSARY)
    items = []
    for slug, name, d, link in GLOSSARY:
        more = f'<a class="more" href="{r}{link}">Read more →</a>' if link else ""
        items.append(f'<article class="term" id="{slug}"><h2>{html.escape(name)}</h2><p>{html.escape(d)}</p>{more}</article>')
    return f'<nav class="az" aria-label="Terms">{az}</nav>\n  <div class="terms">\n  ' + "\n  ".join(items) + "\n  </div>"

def crumbs(*items):
    return {"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": f"{SITE}/{p}"} for i, (n, p) in enumerate(items)]}

def offer(name, desc):
    return {"@type": "Offer", "itemOffered": {"@type": "Service", "name": name, "description": desc, "provider": {"@id": f"{SITE}/#person"}}}

def article(path, headline, desc, section):
    return {"@type": "TechArticle", "headline": headline, "description": desc, "articleSection": section,
            "datePublished": PUBLISHED, "dateModified": UPDATED, "inLanguage": "en",
            "author": {"@id": f"{SITE}/#person"}, "publisher": {"@id": f"{SITE}/#person"},
            "image": f"{SITE}/og.png", "mainEntityOfPage": f"{SITE}/{path}"}

# ------------------------------------------------------------------ pages
PAGES = [
    dict(src="index.html", out="index.html", nav="home", faq="index", scripts=["home.js"],
         title="Neeraj Dana · Founder of Profract · Distributed Systems, Real-Time & Production AI",
         desc="Neeraj Dana, founder of Profract, helps startups go from idea to production and helps growing companies scale. 11+ years building distributed systems, real-time platforms and production AI at Atlassian, ServiceNow and Egnyte.",
         schema=lambda: [
             {"@type": "WebSite", "@id": f"{SITE}/#website", "url": f"{SITE}/", "name": "Neeraj Dana", "publisher": {"@id": f"{SITE}/#person"}, "inLanguage": "en"},
             {"@type": "ProfilePage", "@id": f"{SITE}/#profile", "url": f"{SITE}/", "mainEntity": {"@id": f"{SITE}/#person"},
              "dateModified": UPDATED, "isPartOf": {"@id": f"{SITE}/#website"}},
             PERSON,
             dict(ORG, **{"areaServed": "Worldwide", "email": EMAIL, "makesOffer": [
                  offer("MVP to production", "For startups: architecture, hands-on build and launch of a product designed to scale, including AI-first products."),
                  offer("Architecture & scaling", "For startups and mid-size companies: architecture and reliability reviews, fractional technical leadership, and reliability, performance and data-consistency work."),
                  offer("Production AI", "Taking LLM features and agents to production: orchestration, RAG, output validation, evals, latency and cost."),
              ]}),
             faq_schema("index")]),
    dict(src="case-studies.html", out="case-studies.html", nav="cases", faq=None,
         title="Case Studies · Atlassian, Egnyte & ServiceNow · Neeraj Dana",
         desc="Case studies by Neeraj Dana: cutting flaky end-to-end tests by 80% at Atlassian, real-time sync between Egnyte and Google Workspace, a caching layer with 30% lower latency, and LLM orchestration at ServiceNow.",
         schema=lambda: [
             {"@type": "CollectionPage", "name": "Case studies", "url": f"{SITE}/case-studies.html", "author": {"@id": f"{SITE}/#person"}},
             crumbs(("Home", ""), ("Case studies", "case-studies.html"))]),
    dict(src="ai-agent-evaluation.html", out="ai-agent-evaluation.html", nav="ai", faq="ai", scripts=["gauntlet.js"],
         title="AI Agent Evaluation & Coding Task Engineering · Neeraj Dana",
         desc="Hard, verifiable software-engineering tasks and verifiers for AI labs and evaluation teams, built from real distributed-systems failures. Contract work, part-time or full-time.",
         schema=lambda: [
             {"@type": "Service", "name": "AI agent evaluation and coding task engineering", "serviceType": "AI evaluation",
              "provider": {"@id": f"{SITE}/#person"}, "areaServed": "Worldwide", "url": f"{SITE}/ai-agent-evaluation.html",
              "description": "Task environments, verifiers, difficulty calibration and shortcut review for teams training and evaluating coding agents."},
             crumbs(("Home", ""), ("AI agent evaluation", "ai-agent-evaluation.html")),
             faq_schema("ai")]),
    dict(src="notes.html", out="notes.html", nav="notes", faq=None,
         title="Writing on Kafka, Real-Time Systems & AI Evaluation · Neeraj Dana",
         desc="Practical write-ups by Neeraj Dana on event-driven systems, Kafka, real-time sync, production LLM systems and evaluating AI coding agents.",
         schema=lambda: [
             {"@type": "Blog", "name": "Writing", "url": f"{SITE}/notes.html", "author": {"@id": f"{SITE}/#person"}},
             crumbs(("Home", ""), ("Writing", "notes.html"))]),
    dict(src="glossary.html", out="glossary.html", nav="notes", faq=None,
         title="Glossary: Distributed Systems & AI Evaluation Terms · Neeraj Dana",
         desc="Plain-language definitions of at-least-once delivery, idempotent consumers, consumer rebalances, the transactional outbox, verifiers, RL environments and more.",
         schema=lambda: [
             {"@type": "DefinedTermSet", "@id": f"{SITE}/glossary.html#terms", "name": "Distributed systems and AI evaluation glossary",
              "url": f"{SITE}/glossary.html", "author": {"@id": f"{SITE}/#person"}, "dateModified": UPDATED,
              "hasDefinedTerm": [{"@type": "DefinedTerm", "@id": f"{SITE}/glossary.html#{s}", "name": n, "description": d,
                                  "url": f"{SITE}/glossary.html#{s}", "inDefinedTermSet": f"{SITE}/glossary.html#terms"} for s, n, d, _ in GLOSSARY]},
             crumbs(("Home", ""), ("Glossary", "glossary.html"))]),
    dict(src=KAFKA, out=KAFKA, nav="notes", faq="kafka", scripts=["lab.js"], og_type="article",
         title="Why Kafka Consumers Process Messages Twice (and How to Stop It)",
         desc="Kafka consumers process messages twice when the offset commit misses a rebalance or restart. The four causes, the fixes that hold up, and an interactive lab to try it yourself.",
         schema=lambda: [
             article(KAFKA, "Why Kafka consumers process messages twice, and how to stop it",
                     "The four causes of duplicate processing in Kafka consumers and the fixes that hold up under deploys and crashes.", "Distributed systems"),
             crumbs(("Home", ""), ("Writing", "notes.html"), ("Kafka duplicates", KAFKA)),
             faq_schema("kafka")]),
    dict(src=TASKS, out=TASKS, nav="notes", faq="tasks", og_type="article",
         title="Designing Verifiable Coding Tasks for AI Agents",
         desc="How to build coding tasks and verifiers for AI agent training and evaluation: realistic environments, shortcut-resistant hidden tests, reproducible race conditions and difficulty calibration.",
         schema=lambda: [
             article(TASKS, "Designing verifiable coding tasks for AI agents",
                     "How to build coding tasks and verifiers that are hard for the right reasons and can't be gamed.", "AI evaluation"),
             crumbs(("Home", ""), ("Writing", "notes.html"), ("Verifiable coding tasks", TASKS)),
             faq_schema("tasks")]),
    dict(src="404.html", out="404.html", nav=None, faq=None, robots="noindex",
         title="Page not found · Neeraj Dana", desc="This page doesn't exist. Head back to the home page, case studies or writing.",
         schema=lambda: [PERSON]),
]

MARK = ('<svg class="brand-mark" viewBox="0 0 64 64" aria-hidden="true"><rect width="64" height="64" rx="14" fill="var(--accent)"/>'
        '<circle cx="18" cy="32" r="6" fill="var(--on-accent)"/><circle cx="46" cy="18" r="6" fill="var(--on-accent)"/>'
        '<circle cx="46" cy="46" r="6" fill="var(--on-accent)"/><path d="M23 29.5 41 20.5M23 34.5l18 9" stroke="var(--on-accent)" stroke-width="3.5" stroke-linecap="round"/></svg>')

NAV = [("exp", "index.html#experience", "Experience"), ("work", "index.html#services", "Services"),
       ("cases", "case-studies.html", "Case studies"), ("notes", "notes.html", "Writing")]

def header(r, nav):
    items = "".join(f'<a href="{r}{h}"{" aria-current=\"page\"" if k == nav else ""}>{t}</a>' for k, h, t in NAV)
    return (f'<a class="skip" href="#main">Skip to content</a>\n<header class="site-header"><div class="wrap">'
            f'<a class="brand" href="{r}index.html">{MARK}Neeraj Dana</a>'
            f'<nav class="nav" aria-label="Main">{items}<a class="btn btn-primary min-h-10 px-4 text-on-accent no-underline" href="{r}index.html#contact">Contact</a></nav>'
            f'</div></header>')

def footer(r):
    return (f'<footer class="site-footer"><div class="wrap">'
            f'<div><p><strong class="text-ink font-display">Neeraj Dana</strong></p>'
            f'<p>Founder of <a href="https://profract.com">Profract</a>. Distributed, real-time and AI systems. Bengaluru, India · remote worldwide.</p>'
            f'<p class="mt-2 font-mono text-sm select-all">{EMAIL}</p></div>'
            f'<nav aria-label="Footer"><a href="{r}index.html#experience">Experience</a><a href="{r}case-studies.html">Case studies</a>'
            f'<a href="{r}ai-agent-evaluation.html">AI evaluation</a><a href="{r}notes.html">Writing</a><a href="{r}glossary.html">Glossary</a>'
            f'<a href="{LINKEDIN}" rel="me">LinkedIn</a><a href="{GITHUB}" rel="me">GitHub</a></nav>'
            f'<p class="w-full">© 2026 Neeraj Dana</p></div></footer>')

def styles(r, preview):
    if not preview:
        return f'<link rel="stylesheet" href="{r}styles.css">'
    src = "\n".join(l for l in (ROOT / "src" / "input.css").read_text().splitlines() if not l.startswith(("@import", "@source")))
    return f'<script src="{TAILWIND_BROWSER}"></script>\n<style type="text/tailwindcss">\n{src}\n</style>'

def vendor_gsap_available():
    return all((ROOT / "node_modules" / "gsap" / "dist" / f).exists() for f in GSAP_FILES)

def scripts(p, r, preview):
    tags = []
    if p.get("scripts"):
        base = GSAP_CDN if (preview or not vendor_gsap_available()) else f"{r}js/vendor/"
        tags += [f'<script defer src="{base}{f}"></script>' for f in GSAP_FILES]
        tags += [f'<script defer src="{r}js/{s}"></script>' for s in p["scripts"]]
    tags.append(f'<script defer src="{r}js/site.js"></script>')
    return "\n".join(tags)

def head(p, r, preview=False):
    url = f"{SITE}/" if p["out"] == "index.html" else f"{SITE}/{p['out']}"
    graph = json.dumps({"@context": "https://schema.org", "@graph": p["schema"]()}, ensure_ascii=False, indent=1)
    t, d = html.escape(p["title"]), html.escape(p["desc"])
    article_meta = (f'<meta property="article:published_time" content="{PUBLISHED}">\n'
                    f'<meta property="article:modified_time" content="{UPDATED}">\n'
                    f'<meta property="article:author" content="Neeraj Dana">') if p.get("og_type") == "article" else ""
    return f"""<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{t}</title>
<meta name="description" content="{d}">
<link rel="canonical" href="{url}">
<meta name="robots" content="{p.get('robots', 'index, follow, max-image-preview:large, max-snippet:-1')}">
<meta name="author" content="Neeraj Dana">
<meta name="theme-color" content="#F4F5F8" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#0D1016" media="(prefers-color-scheme: dark)">
<meta property="og:type" content="{p.get('og_type', 'profile' if p['out'] == 'index.html' else 'website')}">
<meta property="og:site_name" content="Neeraj Dana">
<meta property="og:title" content="{t}">
<meta property="og:description" content="{d}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{t}">
<meta name="twitter:description" content="{d}">
<meta name="twitter:image" content="{SITE}/og.png">
{article_meta}
<link rel="icon" href="{r}favicon.svg" type="image/svg+xml">
<link rel="alternate" type="text/plain" title="Summary for AI assistants" href="{r}llms.txt">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
{styles(r, preview)}
{scripts(p, r, preview)}
<script type="application/ld+json">
{graph}
</script>"""

def body(p, r):
    src = (ROOT / "pages" / p["src"]).read_text().replace("{{R}}", r)
    src = src.replace("{{UPDATED}}", UPDATED).replace("{{UPDATED_H}}", human_date(UPDATED))
    if p["faq"]:
        src = src.replace("{{FAQ}}", faq_html(p["faq"], r))
    src = src.replace("{{GLOSSARY}}", glossary_html(r))
    assert "{{" not in src, p["src"]
    return f'{header(r, p["nav"])}\n<main id="main">\n{src}\n</main>\n{footer(r)}'

def page_text(p):
    """Plain text of a page's main content, for llms-full.txt."""
    s = body(p, "/")
    s = s[s.index("<main"):s.index("</main>")]
    s = re.sub(r"<(script|style|svg)[\s\S]*?</\1>", " ", s)
    s = re.sub(r"</(p|h1|h2|h3|li|dt|dd|summary|div|tr)>", "\n", s)
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    s = re.sub(r"[ \t]+([,.;:!?])", r"\1", s)
    lines = [re.sub(r"[ \t]+", " ", l).strip() for l in s.splitlines()]
    return "\n".join(l for l in lines if l)

def compile_css():
    cmd = ["npx", "--no-install", "@tailwindcss/cli", "-i", "src/input.css", "-o", str(DIST / "styles.css"), "--minify"]
    try:
        subprocess.run(cmd, cwd=ROOT, check=True)
    except (OSError, subprocess.CalledProcessError):
        if os.environ.get("CI"):
            raise
        print("warning: Tailwind CLI not installed; run `npm install`. dist/styles.css was not built.", file=sys.stderr)

def build():
    for d in (DIST, PREVIEW):
        if d.exists():
            shutil.rmtree(d)
        d.mkdir()
    for p in PAGES:
        r = "/" if p["out"] == "404.html" else "../" * p["out"].count("/")
        for d, pv in ((DIST, False), (PREVIEW, True)):
            rr = "" if (pv and p["out"] == "404.html") else r
            full = f'<!doctype html>\n<html lang="en">\n<head>\n{head(p, rr, pv)}\n</head>\n<body>\n{body(p, rr)}\n</body>\n</html>\n'
            (d / p["out"]).parent.mkdir(parents=True, exist_ok=True)
            (d / p["out"]).write_text(full)
        if p["out"] == "index.html":   # the in-chat preview wraps its entry page itself
            frag = (f'<title>Neeraj Dana Website</title>\n<link rel="stylesheet" href="{FONTS}">\n'
                    f'{styles("", True)}\n{scripts(p, "", True)}\n{body(p, "")}\n')
            (PREVIEW / "index.html").write_text(frag)

    for d in (DIST, PREVIEW):
        shutil.copytree(ROOT / "static", d, dirs_exist_ok=True)
    if vendor_gsap_available():
        (DIST / "js" / "vendor").mkdir(parents=True, exist_ok=True)
        for f in GSAP_FILES:
            shutil.copy(ROOT / "node_modules" / "gsap" / "dist" / f, DIST / "js" / "vendor" / f)

    (DIST / "CNAME").write_text("neerajdana.com\n")
    (DIST / ".nojekyll").write_text("")
    (DIST / f"{INDEXNOW_KEY}.txt").write_text(INDEXNOW_KEY)
    compile_css()

    urls = [("", "1.0"), ("case-studies.html", "0.8"), ("ai-agent-evaluation.html", "0.7"), ("notes.html", "0.6"),
            ("glossary.html", "0.6"), (KAFKA, "0.7"), (TASKS, "0.7")]
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    sm += [f"  <url><loc>{SITE}/{u}</loc><lastmod>{UPDATED}</lastmod><priority>{pr}</priority></url>" for u, pr in urls]
    sm.append("</urlset>")
    (DIST / "sitemap.xml").write_text("\n".join(sm) + "\n")
    (DIST / "urls.txt").write_text("\n".join(f"{SITE}/{u}" for u, _ in urls) + "\n")   # used by the IndexNow ping

    (DIST / "robots.txt").write_text(f"""# Search engines and AI answer engines are welcome.
User-agent: *
Allow: /

User-agent: GPTBot
Allow: /

User-agent: OAI-SearchBot
Allow: /

User-agent: ChatGPT-User
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: Claude-SearchBot
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: Google-Extended
Allow: /

Sitemap: {SITE}/sitemap.xml
""")

    llms = f"""# Neeraj Dana

> Founder of Profract (https://profract.com) and staff-level software engineer based in Bengaluru, India, with 11+ years building production systems at companies including Atlassian, ServiceNow and Egnyte. Specialises in distributed and event-driven systems, real-time data sync and production AI. Through Profract he helps startups go from idea to production and helps startups and mid-size companies scale their systems, remotely worldwide. Contact: {EMAIL}

## About
- [Home and profile]({SITE}/): expertise, experience, what he's open to, and quick facts.
- [Experience]({SITE}/#experience): Atlassian (commerce, 2025–present), ServiceNow (Staff Software Engineer, Generative AI, 2024–2025), Egnyte (Senior Software Developer, 2023–2024), Trianz (Senior Tech Lead, 2020–2023), Kahnputers (Team Lead, 2016–2020), MegaSoft (Senior Software Developer, 2013–2016).
- [Case studies]({SITE}/case-studies.html): 80% fewer flaky end-to-end tests at Atlassian; real-time two-way sync between Egnyte and Google Workspace; Redis caching with 30% lower query latency at Egnyte; LLM orchestration and output validation for ServiceNow's prompt-to-app product.

## Services (through Profract)
- MVP to production, for startups: architecture, hands-on build and launch, including AI-first products.
- Architecture & scaling, for startups and mid-size companies: reviews, fractional technical leadership, reliability, performance and data consistency.
- Production AI: orchestration, RAG, agents, output validation, evals, latency and cost.
- [AI evaluation and coding-task work for AI labs]({SITE}/ai-agent-evaluation.html).

## Writing
- [Why Kafka consumers process messages twice, and how to stop it]({SITE}/{KAFKA})
- [Designing verifiable coding tasks for AI agents]({SITE}/{TASKS})
- [Glossary of distributed systems and AI evaluation terms]({SITE}/glossary.html)

## Full text
- [llms-full.txt]({SITE}/llms-full.txt): every page as plain text.

## Profiles
- LinkedIn: {LINKEDIN}
- GitHub: {GITHUB}
"""
    (DIST / "llms.txt").write_text(llms)
    full = [f"# Neeraj Dana: full site text\n\nSource: {SITE}/ · Updated {UPDATED}\n"]
    for p in PAGES:
        if p["out"] == "404.html":
            continue
        url = f"{SITE}/" if p["out"] == "index.html" else f"{SITE}/{p['out']}"
        full.append(f"\n\n---\n\n## {p['title']}\nURL: {url}\n\n{page_text(p)}")
    (DIST / "llms-full.txt").write_text("".join(full) + "\n")
    for f in ("llms.txt", "llms-full.txt"):
        shutil.copy(DIST / f, PREVIEW / f)
    make_og(DIST / "og.png")
    shutil.copy(DIST / "og.png", PREVIEW / "og.png")

def make_og(path):
    from PIL import Image, ImageDraw, ImageFont
    W, H = 1200, 630
    im = Image.new("RGB", (W, H), "#0D1016")
    d = ImageDraw.Draw(im)
    fonts = "/usr/share/fonts/truetype/dejavu/"
    bold, mono = ImageFont.truetype(fonts + "DejaVuSans-Bold.ttf", 96), ImageFont.truetype(fonts + "DejaVuSansMono.ttf", 26)
    d.rectangle([0, 0, 14, H], fill="#8FA8FF")
    d.text((80, 90), "FOUNDER, PROFRACT · 11+ YEARS IN PRODUCTION", font=mono, fill="#A6AEBD")
    d.text((80, 150), "Neeraj Dana", font=bold, fill="#E6E9EF")
    sub = ImageFont.truetype(fonts + "DejaVuSans.ttf", 38)
    d.text((80, 285), "Distributed systems · real-time platforms", font=sub, fill="#8FA8FF")
    d.text((80, 340), "production AI", font=sub, fill="#8FA8FF")
    d.line([80, 450, 1120, 450], fill="#262E3B", width=2)
    d.text((80, 485), "Atlassian · ServiceNow · Egnyte", font=ImageFont.truetype(fonts + "DejaVuSans-Bold.ttf", 30), fill="#E6E9EF")
    d.text((80, 540), "MVP to production · architecture & scaling · neerajdana.com", font=mono, fill="#A6AEBD")
    im.save(path, optimize=True)

if __name__ == "__main__":
    build()
    print("built", sorted(str(p.relative_to(DIST)) for p in DIST.rglob("*") if p.is_file()))
