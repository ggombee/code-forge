# Selector Strategies

> How to find, write, and maintain reliable selectors for crawling.

---

## Selector Priority

Use the most resilient selector available. Higher priority = more stable across site updates.

| Priority | Type | Example | Stability |
|------|------|------|------|
| 1 | ARIA role + name | `getByRole('button', { name: 'Submit' })` | Highest |
| 2 | data-testid | `[data-testid="login-btn"]` | High |
| 3 | Semantic HTML | `article`, `nav`, `main` | High |
| 4 | ARIA attributes | `[aria-label="Close"]` | Medium-High |
| 5 | Stable class names | `.product-card` (BEM/utility) | Medium |
| 6 | ID | `#main-content` | Medium |
| 7 | Text content | `text=Sign In` | Medium |
| 8 | Structural CSS | `div > ul > li:nth-child(2)` | Low |
| 9 | XPath | `//div[@class="item"]/a` | Lowest |

---

## Extraction Patterns

### Text Content

```typescript
// Single element
const title = await page.locator('h1').textContent();

// Multiple elements
const titles = await page.$$eval('h2.title', (els) =>
  els.map((el) => el.textContent?.trim() || '')
);

// Inner text (visible text only)
const visibleText = await page.locator('.content').innerText();
```

### Attributes

```typescript
// href
const links = await page.$$eval('a.item-link', (els) =>
  els.map((el) => (el as HTMLAnchorElement).href)
);

// data attributes
const ids = await page.$$eval('[data-item-id]', (els) =>
  els.map((el) => (el as HTMLElement).dataset.itemId || '')
);

// src
const images = await page.$$eval('img.product-image', (els) =>
  els.map((el) => (el as HTMLImageElement).src)
);
```

### Structured Data

```typescript
// Extract full card data
const items = await page.$$eval('.product-card', (cards) =>
  cards.map((card) => ({
    title: card.querySelector('.title')?.textContent?.trim() || '',
    price: card.querySelector('.price')?.textContent?.trim() || '',
    url: (card.querySelector('a') as HTMLAnchorElement)?.href || '',
    image: (card.querySelector('img') as HTMLImageElement)?.src || '',
    rating: card.querySelector('.rating')?.getAttribute('data-score') || '',
  }))
);
```

### Nested / Complex Structures

```typescript
// Table data
const tableData = await page.$$eval('table tbody tr', (rows) =>
  rows.map((row) => {
    const cells = row.querySelectorAll('td');
    return {
      name: cells[0]?.textContent?.trim() || '',
      value: cells[1]?.textContent?.trim() || '',
      status: cells[2]?.textContent?.trim() || '',
    };
  })
);

// Nested lists
const categories = await page.$$eval('.category', (cats) =>
  cats.map((cat) => ({
    name: cat.querySelector('h3')?.textContent?.trim() || '',
    items: Array.from(cat.querySelectorAll('.sub-item')).map(
      (item) => item.textContent?.trim() || ''
    ),
  }))
);
```

---

## Locator Patterns (Playwright)

### Role-Based (Preferred)

```typescript
// Button by accessible name
page.getByRole('button', { name: 'Submit' });
page.getByRole('link', { name: 'Next page' });
page.getByRole('heading', { name: 'Products', level: 2 });
page.getByRole('tab', { name: 'Reviews' });
page.getByRole('checkbox', { name: 'Accept terms' });
```

### Text-Based

```typescript
// Exact text
page.getByText('Sign In', { exact: true });

// Partial text
page.getByText('Sign');

// Regex
page.getByText(/sign\s*in/i);
```

### Label / Placeholder

```typescript
page.getByLabel('Email address');
page.getByPlaceholder('Search...');
page.getByAltText('Product image');
page.getByTitle('Close dialog');
```

### CSS Selectors

```typescript
// Class
page.locator('.product-card');

// Attribute
page.locator('[data-testid="product-list"]');
page.locator('[aria-label="Search"]');

// Combinators
page.locator('.card >> h2'); // descendant within shadow DOM boundaries
page.locator('.card > .title'); // direct child
page.locator('.card + .card'); // adjacent sibling
```

### Filtering

```typescript
// Has text
page.locator('.card').filter({ hasText: 'Featured' });

// Has child element
page.locator('.card').filter({ has: page.locator('.badge-new') });

// Not
page.locator('.card').filter({ hasNot: page.locator('.sold-out') });

// Chaining
page.locator('.product-list').locator('.card').filter({ hasText: 'Sale' }).first();
```

---

## Crawling-Specific Patterns

### Container + Child Pattern

Most reliable for list crawling:

```typescript
// 1. Find the container
const container = page.locator('[data-testid="product-grid"]');
// Fallback: page.locator('.product-list')

// 2. Find items within container
const items = container.locator('.product-card');
const count = await items.count();

// 3. Extract from each item
for (let i = 0; i < count; i++) {
  const item = items.nth(i);
  const title = await item.locator('h2').textContent();
  const price = await item.locator('.price').textContent();
}
```

### Pagination Selector

```typescript
// Next button
const nextBtn = page.locator('button[aria-label="Next page"]');
// Fallback: page.locator('.pagination .next')
// Fallback: page.getByRole('button', { name: /next/i })

// Check if there's a next page
const hasNext = await nextBtn.isEnabled().catch(() => false);
```

### Dynamic Content Detection

```typescript
// Wait for content to load
await page.waitForSelector('.product-card', { state: 'visible' });

// Wait for loading indicator to disappear
await page.waitForSelector('.spinner', { state: 'hidden' });

// Wait for specific count
await page.waitForFunction(
  (min) => document.querySelectorAll('.product-card').length >= min,
  10
);
```

---

## Waiting Strategies

| Scenario | Method | Example |
|------|------|------|
| Element appears | `waitForSelector` | `await page.waitForSelector('.item')` |
| Element disappears | `waitForSelector hidden` | `await page.waitForSelector('.loader', { state: 'hidden' })` |
| Network settles | `waitForLoadState` | `await page.waitForLoadState('networkidle')` |
| API response | `waitForResponse` | `await page.waitForResponse('**/api/items')` |
| Custom condition | `waitForFunction` | `await page.waitForFunction(() => ...)` |
| URL change | `waitForURL` | `await page.waitForURL('**/page/2')` |

---

## Troubleshooting Selectors

### Selector Not Finding Elements

```typescript
// Debug: check what's on the page
const html = await page.content();
console.log(html.substring(0, 5000));

// Debug: screenshot
await page.screenshot({ path: 'debug.png', fullPage: true });

// Debug: list all matching elements
const count = await page.locator('.item').count();
console.log(`Found ${count} items`);

// Debug: check if element is in iframe
const frames = page.frames();
for (const frame of frames) {
  const count = await frame.locator('.item').count();
  console.log(`Frame ${frame.url()}: ${count} items`);
}
```

### Elements in Shadow DOM

```typescript
// Playwright pierces shadow DOM by default with >>
page.locator('my-component >> .inner-element');

// Or use shadow DOM specific approach
const shadow = await page.evaluateHandle(() =>
  document.querySelector('my-component')?.shadowRoot
);
```

### Elements in iframes

```typescript
// Get frame by name/URL
const frame = page.frame({ name: 'content-frame' });
// or
const frame = page.frame({ url: /embed/ });

// Use frameLocator
const items = page.frameLocator('#content-frame').locator('.item');
```
