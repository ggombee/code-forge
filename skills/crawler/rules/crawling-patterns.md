# Crawling Patterns

> Common patterns for different crawling scenarios.

---

## Rendering Patterns

### SSR (Server-Side Rendered)

Data is in the initial HTML response. Simplest to crawl.

```typescript
// Direct fetch + parse
const response = await fetch(url);
const html = await response.text();

// Parse with cheerio or similar
import * as cheerio from 'cheerio';
const $ = cheerio.load(html);
const items = $('.item-card')
  .map((_, el) => ({
    title: $(el).find('h2').text().trim(),
    url: $(el).find('a').attr('href'),
  }))
  .get();
```

### CSR (Client-Side Rendered)

Data loaded via JavaScript. Need browser or API interception.

```typescript
// Option 1: Intercept API calls
const items: Item[] = [];

page.on('response', async (response) => {
  if (response.url().includes('/api/items') && response.status() === 200) {
    const data = await response.json();
    items.push(...data.items);
  }
});

await page.goto(url);
await page.waitForSelector('.item-card'); // wait for render

// Option 2: Parse rendered DOM
const renderedItems = await page.$$eval('.item-card', (cards) =>
  cards.map((card) => ({
    title: card.querySelector('h2')?.textContent?.trim() || '',
    url: (card.querySelector('a') as HTMLAnchorElement)?.href || '',
  }))
);
```

### Hybrid

Some data in HTML, more loaded via JS.

```typescript
// Get initial data from HTML
await page.goto(url, { waitUntil: 'domcontentloaded' });
const initialData = await page.$$eval('.item', extractItems);

// Wait for dynamic content
await page.waitForSelector('.dynamic-section');
const dynamicData = await page.$$eval('.dynamic-item', extractItems);

const allData = [...initialData, ...dynamicData];
```

---

## Pagination Patterns

### Page Number Pagination

```typescript
async function crawlPaginated(baseUrl: string): Promise<Item[]> {
  const allItems: Item[] = [];
  let page = 1;
  let hasMore = true;

  while (hasMore) {
    const url = `${baseUrl}?page=${page}`;
    const items = await crawlPage(url);

    if (items.length === 0) {
      hasMore = false;
    } else {
      allItems.push(...items);
      page++;
      await humanDelay();
    }
  }

  return allItems;
}
```

### Cursor-Based Pagination

```typescript
async function crawlCursorPaginated(baseUrl: string): Promise<Item[]> {
  const allItems: Item[] = [];
  let cursor: string | null = null;

  do {
    const url = cursor ? `${baseUrl}?cursor=${cursor}` : baseUrl;
    const response = await fetch(url);
    const data = await response.json();

    allItems.push(...data.items);
    cursor = data.nextCursor || null;
    await humanDelay();
  } while (cursor);

  return allItems;
}
```

### Infinite Scroll

```typescript
async function crawlInfiniteScroll(page: Page): Promise<Item[]> {
  const seen = new Set<string>();
  let previousCount = 0;
  let noChangeCount = 0;
  const MAX_NO_CHANGE = 3;

  while (noChangeCount < MAX_NO_CHANGE) {
    // Scroll to bottom
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(2000);

    // Count items
    const items = await page.$$eval('.item', (els) =>
      els.map((el) => ({
        id: (el as HTMLElement).dataset.id || '',
        title: el.querySelector('h2')?.textContent?.trim() || '',
      }))
    );

    items.forEach((item) => seen.set(item.id));

    if (seen.size === previousCount) {
      noChangeCount++;
    } else {
      noChangeCount = 0;
      previousCount = seen.size;
    }

    // Check for "Load more" button
    const loadMore = await page.$('button:has-text("Load more")');
    if (loadMore) {
      await loadMore.click();
      await page.waitForTimeout(2000);
    }
  }

  return Array.from(seen).map((id) => ({ id })) as Item[];
}
```

### "Load More" Button

```typescript
async function crawlLoadMore(page: Page): Promise<Item[]> {
  await page.goto(url);

  while (true) {
    const loadMoreBtn = await page.$('button.load-more:not([disabled])');
    if (!loadMoreBtn) break;

    await loadMoreBtn.click();
    await page.waitForResponse((resp) =>
      resp.url().includes('/api/items') && resp.status() === 200
    );
    await humanDelay(500, 1500);
  }

  return page.$$eval('.item', extractItems);
}
```

---

## Authentication Patterns

### Cookie-Based Auth

```typescript
// Extract cookies from browser manually, then use:
const context = await browser.newContext({
  extraHTTPHeaders: {
    Cookie: 'session=abc123; token=xyz789',
  },
});

// Or set cookies directly
await context.addCookies([
  {
    name: 'session',
    value: 'abc123',
    domain: '.example.com',
    path: '/',
  },
]);
```

### Login Flow

