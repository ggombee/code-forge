# Playwright Commands

> Quick reference for Playwright browser automation commands.

---

## Session Management

### Browser Launch

```typescript
import { chromium, firefox, webkit } from 'playwright';

// Basic launch
const browser = await chromium.launch({ headless: true });

// With options
const browser = await chromium.launch({
  headless: false,
  slowMo: 100, // slow down by 100ms per operation
  args: ['--disable-blink-features=AutomationControlled'],
});

// New context (isolated session)
const context = await browser.newContext({
  userAgent: 'Mozilla/5.0 ...',
  viewport: { width: 1920, height: 1080 },
  locale: 'en-US',
  timezoneId: 'America/New_York',
});

const page = await context.newPage();
```

### Context with Cookies

```typescript
// Set cookies before navigation
await context.addCookies([
  {
    name: 'session',
    value: 'abc123',
    domain: '.example.com',
    path: '/',
  },
]);

// Get cookies after navigation
const cookies = await context.cookies();
```

### State Persistence

```typescript
// Save state (cookies + localStorage)
await context.storageState({ path: 'state.json' });

// Restore state
const context = await browser.newContext({
  storageState: 'state.json',
});
```

---

## Page Execution

### Navigation

```typescript
// Go to URL
await page.goto('https://example.com');
await page.goto('https://example.com', {
  waitUntil: 'domcontentloaded', // or 'load', 'networkidle'
  timeout: 30000,
});

// Wait for navigation after action
await Promise.all([
  page.waitForNavigation(),
  page.click('a.next-page'),
]);

// Reload
await page.reload();

// Go back / forward
await page.goBack();
await page.goForward();
```

### JavaScript Evaluation

```typescript
// Evaluate in page context
const title = await page.evaluate(() => document.title);

// With arguments
const text = await page.evaluate(
  (selector) => document.querySelector(selector)?.textContent,
  '.my-class'
);

// Return complex data
const data = await page.evaluate(() => {
  return Array.from(document.querySelectorAll('.item')).map((el) => ({
    title: el.querySelector('h2')?.textContent?.trim(),
    url: (el.querySelector('a') as HTMLAnchorElement)?.href,
  }));
});
```

---

## Page Content

### Screenshots

```typescript
// Full page
await page.screenshot({ path: 'page.png', fullPage: true });

// Element only
await page.locator('.chart').screenshot({ path: 'chart.png' });

// Buffer (no file)
const buffer = await page.screenshot();
```

### PDF

```typescript
await page.pdf({
  path: 'page.pdf',
  format: 'A4',
  printBackground: true,
});
```

### HTML Content

```typescript
// Full page HTML
const html = await page.content();

// Inner HTML of element
const inner = await page.locator('.container').innerHTML();

// Text content
const text = await page.locator('.title').textContent();
```

---

## DOM Structure

### Query Elements

```typescript
// Single element
const el = page.locator('.my-class');
const el = page.locator('css=.my-class');
const el = page.locator('xpath=//div[@class="my-class"]');

// Multiple elements
const items = page.locator('.item');
const count = await items.count();

// Nth element
const third = page.locator('.item').nth(2);
const first = page.locator('.item').first();
const last = page.locator('.item').last();
```

### Element Properties

```typescript
// Text
const text = await el.textContent();
const innerText = await el.innerText();

// Attribute
const href = await el.getAttribute('href');
const dataId = await el.getAttribute('data-id');

// Visibility
const visible = await el.isVisible();
const hidden = await el.isHidden();

// State
const enabled = await el.isEnabled();
const checked = await el.isChecked();
```

### $$eval Pattern

```typescript
// Evaluate on all matching elements
const data = await page.$$eval('.item-card', (cards) =>
  cards.map((card) => ({
    title: card.querySelector('h2')?.textContent?.trim() || '',
    price: card.querySelector('.price')?.textContent?.trim() || '',
  }))
);
```

---

## Interaction

### Click

```typescript
await page.click('button.submit');
await page.click('text=Sign In');
await page.click('a >> text=Next');

// With options
await page.click('button', {
  button: 'right', // or 'middle'
  clickCount: 2, // double click
  delay: 100, // ms between mousedown and mouseup
  position: { x: 10, y: 20 }, // relative to element
});
```

### Input

```typescript
// Type text
await page.fill('input[name="email"]', 'user@example.com');

// Type with delay (simulates real typing)
await page.type('input[name="search"]', 'query', { delay: 100 });

// Clear and type
await page.locator('input').clear();
await page.locator('input').fill('new value');

// Press key
await page.press('input', 'Enter');
await page.keyboard.press('Escape');
```

### Select / Checkbox

```typescript
// Select dropdown
await page.selectOption('select#country', 'US');
await page.selectOption('select', { label: 'United States' });

// Checkbox
await page.check('input[type="checkbox"]');
await page.uncheck('input[type="checkbox"]');
```

### Scroll

```typescript
// Scroll to element
await page.locator('.target').scrollIntoViewIfNeeded();

// Scroll page
await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));

// Scroll by amount
await page.evaluate(() => window.scrollBy(0, 500));
```

---

## Selector Strategies

### Priority Order

| Priority | Selector Type | Example |
|------|------|------|
| 1 | Role + Name | `getByRole('button', { name: 'Submit' })` |
| 2 | Test ID | `getByTestId('login-btn')` |
| 3 | Text | `getByText('Sign In')` |
| 4 | Label | `getByLabel('Email')` |
| 5 | Placeholder | `getByPlaceholder('Search...')` |
| 6 | CSS | `locator('.btn-primary')` |
| 7 | XPath | `locator('xpath=//button')` |

### Chaining

```typescript
// Parent > Child
page.locator('.card').locator('h2');

// Filter
page.locator('.card').filter({ hasText: 'Featured' });
page.locator('.card').filter({ has: page.locator('.badge') });

// Nth match
page.locator('.card').nth(0);
```

---

## Network

### Intercept Requests

```typescript
// Block images/css for faster crawling
await page.route('**/*.{png,jpg,jpeg,gif,css,woff2}', (route) => route.abort());

// Modify request
await page.route('**/api/**', (route) => {
  route.continue({
    headers: { ...route.request().headers(), 'X-Custom': 'value' },
  });
});

// Mock response
await page.route('**/api/data', (route) => {
  route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ data: [] }),
  });
});
```

### Wait for Response

```typescript
// Wait for specific API call
const response = await page.waitForResponse('**/api/items');
const data = await response.json();

// Wait with predicate
const response = await page.waitForResponse(
  (resp) => resp.url().includes('/api/items') && resp.status() === 200
);
```

### Listen to All Requests

```typescript
// Log all API calls
page.on('request', (req) => {
  if (req.url().includes('/api/')) {
    console.log('API:', req.method(), req.url());
  }
});

page.on('response', async (resp) => {
  if (resp.url().includes('/api/') && resp.status() === 200) {
    const data = await resp.json();
    console.log('Response:', data);
  }
});
```

---

## Waiting Strategies

```typescript
// Wait for selector
await page.waitForSelector('.loaded', { state: 'visible', timeout: 10000 });

// Wait for load state
await page.waitForLoadState('networkidle');
await page.waitForLoadState('domcontentloaded');

// Wait for function
await page.waitForFunction(() => document.querySelectorAll('.item').length > 10);

// Wait for timeout
await page.waitForTimeout(2000); // use sparingly

// Wait for URL change
await page.waitForURL('**/dashboard/**');
```
