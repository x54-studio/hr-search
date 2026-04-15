# Stage 5: Frontend

**Owner**: B (Frontend Engineer)
**Depends on**: Stage 4 (API)
**Branch**: `refactor/05-frontend`

## Goal

Update API client, components, and hooks to use new `/api/items` endpoints. Title from `/api/config`. Replace `content_type` filter with `source_type`. Fix search UX: separate "typing" (autocomplete only) from "submitted" (search results). Minimal visual changes (decision B4).

## Changes

### `frontend/src/services/api.ts`

- Endpoint URLs: `/api/webinars` → `/api/items`
- Response parsing: `data.webinars` → `data.items`
- Add `fetchConfig()` function to call `GET /api/config`
- Parameter: `content_type` → `source_type`
- Type/interface: `Webinar` → `Item` (or similar)

### `frontend/src/hooks/useSearch.ts`

#### Search UX fix: separate typing from submission

Current bug: `Promise.all([search(), autocomplete()])` fires on every keystroke (100ms debounce).
This shows autocomplete dropdown AND search results simultaneously — competing for attention
and wasting backend resources (embedding generation on every keystroke).

**New behavior:**

```
handleQueryChange(query)
  → fires autocomplete ONLY (debounce 250ms)
  → showSuggestions = true
  → does NOT fire search

handleSubmit() — new, triggered by Enter key
  → fires search(query)
  → showSuggestions = false

handleSuggestionClick(suggestion)
  → sets query = suggestion
  → fires search(suggestion)
  → showSuggestions = false
```

**State changes:**

- New state: `hasSearched: boolean` — true after first explicit search, controls SearchResults visibility
- Remove: the `useEffect` that auto-triggers `search()` on query changes
- Add: new `useEffect` for autocomplete-only on query changes (250ms debounce)
- Keep: `useEffect` that triggers search on filter changes (but only if `hasSearched` is already true)

**New split:**

```typescript
// Autocomplete only — fires on keystroke (250ms debounce)
const fetchSuggestions = useCallback(async (q: string) => {
  if (q.trim().length === 0) { setSuggestions([]); return; }
  const response = await apiService.autocomplete(q);
  setSuggestions(response.suggestions);
}, []);

// Full search — fires on Enter / suggestion click / filter change
const executeSearch = useCallback(async (q: string) => {
  setShowSuggestions(false);
  setLoading(true);
  // ... existing search logic (semantic search + filter handling) ...
  setHasSearched(true);
}, [/* deps */]);
```

#### Rename changes (same as before)

- Type references: webinar → item
- State variables: if any named `webinars` → `items`
- Filter state: `contentType` → `sourceType`
- API call params: `content_type` → `source_type`
- `apiService.listWebinars()` → `apiService.listItems()`
- Response field: `response.webinars` → `response.items`
- Metadata types: `webinar_count` → `item_count` in categories, speakers, tags response interfaces
- `clearSearch()` must reset `hasSearched` to `false`

### `frontend/src/components/SearchResults.tsx`

- Props type: webinar → item
- Primary link: `source_url` (main clickable link, replaces `video_url`)
- Secondary link: `metadata.pdf_url` if present — render as small "PDF" link (decision P1)
- Duration display: keep, but only show when `duration_ms` is not null
- Date field: `recorded_date` → `published_date`

### `frontend/src/components/SearchFilters.tsx`

- Filter options: replace `content_type: webinar|pdf` with `source_type` dropdown
- **Hide filter when `config.source_types.length <= 1`** (decision P3)
  ```tsx
  {config.source_types.length > 1 && <SourceTypeFilter ... />}
  ```
- When visible: show whatever `source_types` the `/api/config` endpoint returns
- Minimal UI — simple select/dropdown, no icons (decision B4)

### `frontend/src/components/SearchInput.tsx`

- Placeholder text: hardcoded "Szukaj webinaru, tematu lub prelegenta..." → use generic text or fetch from config
- Suggestion type labels: `'title'` / `'speaker'` / `'tag'` (decision P2 — matches autocomplete response from Stage 4)
- **New prop: `onSubmit`** — called on Enter key press, triggers `executeSearch()`
- Enter behavior change:
  - If suggestion highlighted (arrow keys) → select suggestion (existing)
  - If no suggestion highlighted → submit current query as search (new)

### `frontend/src/App.tsx`

- Title: `"HR Knowledge Search"` → fetched from `/api/config` (decision B5)
- Fallback if config fetch fails: `"Knowledge Search"` (decision P4 from review)
- Footer text: `"HR Knowledge Search System"` → from config or generic
- Add `useEffect` to fetch config on mount, store in state
- **Conditional rendering for search UX fix:**
  ```tsx
  {/* Autocomplete dropdown — visible while typing */}
  <SearchSuggestions
    visible={showSuggestions && query.length > 0 && !loading}
    ...
  />

  {/* Results — visible only after explicit search */}
  {hasSearched && (
    <SearchResults ... />
  )}
  ```

### Type definitions

If there's a shared type file, update:
```typescript
// Before
interface Webinar {
  id: string;
  title: string;
  description: string;
  video_url: string | null;
  pdf_url: string | null;
  recorded_date: string;
  // ...
}

// After
interface Item {
  id: string;
  title: string;
  description: string;
  source_type: string;
  source_url: string | null;       // primary link (decision P1)
  published_date: string;
  metadata: Record<string, unknown>; // e.g. { pdf_url: "..." }
  duration_ms: number | null;
  // ...
}

interface AppConfig {
  title: string;
  source_types: string[];
}
```

## Acceptance criteria

### Rename
- [ ] `npm run build` — no TypeScript errors
- [ ] `npm run lint` — passes
- [ ] Dev server loads, title shows from config
- [ ] Results show `source_url` link instead of separate video/pdf links
- [ ] No references to "webinar" in `frontend/src/` (except possibly display labels for source_type='webinar')

### Search UX fix
- [ ] Typing "rek" → autocomplete dropdown appears, NO search results below
- [ ] Enter key → autocomplete hides, search results appear
- [ ] Click suggestion → autocomplete hides, search results appear for that suggestion
- [ ] Arrow keys + Enter → selects suggestion, triggers search
- [ ] Clearing input → hides both autocomplete and results
- [ ] Filter change after search → results update (re-filters)
- [ ] Filter change without prior search → fetches items via list endpoint

### Config
- [ ] `/api/config` failure → fallback title "Knowledge Search" shown
- [ ] Source type filter hidden when only 1 source_type in config
