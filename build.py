"""Builds the static site into dist/ (deploy) and preview/ (artifact preview).

Change SITE to your real domain before deploying, then run: python3 build.py
"""
import html, json, os, re, shutil, subprocess, sys
from pathlib import Path

SITE = "https://neerajdana.com"          # <- your domain, no trailing slash
EMAIL = "neerajdana9@gmail.com"
LINKEDIN = "https://linkedin.com/in/neeraj-dana"
GITHUB = "https://github.com/neerajdana996"
PUBLISHED = "2026-10-09"

ROOT = Path(__file__).parent
DIST = ROOT / "dist"
PREVIEW = ROOT / "preview"

TAILWIND_BROWSER = "https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4.1.11"   # preview only, never production

FONTS = ("https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500..700"
         "&family=Source+Serif+4:opsz,wght@8..60,400..600&family=JetBrains+Mono:wght@400;500&display=swap")

PERSON = {
    "@type": "Person",
    "@id": f"{SITE}/#person",
    "name": "Neeraj Dana",
    "url": f"{SITE}/",
    "image": f"{SITE}/og.png",
    "jobTitle": "Independent Software Engineer, Distributed and Real-Time Systems",
    "email": f"mailto:{EMAIL}",
    "sameAs": [LINKEDIN, GITHUB],
    "knowsAbout": [
        "Distributed systems", "Event-driven architecture", "Apache Kafka", "Real-time data synchronization",
        "Microservices", "Caching with Redis", "Site reliability and incident response",
        "Large language model orchestration", "Retrieval-augmented generation", "AI agent evaluation",
        "Reinforcement learning environments for coding agents", "TypeScript", "Node.js", "Python", "Go",
    ],
    "homeLocation": {"@type": "Country", "name": "India"},
}

# ---------------------------------------------------------------- FAQs (one source for HTML and schema)
FAQS = {
    "index": [
        ("What does a distributed systems consultant do?",
         "A distributed systems consultant reviews, designs and fixes software that runs across several services, queues and databases, where failures, retries and timing can lose, duplicate or reorder data. I map how data moves through your system, find where its guarantees break, and either fix it hands-on or give your team a ranked plan to fix it."),
        ("How do you price an engagement?",
         "Architecture reviews are a fixed fee, fractional work is a monthly retainer, and build sprints are priced per sprint or hourly. Every engagement starts with a free 30-minute call, after which I send a written proposal with a fixed scope and price."),
        ("Why does my Kafka consumer process the same message twice?",
         "Because the consumer finished the work but its offset commit didn't happen before a rebalance or restart, so the next owner resumed from the old offset. That is Kafka's at-least-once delivery. The durable fix is idempotent processing: store a deduplication key in the same transaction as the side effect.",
         "notes/kafka-consumer-duplicate-messages-rebalance.html", "Read the full explanation"),
        ("Do you work with early-stage startups?",
         "Yes. Seed to Series B teams are a strong fit: they have outgrown their first architecture but don't yet have a staff engineer for the hard parts. Larger companies bring me in for focused reviews or a specific system."),
        ("Can you work in our time zone?",
         "I'm based in India and work remotely. My working day overlaps fully with European business hours, and I schedule calls in US mornings or evenings as needed."),
        ("Do you sign NDAs?",
         "Yes, and I keep them. That is why this site describes problems and results without naming clients or employers."),
        ("Which technologies do you work with?",
         "TypeScript, Node.js, Python and Go; Kafka and event-driven microservices; PostgreSQL, MongoDB, Redis and Qdrant; AWS and Azure; LangChain and LangGraph for LLM systems; and Playwright for end-to-end testing."),
    ],
    "ai": [
        ("What is an RL environment for a coding agent?",
         "It is a sandboxed software project, usually a repository running in a container, that an AI agent works in to complete a task. A verifier then checks the result automatically, which produces the reward signal used in reinforcement learning or the score used in an evaluation."),
        ("What makes a good verifier for a coding task?",
         "It checks behaviour rather than matching a reference diff, runs outside the agent's reach, fails every known wrong-but-plausible fix, and gives the same result every time it runs. For timing bugs, that means fault injection and fixed seeds."),
        ("How do you stop agents from gaming a task?",
         "Hidden tests run in a clean step after the agent finishes, the agent's diff is checked for edits to tests and fixtures, the answer is kept out of git history and comments, and I confirm that shortcuts such as sleeps, retries or hard-coded outputs all fail."),
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

def faq_html(key, r):
    out = []
    for i, item in enumerate(FAQS[key]):
        q, a = item[0], item[1]
        link = f' <a href="{r}{item[2]}">{item[3]} →</a>' if len(item) > 3 else ""
        out.append(f'<details{" open" if i == 0 else ""}><summary>{html.escape(q)}</summary>'
                   f'<div class="answer"><p>{html.escape(a)}{link}</p></div></details>')
    return "\n      ".join(out)

def faq_schema(key):
    return {"@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": it[0], "acceptedAnswer": {"@type": "Answer", "text": it[1]}} for it in FAQS[key]]}