```typescript
async function login(page: Page, email: string, password: string): Promise<void> {
  await page.goto('https://example.com/login');
  await page.fill('input[name="email"]', email);
  await page.fill('input[name="password"]', password);
  await page.click('button[type="submit"]');
  await page.waitForURL('**/dashboard**');

  // Save session for reuse
  const context = page.context();
  await context.storageState({ path: 'auth-state.json' });
}

// Reuse session
const context = await browser.newContext({
  storageState: 'auth-state.json',
});
```

### Token-Based Auth (API)

```typescript
async function fetchWithAuth(url: string, token: string): Promise<unknown> {
  const response = await fetch(url, {
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });

  if (response.status === 401) {
    // Token expired — refresh
    const newToken = await refreshToken();
    return fetchWithAuth(url, newToken);
  }

  return response.json();
}
```

---

## Dynamic Content Patterns

### Tab/Filter Switching

```typescript
async function crawlAllTabs(page: Page): Promise<Record<string, Item[]>> {
  const results: Record<string, Item[]> = {};
  const tabs = await page.$$eval('.tab', (els) =>
    els.map((el) => ({
      name: el.textContent?.trim() || '',
      selector: `[data-tab="${(el as HTMLElement).dataset.tab}"]`,
    }))
  );

  for (const tab of tabs) {
    await page.click(tab.selector);
    await page.waitForSelector('.item-list:not(.loading)');
    await humanDelay();

    results[tab.name] = await page.$$eval('.item', extractItems);
  }

  return results;
}
```

### Modal/Popup Content

```typescript
async function crawlWithDetails(page: Page): Promise<Item[]> {
  const items = await page.$$eval('.item-card', extractBasicItems);
  const detailed: Item[] = [];

  for (const item of items) {
    // Click to open detail modal
    await page.click(`[data-id="${item.id}"]`);
    await page.waitForSelector('.modal.visible');

    const details = await page.$eval('.modal', (modal) => ({
      description: modal.querySelector('.description')?.textContent?.trim(),
      metadata: modal.querySelector('.metadata')?.textContent?.trim(),
    }));

    detailed.push({ ...item, ...details });

    // Close modal
    await page.click('.modal .close-btn');
    await page.waitForSelector('.modal', { state: 'hidden' });
    await humanDelay(500, 1000);
  }

  return detailed;
}
```

---

## Reliability Patterns

### Retry with Backoff

```typescript
async function withRetry<T>(
  fn: () => Promise<T>,
  maxRetries = 3,
  baseDelay = 1000
): Promise<T> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      if (attempt === maxRetries) throw error;

      const delay = baseDelay * Math.pow(2, attempt) + Math.random() * 1000;
      console.warn(`Attempt ${attempt + 1} failed, retrying in ${Math.round(delay)}ms`);
      await new Promise((r) => setTimeout(r, delay));
    }
  }

  throw new Error('Unreachable');
}
```

### Progress Tracking

```typescript
class CrawlProgress {
  private total = 0;
  private completed = 0;
  private failed = 0;
  private startTime = Date.now();

  setTotal(n: number): void {
    this.total = n;
  }

  success(): void {
    this.completed++;
    this.log();
  }

  failure(url: string, error: Error): void {
    this.failed++;
    console.error(`Failed: ${url} - ${error.message}`);
    this.log();
  }

  private log(): void {
    const elapsed = ((Date.now() - this.startTime) / 1000).toFixed(1);
    const pct = this.total ? ((this.completed / this.total) * 100).toFixed(1) : '?';
    console.log(
      `Progress: ${this.completed}/${this.total} (${pct}%) | Failed: ${this.failed} | ${elapsed}s`
    );
  }
}
```

### Checkpoint / Resume

```typescript
import { readFileSync, writeFileSync, existsSync } from 'fs';

interface Checkpoint {
  completedUrls: string[];
  lastPage: number;
  data: Item[];
}

function saveCheckpoint(checkpoint: Checkpoint, path = 'checkpoint.json'): void {
  writeFileSync(path, JSON.stringify(checkpoint, null, 2));
}

function loadCheckpoint(path = 'checkpoint.json'): Checkpoint | null {
  if (!existsSync(path)) return null;
  return JSON.parse(readFileSync(path, 'utf-8'));
}

async function crawlWithCheckpoint(): Promise<Item[]> {
  const checkpoint = loadCheckpoint() || {
    completedUrls: [],
    lastPage: 0,
    data: [],
  };

  const completed = new Set(checkpoint.completedUrls);

  for (let page = checkpoint.lastPage + 1; page <= totalPages; page++) {
    const url = `${baseUrl}?page=${page}`;
    if (completed.has(url)) continue;

    const items = await crawlPage(url);
    checkpoint.data.push(...items);
    checkpoint.completedUrls.push(url);
    checkpoint.lastPage = page;

    saveCheckpoint(checkpoint);
  }

  return checkpoint.data;
}
```
