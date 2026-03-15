# Analysis Document Templates

> Standard output structure for `.hypercore/crawler/[site-name]/`.

---

## Folder Structure

```text
.hypercore/crawler/example-com/
├── ANALYSIS.md      # Site structure and crawl strategy
├── SELECTORS.md     # DOM selector inventory
├── API.md           # API endpoint map
├── NETWORK.md       # Auth/network details
└── CRAWLER.ts       # Generated implementation
```

---

## ANALYSIS.md

```markdown
# [Site Name] Crawl Analysis

Created: {{TIMESTAMP}}
URL: {{BASE_URL}}

## Page Types

| Type | URL | Notes |
|------|-----|------|
| List | /items | |
| Detail | /items/[id] | |
| Search | /search?q= | |

## Data Loading

- [ ] SSR
- [ ] CSR (API-driven)
- [ ] Infinite scroll
- [ ] Pagination

## Authentication

- [ ] Public
- [ ] Login required
- [ ] API key required

## Findings

[Key constraints, edge cases, warnings]
```

---

## SELECTORS.md

```markdown
# [Site Name] Selectors

## List Page

| Element | Selector | Notes |
|------|------|------|
| Container | `.item-list` | |
| Card | `.item-card` | |
| Title | `.item-card h2` | |
| Link | `.item-card a` | |
| Next | `button[aria-label="Next"]` | |

## aria-ref Mapping

| ref | Selector | Meaning |
|------|------|------|
| e14 | `getByRole('button', { name: 'Load more' })` | Load more |
```

---

## API.md

```markdown
# [Site Name] API

## Endpoint Summary

| Method | Endpoint | Purpose |
|------|------|------|
| GET | /api/items | Fetch item list |
| GET | /api/items/:id | Fetch item detail |

## Query Parameters

| Parameter | Type | Description |
|------|------|------|
| page | number | Page index |
| limit | number | Page size |

## Rate Limit / Constraints

[Rate limit, anti-bot checks, auth constraints]
```

---

## NETWORK.md

```markdown
# [Site Name] Network

## Authentication Data

| Field | Value | Expires |
|------|------|------|
| Cookie | session=... | 24h |
| Bearer Token | ey... | 1h |

## Required Headers

- User-Agent: ...
- Accept-Language: ...
- Referer: ...

## Limits

- Rate limit: 60 req/min
- Delay: 1000ms

## Bot Detection

[Cloudflare, CAPTCHA, behavioral constraints]
```