def crumbs(*items):
    return {"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": f"{SITE}/{p}"} for i, (n, p) in enumerate(items)]}

def offer(name, desc):
    return {"@type": "Offer",
            "itemOffered": {"@type": "Service", "name": name, "description": desc, "provider": {"@id": f"{SITE}/#person"}}}

def article(path, headline, desc, section):
    return {"@type": "TechArticle", "headline": headline, "description": desc, "articleSection": section,
            "datePublished": PUBLISHED, "dateModified": PUBLISHED, "inLanguage": "en",
            "author": {"@id": f"{SITE}/#person"}, "publisher": {"@id": f"{SITE}/#person"},
            "image": f"{SITE}/og.png", "mainEntityOfPage": f"{SITE}/{path}"}

# ---------------------------------------------------------------- pages
PAGES = [
    dict(src="index.html", out="index.html", nav="home", faq="index",
         title="Neeraj Dana · Distributed & Real-Time Systems Engineer",
         desc="Independent staff-level engineer who fixes event-driven and real-time systems: duplicate and lost messages, consumer lag, sync drift, caching and production LLM features.",
         schema=lambda: [
             {"@type": "WebSite", "@id": f"{SITE}/#website", "url": f"{SITE}/", "name": "Neeraj Dana", "publisher": {"@id": f"{SITE}/#person"}, "inLanguage": "en"},
             PERSON,
             {"@type": "ProfessionalService", "@id": f"{SITE}/#service", "name": "Neeraj Dana, distributed systems consulting",
              "url": f"{SITE}/", "image": f"{SITE}/og.png", "founder": {"@id": f"{SITE}/#person"}, "areaServed": "Worldwide",
              "email": EMAIL,
              "description": "Architecture reviews, fractional staff engineering and hands-on fixes for event-driven, real-time and LLM systems.",
              "makesOffer": [
                  offer("Architecture & reliability review", "Two-week fixed-scope review of an event-driven or real-time system with a ranked fix plan."),
                  offer("Fractional staff engineer", "One to two days a week of senior technical leadership and hands-on work."),
                  offer("Build & fix sprints", "Hands-on implementation: idempotent consumers, real-time sync, caching, LLM orchestration and evals."),
                  offer("AI agent evaluation tasks", "Verifiable software-engineering tasks and verifiers for training and evaluating coding agents."),
              ]},
             faq_schema("index")]),
    dict(src="case-studies.html", out="case-studies.html", nav="cases", faq=None,
         title="Case Studies · Distributed Systems, Real-Time Sync & LLM Orchestration · Neeraj Dana",
         desc="Anonymised case studies: cutting flaky end-to-end tests by 80%, real-time bidirectional sync across two platforms, a caching layer with 30% lower latency, and LLM orchestration.",
         schema=lambda: [
             {"@type": "CollectionPage", "name": "Case studies", "url": f"{SITE}/case-studies.html", "author": {"@id": f"{SITE}/#person"}},
             crumbs(("Home", ""), ("Case studies", "case-studies.html"))]),
    dict(src="ai-agent-evaluation.html", out="ai-agent-evaluation.html", nav="ai", faq="ai",
         title="AI Agent Evaluation & RL Environment Tasks for Coding Agents · Neeraj Dana",
         desc="Hard, verifiable software-engineering tasks and verifiers for AI labs and evaluation teams, built from real distributed-systems failures. Hourly, sprint or full-time contract.",
         schema=lambda: [
             {"@type": "Service", "name": "AI agent evaluation and coding task engineering", "serviceType": "AI evaluation",
              "provider": {"@id": f"{SITE}/#person"}, "areaServed": "Worldwide", "url": f"{SITE}/ai-agent-evaluation.html",
              "description": "Task environments, verifiers, difficulty calibration and shortcut review for teams training and evaluating coding agents."},
             crumbs(("Home", ""), ("AI agent evaluation", "ai-agent-evaluation.html")),
             faq_schema("ai")]),
    dict(src="notes.html", out="notes.html", nav="notes", faq=None,
         title="Field Notes on Kafka, Real-Time Systems & AI Evaluation · Neeraj Dana",
         desc="Practical write-ups on event-driven systems, Kafka, real-time sync, production LLM systems and evaluating AI coding agents.",
         schema=lambda: [
             {"@type": "Blog", "name": "Field notes", "url": f"{SITE}/notes.html", "author": {"@id": f"{SITE}/#person"}},
             crumbs(("Home", ""), ("Field notes", "notes.html"))]),
    dict(src="notes/kafka-consumer-duplicate-messages-rebalance.html", out="notes/kafka-consumer-duplicate-messages-rebalance.html", nav="notes", faq="kafka",
         title="Why Kafka Consumers Process Messages Twice (and How to Stop It)",
         desc="Kafka consumers process messages twice when the offset commit misses a rebalance or restart. The four causes, and the fixes: idempotent processing, commit on revoke, cooperative rebalancing and static membership.",
         og_type="article",
         schema=lambda: [
             article("notes/kafka-consumer-duplicate-messages-rebalance.html", "Why Kafka consumers process messages twice, and how to stop it",
                     "The four causes of duplicate processing in Kafka consumers and the fixes that hold up under deploys and crashes.", "Distributed systems"),
             crumbs(("Home", ""), ("Field notes", "notes.html"), ("Kafka duplicates", "notes/kafka-consumer-duplicate-messages-rebalance.html")),
             faq_schema("kafka")]),
    dict(src="notes/designing-verifiable-coding-tasks-for-ai-agents.html", out="notes/designing-verifiable-coding-tasks-for-ai-agents.html", nav="notes", faq="tasks",
         title="Designing Verifiable Coding Tasks for AI Agents",
         desc="How to build coding tasks and verifiers for AI agent training and evaluation: realistic environments, shortcut-resistant hidden tests, reproducible race conditions and difficulty calibration.",
         og_type="article",
         schema=lambda: [
             article("notes/designing-verifiable-coding-tasks-for-ai-agents.html", "Designing verifiable coding tasks for AI agents",
                     "How to build coding tasks and verifiers that are hard for the right reasons and can't be gamed.", "AI evaluation"),
             crumbs(("Home", ""), ("Field notes", "notes.html"), ("Verifiable coding tasks", "notes/designing-verifiable-coding-tasks-for-ai-agents.html")),
             faq_schema("tasks")]),
]

