# Anti-Bot Evasion Checklist

> Techniques to avoid detection when crawling protected sites.

---

## 1. Browser Fingerprint

### User-Agent

```
[ ] Use recent, real browser User-Agent strings
[ ] Rotate User-Agents between requests
[ ] Match User-Agent to actual browser capabilities
```

```typescript
const USER_AGENTS = [
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
  'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
];

function randomUA(): string {
  return USER_AGENTS[Math.floor(Math.random() * USER_AGENTS.length)];
}
```

### WebDriver Detection

```
[ ] Override navigator.webdriver property
[ ] Remove automation-related window properties
[ ] Patch Chrome DevTools Protocol detection
```

```typescript
// Playwright stealth setup
await page.addInitScript(() => {
  Object.defineProperty(navigator, 'webdriver', { get: () => false });
  // Remove automation indicators
  delete (window as Record<string, unknown>).__playwright;
  delete (window as Record<string, unknown>).__pw_manual;
});
```

### Canvas / WebGL Fingerprint

```
[ ] Use consistent canvas rendering
[ ] Don't block canvas — it flags as bot
[ ] Match GPU renderer to User-Agent OS
```

---

## 2. Behavioral Patterns

### Timing

```
[ ] Add random delays between requests (1-5s)
[ ] Vary delay duration (not fixed intervals)
[ ] Add longer pauses periodically (simulating reading)
[ ] Don't crawl faster than a human could browse
```

```typescript
async function humanDelay(minMs = 1000, maxMs = 5000): Promise<void> {
  const delay = Math.floor(Math.random() * (maxMs - minMs) + minMs);
  await new Promise((r) => setTimeout(r, delay));
}

// Occasionally take a longer break
async function maybeRest(): Promise<void> {
  if (Math.random() < 0.1) {
    await humanDelay(10000, 30000); // 10-30s break
  }
}
```

### Mouse / Scroll Simulation

```
[ ] Move mouse to elements before clicking
[ ] Use bezier curves for mouse movement (not linear)
[ ] Scroll gradually, not instantly
[ ] Simulate viewport-appropriate scroll distances
```

```typescript
// Gradual scroll simulation
async function humanScroll(page: Page): Promise<void> {
  const scrollHeight = await page.evaluate(() => document.body.scrollHeight);
  let currentPosition = 0;

  while (currentPosition < scrollHeight) {
    const scrollAmount = Math.floor(Math.random() * 300 + 200);
    currentPosition += scrollAmount;
    await page.evaluate((y) => window.scrollTo(0, y), currentPosition);
    await humanDelay(500, 1500);
  }
}
```

---

## 3. Network Patterns

### Headers

```
[ ] Send realistic Accept headers
[ ] Include Accept-Language matching geo
[ ] Send proper Referer chain
[ ] Include sec-ch-ua headers for Chrome
```

```typescript
const REALISTIC_HEADERS = {
  Accept:
    'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
  'Accept-Language': 'en-US,en;q=0.9',
  'Accept-Encoding': 'gzip, deflate, br',
  'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
  'sec-ch-ua-mobile': '?0',
  'sec-ch-ua-platform': '"macOS"',
  'Sec-Fetch-Dest': 'document',
  'Sec-Fetch-Mode': 'navigate',
  'Sec-Fetch-Site': 'none',
  'Sec-Fetch-User': '?1',
};
```

### Connection Patterns

```
[ ] Reuse connections (keep-alive)
[ ] Don't open too many parallel connections
[ ] Use HTTP/2 if the site supports it
[ ] Rotate IPs if needed (proxy pool)
```

---

## 4. CAPTCHA Handling

| Type | Detection | Strategy |
|------|------|------|
| reCAPTCHA v2 | iframe with `recaptcha` | Manual solve or service |
| reCAPTCHA v3 | Score-based, invisible | Behavioral mimicry |
| hCaptcha | iframe with `hcaptcha` | Manual solve or service |
| Custom CAPTCHA | Image challenge | OCR or manual |
| Cloudflare Turnstile | `cf-turnstile` div | Wait + cookie extraction |

```
[ ] Detect CAPTCHA presence before proceeding
[ ] Implement CAPTCHA detection callback
[ ] Have fallback strategy (manual intervention)
[ ] Don't retry rapidly on CAPTCHA — it increases difficulty
```

---

## 5. Detection Test

Before running full crawl, verify stealth:

```
[ ] Test against bot detection sites:
    - https://bot.sannysoft.com
    - https://fingerprint.com/demo
    - https://abrahamjuliot.github.io/creepjs/
[ ] Compare fingerprint with real browser
[ ] Verify no automation flags in navigator
[ ] Check that cookies are properly set
```

```bash
# Quick detection test
# Run your crawler against bot detection test page
# Compare output with manual browser visit
```

---

## Priority by Protection Level

| Protection Level | Required Measures |
|------|------|
| None | Basic headers, reasonable delays |
| Low (simple checks) | User-Agent rotation, realistic headers |
| Medium (Cloudflare) | Full header set, delays, cookie handling |
| High (DataDome, PerimeterX) | Browser automation, fingerprint spoofing, proxies |
| Extreme (custom ML detection) | Consider if crawling is appropriate |
