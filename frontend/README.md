# Frontend

React 18 + TypeScript + Vite + Tailwind CSS.

## Setup

```bash
npm install
npm run dev       # Dev server at http://localhost:5173
npm run build     # Production build
npm run lint      # ESLint
```

Expects backend running at http://localhost:8000.

## Structure

```
src/
  components/   SearchInput, SearchResults, SearchSuggestions, SearchFilters
  hooks/        useSearch (main search state/logic)
  services/     API client (native fetch, no axios)
  App.tsx       Root component
```