PAGES.append(dict(src="404.html", out="404.html", nav=None, faq=None, robots="noindex",
                  title="Page not found · Neeraj Dana", desc="This page doesn't exist. Head back to the home page, case studies or field notes.",
                  schema=lambda: [PERSON]))

MARK = ('<svg class="brand-mark" viewBox="0 0 64 64" aria-hidden="true"><rect width="64" height="64" rx="14" fill="var(--accent)"/>'
        '<circle cx="18" cy="32" r="6" fill="var(--on-accent)"/><circle cx="46" cy="18" r="6" fill="var(--on-accent)"/>'
        '<circle cx="46" cy="46" r="6" fill="var(--on-accent)"/><path d="M23 29.5 41 20.5M23 34.5l18 9" stroke="var(--on-accent)" stroke-width="3.5" stroke-linecap="round"/></svg>')

def header(r, nav):
    links = [("services", "index.html#services", "Services"), ("cases", "case-studies.html", "Case studies"),
             ("ai", "ai-agent-evaluation.html", "AI evaluation"), ("notes", "notes.html", "Field notes")]
    items = "".join(f'<a href="{r}{h}"{" aria-current=\"page\"" if k == nav else ""}>{t}</a>' for k, h, t in links)
    return (f'<a class="skip" href="#main">Skip to content</a>\n<header class="site-header"><div class="wrap">'
            f'<a class="brand" href="{r}index.html">{MARK}Neeraj Dana</a>'
            f'<nav class="nav" aria-label="Main">{items}<a class="btn btn-primary min-h-10 px-4 text-on-accent no-underline" href="{r}index.html#contact">Contact</a></nav>'
            f'</div></header>')

