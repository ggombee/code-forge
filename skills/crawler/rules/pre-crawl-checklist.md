# Pre-Crawl Analysis Checklist

> Mandatory checks before writing any crawler code.

---

## 1. Rendering Check

Determine how the page renders its content.

```
[ ] Open target URL in browser
[ ] View Page Source (Ctrl+U) — check if data is in raw HTML
[ ] Compare source vs rendered DOM (DevTools Elements tab)
```

| Result | Meaning | Approach |
|------|------|------|
| Data in source | SSR | DOM parsing or API |
| Data NOT in source | CSR (JavaScript-rendered) | API intercept or Playwright |
| Partial data in source | Hybrid | Check both approaches |

---

## 2. Bot Detection Check

```
[ ] Open DevTools Network tab
[ ] Look for Cloudflare/Akamai/DataDome challenge pages
[ ] Check for CAPTCHA on first load
[ ] Try fetching with curl — does it return same content?
```

```bash
# Quick bot detection test
curl -s -o /dev/null -w "%{http_code}" "https://target.com"
# 403/503 = likely bot protection
# 200 = probably accessible
```

| Detection | Sign | Mitigation |
|------|------|------|
| Cloudflare | `cf-` cookies, challenge page | Nstbrowser or session cookies |
| DataDome | `datadome` cookie | Rotate proxies, browser profile |
| Custom WAF | 403 on curl, works in browser | Full browser automation |
| None | curl returns 200 with data | Simple fetch is fine |

---

## 3. Honeypot Check

```
[ ] Inspect links — any hidden links (display:none, visibility:hidden)?
[ ] Check for invisible form fields
[ ] Look for links with suspicious paths (/trap, /honeypot, /admin)
```

```typescript
// Honeypot detection in crawler
const isHoneypot = (element: Element): boolean => {
  const style = window.getComputedStyle(element);
  return (
    style.display === 'none' ||
    style.visibility === 'hidden' ||
    style.opacity === '0' ||
    (element as HTMLElement).offsetHeight === 0
  );
};
```

---

## 4. Rate Limit Discovery

```
[ ] Check response headers for rate limit info
[ ] Look for X-RateLimit-*, Retry-After headers
[ ] Test rapid requests — at what point do you get 429?
[ ] Check robots.txt for Crawl-delay directive
```

```bash
# Check robots.txt
curl -s "https://target.com/robots.txt"

# Check rate limit headers
curl -sI "https://target.com/api/items" | grep -i "rate\|limit\|retry"
```

| Header | Meaning |
|------|------|
| `X-RateLimit-Limit` | Max requests per window |
| `X-RateLimit-Remaining` | Requests left |
| `X-RateLimit-Reset` | Window reset timestamp |
| `Retry-After` | Seconds to wait |

---

## 5. Authentication Analysis

```
[ ] Is the page public or login-required?
[ ] Check cookies after login (DevTools > Application > Cookies)
[ ] Check for Bearer tokens in API requests
[ ] Identify token refresh mechanism
```

| Auth Type | Storage | Extraction Method |
|------|------|------|
| Session cookie | Cookie | Copy from browser DevTools |
| JWT Bearer | Header | Copy from Network tab |
| API key | Query param / Header | Find in page source or docs |
| OAuth | Header | Token exchange flow |

---

## 6. API Discovery

```
[ ] Open DevTools Network tab, filter by XHR/Fetch
[ ] Navigate through the site — watch for API calls
[ ] Check for GraphQL endpoint (/graphql)
[ ] Look for REST patterns (/api/v1/...)
[ ] Inspect request/response payloads
```

### API Documentation Checklist

For each discovered API endpoint:

```
[ ] Method (GET/POST/PUT/DELETE)
[ ] URL pattern
[ ] Required headers
[ ] Query parameters / request body
[ ] Response structure (fields, types)
[ ] Pagination mechanism
[ ] Error response format
```

---

## Decision Matrix

After completing checks, decide approach:

| Condition | Decision |
|------|------|
| API found + no bot protection | Use API directly with fetch |
| API found + cookie auth | Use API with extracted cookies |
| No API + SSR content | Playwright DOM crawling |
| No API + CSR + bot protection | Nstbrowser or manual session |
| Heavy bot protection everywhere | Consider if crawling is feasible |
