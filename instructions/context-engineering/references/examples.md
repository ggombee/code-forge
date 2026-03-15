# Examples - 실전 패턴

## Agentic Coding

```xml
<coding_guidelines>

<investigation>
ALWAYS read files before proposing edits.
Use Explore agent for codebase discovery.
Do not speculate about code structure.
</investigation>

<implementation>
Avoid over-engineering.
Only make directly requested changes.
Don't add features unless asked.
Keep solutions simple and focused.
</implementation>

<testing>
Run tests after changes.
Verify no regressions.
Add new tests for new features.
</testing>

</coding_guidelines>
```

## Frontend Design

```xml
<frontend_aesthetics>

Avoid generic "AI slop" aesthetic.
Make creative, distinctive frontends that stand out.

<focus>

**Typography**
- Unique font combinations
- Avoid overused fonts (Inter, Roboto)
- Consider: Geist, Cal Sans, Untitled Sans

**Color**
- Cohesive theme with sharp accents
- Use color psychology
- Dark mode by default

**Motion**
- High-impact animations (Framer Motion, GSAP)
- Smooth transitions
- Micro-interactions

**Backgrounds**
- Depth and atmosphere
- Gradients, meshes, noise
- Avoid flat single colors

</focus>

<frameworks>
- TailwindCSS for utility-first
- shadcn/ui for components
- Framer Motion for animations
</frameworks>

</frontend_aesthetics>
```

## API Design

```xml
<api_guidelines>

<rest_patterns>

**Naming**
- Resource-oriented: `/users/:id/posts`
- Kebab-case: `/user-profiles`
- Versioning: `/api/v1/...`

**Methods**
- GET: Read (safe, idempotent)
- POST: Create
- PUT: Full update (idempotent)
- PATCH: Partial update
- DELETE: Remove (idempotent)

**Responses**
200 OK | 201 Created | 400 Bad Request | 401 Unauthorized | 404 Not Found | 500 Internal Error

</rest_patterns>

<validation>
- Validate at boundary (input validators)
- Use Zod/Yup schemas
- Return detailed error messages
- Never trust client input
</validation>

</api_guidelines>
```

## Error Handling

```xml
<error_patterns>

Client-Side (React):
try {
  const data = await api.fetch()
  return data
} catch (error) {
  if (error.status === 401) redirect('/login')
  toast.error(error.message)
  throw error
}

Server-Side (API):
try {
  const result = await db.query()
  return result
} catch (error) {
  logger.error(error)
  if (error instanceof ValidationError) throw new HttpError(400, error.message)
  throw new HttpError(500, 'Internal error')
}

User-Facing: Technical → Human-readable message

</error_patterns>
```

## Testing Patterns

```xml
<test_guidelines>

Unit: describe('fn', () => { it('does X', () => expect(fn(input)).toBe(output)) })
Integration: describe('POST /api/users', () => { it('creates user', async () => { ... }) })
Component: test('renders', () => { render(<C />); expect(screen.getByText('X')).toBeInTheDocument() })

</test_guidelines>
```

## Git Commit Messages

```xml
<commit_style>

Format: <type>: <subject>
Types: feat | fix | refactor | style | docs | test | chore
Rules: 50 chars max subject, imperative mood, no period, one logical change

</commit_style>
```

## Security Patterns

```xml
<security>

Input: Sanitize all input, parameterized queries, validate uploads, escape HTML
Auth: Hash passwords (bcrypt/argon2), secure sessions, rate limiting, CSRF
API: Keys in env vars, HTTPS only, CORS config, input size limits
Never: Plain text passwords, trust client validation, expose data in errors

</security>
```

## Performance

```xml
<performance>

React: useMemo (expensive calc), useCallback (handlers), React.memo (children)
Splitting: lazy(() => import('./Heavy')) + Suspense
API: Pagination, Redis caching, JOIN/DataLoader for N+1, gzip/brotli

</performance>
```

---

모든 예시는 **복사 가능**하도록 작성.
패턴을 그대로 적용하고, 프로젝트에 맞게 조정.