def footer(r):
    return (f'<footer class="site-footer"><div class="wrap">'
            f'<div><p><strong class="text-ink font-display">Neeraj Dana</strong></p>'
            f'<p>Independent engineer for event-driven, real-time and AI systems. Remote, worldwide.</p>'
            f'<p class="mt-2 font-mono text-sm select-all">{EMAIL}</p></div>'
            f'<nav aria-label="Footer"><a href="{r}index.html#services">Services</a><a href="{r}case-studies.html">Case studies</a>'
            f'<a href="{r}ai-agent-evaluation.html">AI evaluation</a><a href="{r}notes.html">Field notes</a>'
            f'<a href="{LINKEDIN}" rel="me">LinkedIn</a><a href="{GITHUB}" rel="me">GitHub</a></nav>'
            f'<p class="w-full">© 2026 Neeraj Dana</p></div></footer>')

COPY_JS = """<script>
(function(){var b=document.getElementById('copy-email');if(!b)return;b.addEventListener('click',function(){var t=b.getAttribute('data-copy');
function done(m){b.textContent=m;setTimeout(function(){b.textContent='Copy';},1800);}
function sel(){var o=document.getElementById('email');var r=document.createRange();r.selectNodeContents(o);var s=window.getSelection();s.removeAllRanges();s.addRange(r);done('Selected');}
try{navigator.clipboard.writeText(t).then(function(){done('Copied');},sel);}catch(e){sel();}});})();
</script>"""

def styles(r, preview):
    """Production links the compiled stylesheet. The in-chat preview cannot run the
    Tailwind CLI, so it compiles the same source in the browser instead."""
    if not preview:
        return f'<link rel="stylesheet" href="{r}styles.css">'
    src = "\n".join(l for l in (ROOT / "src" / "input.css").read_text().splitlines()
                    if not l.startswith(("@import", "@source")))
    return f'<script src="{TAILWIND_BROWSER}"></script>\n<style type="text/tailwindcss">\n{src}\n</style>'

def head(p, r, preview=False):
    url = f"{SITE}/" if p["out"] == "index.html" else f"{SITE}/{p['out']}"
    graph = json.dumps({"@context": "https://schema.org", "@graph": p["schema"]()}, ensure_ascii=False, indent=1)
    t, d = html.escape(p["title"]), html.escape(p["desc"])
    return f"""<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{t}</title>
<meta name="description" content="{d}">
<link rel="canonical" href="{url}">
<meta name="robots" content="{p.get('robots', 'index, follow, max-image-preview:large, max-snippet:-1')}">
<meta name="author" content="Neeraj Dana">
<meta name="theme-color" content="#F4F5F8" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#0D1016" media="(prefers-color-scheme: dark)">
<meta property="og:type" content="{p.get('og_type', 'website')}">
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
{"<meta property=\"article:published_time\" content=\"" + PUBLISHED + "\">" if p.get("og_type") == "article" else ""}
<link rel="icon" href="{r}favicon.svg" type="image/svg+xml">
<link rel="alternate" type="text/plain" title="LLM summary" href="{r}llms.txt">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
{styles(r, preview)}
<script type="application/ld+json">
{graph}
</script>"""

def body(p, r):
    src = (ROOT / "pages" / p["src"]).read_text()
    src = src.replace("{{R}}", r)
    if p["faq"]:
        src = src.replace("{{FAQ}}", faq_html(p["faq"], r))
    assert "{{" not in src, p["src"]
    return f"{header(r, p['nav'])}\n<main id=\"main\">\n{src}\n</main>\n{footer(r)}\n{COPY_JS if 'copy-email' in src else ''}"

