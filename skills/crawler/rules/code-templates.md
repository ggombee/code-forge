# Crawler Code Templates

> Templates for generating crawler implementations from analysis results.

---

## Method Selection

| Condition | Method | Template |
|------|------|------|
| API discovered + simple auth | `fetch` | API crawler |
| API + cookie/token auth | `fetch + Cookie` | API crawler (authenticated) |
| Strong anti-bot protection | Nstbrowser | Custom implementation |
| No API (SSR pages) | Playwright | DOM crawler |

---

## API Crawler Template

```typescript
// CRAWLER.ts - API-based
interface ApiResponse {
  data: Item[];
  pagination: { page: number; total: number; hasNext: boolean };
}

interface Item {
  id: string;
  title: string;
}

export class ApiCrawler {
  private baseUrl = 'https://example.com/api';
  private headers: Record<string, string> = {
    'Content-Type': 'application/json',
    // 'Authorization': 'Bearer ...',
    // 'Cookie': '...'
  };

  async fetchPage(page: number, limit = 20): Promise<ApiResponse> {
    const res = await fetch(`${this.baseUrl}/items?page=${page}&limit=${limit}`, {
      headers: this.headers,
    });
    if (!res.ok) throw new Error(`API error: ${res.status}`);
    return res.json();
  }

  async crawlAll(): Promise<Item[]> {
    const items: Item[] = [];
    let page = 1;
    let hasNext = true;

    while (hasNext) {
      const res = await this.fetchPage(page);
      items.push(...res.data);
      hasNext = res.pagination.hasNext;
      page++;
      await new Promise((r) => setTimeout(r, 100)); // rate limit guard
    }

    return items;
  }
}
```

---

## DOM Crawler Template (Playwright)

```typescript
// CRAWLER.ts - DOM-based
import { chromium, Browser, Page } from 'playwright';

interface Item {
  id: string;
  title: string;
  url: string;
}

export class DomCrawler {
  private browser: Browser | null = null;
  private page: Page | null = null;

  async init() {
    this.browser = await chromium.launch({ headless: true });
    this.page = await this.browser.newPage();
  }

  async crawlList(url: string): Promise<Item[]> {
    if (!this.page) throw new Error('Crawler not initialized');

    await this.page.goto(url, { waitUntil: 'domcontentloaded' });
    await this.page.waitForSelector('.item-card');

    return this.page.$$eval('.item-card', (cards) =>
      cards.map((card) => {
        const a = card.querySelector('a');
        const h2 = card.querySelector('h2');
        return {
          id: (card as HTMLElement).dataset.id || '',
          title: h2?.textContent?.trim() || '',
          url: (a as HTMLAnchorElement)?.href || '',
        };
      })
    );
  }

  async close() {
    await this.browser?.close();
  }
}
```
