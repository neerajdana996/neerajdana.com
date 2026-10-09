# neerajdana.com

Static site: plain HTML pages, Tailwind CSS v4 compiled at build time, deployed to GitHub Pages.

## Edit
- Page content: `pages/` (home, case studies, AI evaluation, field notes, 404)
- Styles and design tokens: `src/input.css` (Tailwind utilities such as `text-ink-2`, `bg-surface`, `font-display` work in any page)
- Titles, meta descriptions, FAQs, structured data, sitemap, robots.txt, llms.txt: `build.py`

## Build locally
```
npm install
python3 build.py      # writes dist/
```

## Deploy
Every push to `main` runs `.github/workflows/deploy.yml`, which builds and publishes `dist/` to GitHub Pages.

## Domain
DNS at the registrar for neerajdana.com:
- A records for `@`: 185.199.108.153, 185.199.109.153, 185.199.110.153, 185.199.111.153
- AAAA records for `@`: 2606:50c0:8000::153, 2606:50c0:8001::153, 2606:50c0:8002::153, 2606:50c0:8003::153
- CNAME for `www`: `<github-username>.github.io`