def build():
    for d in (DIST, PREVIEW):
        if d.exists():
            shutil.rmtree(d)
        d.mkdir()
    for p in PAGES:
        r = "/" if p["out"] == "404.html" else "../" * p["out"].count("/")   # 404 is served at any depth
        for d, pv in ((DIST, False), (PREVIEW, True)):
            full = f'<!doctype html>\n<html lang="en">\n<head>\n{head(p, r, pv)}\n</head>\n<body>\n{body(p, r)}\n</body>\n</html>\n'
            (d / p["out"]).parent.mkdir(parents=True, exist_ok=True)
            (d / p["out"]).write_text(full)
        if p["out"] == "index.html":
            # artifact preview wraps the main page in its own skeleton: give it a body fragment
            frag = (f'<title>Neeraj Dana Website</title>\n<link rel="stylesheet" href="{FONTS}">\n'
                    f'{styles("", True)}\n{body(p, "")}\n')
            (PREVIEW / "index.html").write_text(frag)
    for f in (ROOT / "static").iterdir():
        for d in (DIST, PREVIEW):
            shutil.copy(f, d / f.name)

    (DIST / "CNAME").write_text("neerajdana.com\n")
    (DIST / ".nojekyll").write_text("")
    compile_css()

    urls = [("", "1.0"), ("case-studies.html", "0.8"), ("ai-agent-evaluation.html", "0.8"), ("notes.html", "0.6"),
            ("notes/kafka-consumer-duplicate-messages-rebalance.html", "0.7"),
            ("notes/designing-verifiable-coding-tasks-for-ai-agents.html", "0.7")]
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    sm += [f"  <url><loc>{SITE}/{u}</loc><lastmod>{PUBLISHED}</lastmod><priority>{pr}</priority></url>" for u, pr in urls]
    sm.append("</urlset>")
    (DIST / "sitemap.xml").write_text("\n".join(sm) + "\n")

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

    (DIST / "llms.txt").write_text(f"""# Neeraj Dana

> Independent staff-level software engineer (11+ years) who designs and fixes event-driven, real-time and production AI systems for startups, product teams and AI labs. Based in India, works remotely worldwide. Contact: {EMAIL}

## Services
- [Architecture & reliability review]({SITE}/#services): two-week fixed-scope review of an event-driven or real-time system with a ranked fix plan.
- [Fractional staff engineer]({SITE}/#services): one to two days a week of senior technical leadership.
- [Build & fix sprints]({SITE}/#services): idempotent consumers, real-time sync, caching, LLM orchestration and evals.
- [AI agent evaluation]({SITE}/ai-agent-evaluation.html): verifiable software-engineering tasks, environments and verifiers for training and evaluating coding agents.

## Expertise
Distributed systems, event-driven architecture, Apache Kafka, real-time bidirectional sync, Redis caching, microservices, incident response, LLM orchestration and output validation, RAG, AI agent evaluation. Languages: TypeScript, Node.js, Python, Go.

## Case studies
- [Case studies]({SITE}/case-studies.html): flaky end-to-end tests cut by 80% on a commerce platform; real-time bidirectional sync between two platforms; caching layer with 30% lower query latency; LLM orchestration for a prompt-to-app product. Client names withheld under NDA.

## Field notes
- [Why Kafka consumers process messages twice, and how to stop it]({SITE}/notes/kafka-consumer-duplicate-messages-rebalance.html)
- [Designing verifiable coding tasks for AI agents]({SITE}/notes/designing-verifiable-coding-tasks-for-ai-agents.html)

## Profiles
- LinkedIn: {LINKEDIN}
- GitHub: {GITHUB}
""")
    shutil.copy(DIST / "llms.txt", PREVIEW / "llms.txt")
    make_og(DIST / "og.png")
    shutil.copy(DIST / "og.png", PREVIEW / "og.png")

def compile_css():
    cmd = ["npx", "--no-install", "@tailwindcss/cli", "-i", "src/input.css", "-o", str(DIST / "styles.css"), "--minify"]
    try:
        subprocess.run(cmd, cwd=ROOT, check=True)
    except (OSError, subprocess.CalledProcessError):
        if os.environ.get("CI"):
            raise
        print("warning: Tailwind CLI not installed; run `npm install` first. dist/styles.css was not built.", file=sys.stderr)

def make_og(path):
    from PIL import Image, ImageDraw, ImageFont
    W, H = 1200, 630
    im = Image.new("RGB", (W, H), "#0D1016")
    d = ImageDraw.Draw(im)
    bold = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    mono = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
    f_eyebrow, f_h, f_name = ImageFont.truetype(mono, 24), ImageFont.truetype(bold, 58), ImageFont.truetype(bold, 34)
    d.rectangle([0, 0, 14, H], fill="#8FA8FF")
    d.text((80, 80), "INDEPENDENT ENGINEER · DISTRIBUTED & REAL-TIME SYSTEMS", font=f_eyebrow, fill="#A6AEBD")
    lines = ["When your events arrive twice,", "late, or out of order,", "I find out why and fix it."]
    y = 170
    for i, ln in enumerate(lines):
        d.text((80, y), ln, font=f_h, fill="#8FA8FF" if i == 1 else "#E6E9EF")
        y += 76
    d.line([80, 470, 1120, 470], fill="#262E3B", width=2)
    d.text((80, 500), "Neeraj Dana", font=f_name, fill="#E6E9EF")
    d.text((80, 552), "Kafka · real-time sync · production LLM systems · AI agent evaluation", font=ImageFont.truetype(mono, 22), fill="#A6AEBD")
    im.save(path, optimize=True)

if __name__ == "__main__":
    build()
    print("built", sorted(str(p.relative_to(DIST)) for p in DIST.rglob("*") if p.is_file()))
