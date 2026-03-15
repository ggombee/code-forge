# Network Analysis

> How to capture and use network data (cookies, tokens, headers) for crawling.

---

## Cookie Extraction

### From Browser DevTools

```
1. Open target site in Chrome
2. Open DevTools (F12) > Application tab > Cookies
3. Copy relevant cookies (session, auth tokens)
4. Note expiry times
```

### From Playwright

```typescript
// After login or navigation
const cookies = await context.cookies();

// Filter relevant cookies
const authCookies = cookies.filter((c) =>
  ['session', 'token', 'auth', 'sid'].some((name) =>
    c.name.toLowerCase().includes(name)
  )
);

// Format as cookie header
const cookieHeader = authCookies.map((c) => `${c.name}=${c.value}`).join('; ');
console.log('Cookie:', cookieHeader);

// Save for later use
const fs = await import('fs');
fs.writeFileSync('cookies.json', JSON.stringify(authCookies, null, 2));
```

### Cookie Refresh Pattern

```typescript
async function ensureFreshCookies(
  context: BrowserContext,
  page: Page
): Promise<string> {
  const cookies = await context.cookies();
  const sessionCookie = cookies.find((c) => c.name === 'session');

  if (!sessionCookie || isExpired(sessionCookie)) {
    // Re-login or refresh
    await page.goto('https://example.com/login');
    await login(page);
    const newCookies = await context.cookies();
    return newCookies.map((c) => `${c.name}=${c.value}`).join('; ');
  }

  return cookies.map((c) => `${c.name}=${c.value}`).join('; ');
}

function isExpired(cookie: { expires: number }): boolean {
  return cookie.expires > 0 && cookie.expires * 1000 < Date.now();
}
```

---

## Token Extraction

### Bearer Token from Network Tab

```typescript
// Intercept API calls to find bearer token
let authToken: string | null = null;

page.on('request', (request) => {
  const authHeader = request.headers()['authorization'];
  if (authHeader?.startsWith('Bearer ')) {
    authToken = authHeader.replace('Bearer ', '');
    console.log('Found token:', authToken.substring(0, 20) + '...');
  }
});

// Navigate to trigger API calls
await page.goto('https://example.com/dashboard');
await page.waitForTimeout(3000);

console.log('Auth token:', authToken);
```

### Token from localStorage / sessionStorage

```typescript
// Extract tokens stored in browser storage
const tokens = await page.evaluate(() => {
  const result: Record<string, string | null> = {};

  // Check localStorage
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i);
    if (
      key &&
      (key.includes('token') || key.includes('auth') || key.includes('jwt'))
    ) {
      result[`localStorage.${key}`] = localStorage.getItem(key);
    }
  }

  // Check sessionStorage
  for (let i = 0; i < sessionStorage.length; i++) {
    const key = sessionStorage.key(i);
    if (
      key &&
      (key.includes('token') || key.includes('auth') || key.includes('jwt'))
    ) {
      result[`sessionStorage.${key}`] = sessionStorage.getItem(key);
    }
  }

  return result;
});

console.log('Found tokens:', tokens);
```

### Token Refresh

```typescript
interface TokenPair {
  accessToken: string;
  refreshToken: string;
  expiresAt: number;
}

async function refreshAccessToken(refreshToken: string): Promise<TokenPair> {
  const response = await fetch('https://example.com/api/auth/refresh', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refreshToken }),
  });

  if (!response.ok) throw new Error('Token refresh failed');
  return response.json();
}

async function fetchWithAutoRefresh(
  url: string,
  tokens: TokenPair
): Promise<unknown> {
  if (Date.now() >= tokens.expiresAt - 60000) {
    // Refresh 1 min before expiry
    const newTokens = await refreshAccessToken(tokens.refreshToken);
    Object.assign(tokens, newTokens);
  }

  const response = await fetch(url, {
    headers: { Authorization: `Bearer ${tokens.accessToken}` },
  });

  return response.json();
}
```

---

## Header Capture

### Capture All Request Headers

```typescript
// Capture headers from a real browser request
const headers = await new Promise<Record<string, string>>((resolve) => {
  page.on('request', (request) => {
    if (request.url().includes('/api/items')) {
      resolve(request.headers());
    }
  });

  page.goto('https://example.com/items');
});

console.log('Captured headers:', JSON.stringify(headers, null, 2));
```

### Essential Headers for API Crawling

```typescript
function buildHeaders(options: {
  cookie?: string;
  token?: string;
  referer?: string;
}): Record<string, string> {
  const headers: Record<string, string> = {
    Accept: 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'User-Agent':
      'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'sec-ch-ua':
      '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
  };

  if (options.cookie) headers['Cookie'] = options.cookie;
  if (options.token) headers['Authorization'] = `Bearer ${options.token}`;
  if (options.referer) headers['Referer'] = options.referer;

  return headers;
}
```

---

## Bot Detection Analysis

### Detect Protection Type

```typescript
async function detectProtection(
  page: Page,
  url: string
): Promise<{
  type: string;
  details: string;
}> {
  const response = await page.goto(url);
  const status = response?.status() || 0;
  const headers = response?.headers() || {};
  const body = await page.content();

  // Cloudflare
  if (
    headers['cf-ray'] ||
    body.includes('cf-browser-verification') ||
    body.includes('challenge-platform')
  ) {
    return { type: 'cloudflare', details: 'Cloudflare protection detected' };
  }

  // DataDome
  if (headers['x-datadome'] || body.includes('datadome')) {
    return { type: 'datadome', details: 'DataDome protection detected' };
  }

  // PerimeterX
  if (body.includes('_pxhd') || body.includes('perimeterx')) {
    return { type: 'perimeterx', details: 'PerimeterX protection detected' };
  }

  // Generic WAF
  if (status === 403 || status === 503) {
    return { type: 'waf', details: `Blocked with status ${status}` };
  }

  // reCAPTCHA
  if (body.includes('recaptcha') || body.includes('grecaptcha')) {
    return { type: 'recaptcha', details: 'reCAPTCHA detected' };
  }

  return { type: 'none', details: 'No bot protection detected' };
}
```

### Response Analysis

```typescript
// Check if response is a bot challenge vs real content
function isRealContent(html: string, expectedSelector: string): boolean {
  // Simple heuristic checks
  const suspicious = [
    'Please verify you are a human',
    'Access denied',
    'Please enable JavaScript',
    'Checking your browser',
    'cf-browser-verification',
    'challenge-platform',
  ];

  const isSuspicious = suspicious.some((s) =>
    html.toLowerCase().includes(s.toLowerCase())
  );

  const hasExpectedContent = html.includes(expectedSelector.replace('.', ''));

  return !isSuspicious && hasExpectedContent;
}
```

---

## NETWORK.md Template

After analysis, generate this document:

```markdown
# [Site Name] Network

## Authentication Data

| Field | Value | Expires |
|------|------|------|
| Cookie | session=abc123 | 24h |
| Bearer Token | eyJ... | 1h |
| API Key | sk-... | N/A |

## Required Headers

```
Accept: application/json
Accept-Language: en-US,en;q=0.9
User-Agent: Mozilla/5.0 ...
Referer: https://example.com/
sec-ch-ua: "Chromium";v="120"
```

## Rate Limits

| Metric | Value |
|------|------|
| Requests/minute | 60 |
| Requests/hour | 1000 |
| Recommended delay | 1000ms |
| Burst limit | 10 |

## Bot Detection

| Check | Result |
|------|------|
| Cloudflare | No |
| DataDome | No |
| reCAPTCHA | No |
| Custom WAF | No |

## Notes

[Any special considerations, gotchas, or workarounds]
```
