# HR Search Frontend

React-based frontend for the HR Knowledge Search System.

## Tech Stack

- **React 18** - Modern React with hooks and concurrent features
- **TypeScript** - Type safety and better developer experience
- **Vite** - Fast build tool with hot module replacement
- **Tailwind CSS** - Utility-first CSS framework for rapid styling
- **Native fetch API** - No external HTTP client dependencies

## Project Structure

```
src/
├── components/           # React components
│   ├── SearchInput.tsx   # Main search input with autocomplete
│   ├── SearchResults.tsx # Search results display
│   └── SearchSuggestions.tsx # Autocomplete dropdown
├── hooks/               # Custom React hooks
│   └── useSearch.ts     # Search state management
├── services/            # API communication
│   └── api.ts          # HTTP client and types
├── App.tsx             # Main application component
└── main.tsx            # Application entry point
```

## Development

### Prerequisites

- Node.js 18+ 
- npm or yarn

### Setup

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Development Server

The frontend runs on `http://localhost:5173` by default and connects to the backend API at `http://localhost:8000`.

## Features

- **Semantic Search** - Search webinars using natural language
- **Autocomplete** - Real-time search suggestions
- **Spell Correction** - Automatic typo detection and correction
- **Mobile Responsive** - Works on all device sizes
- **Polish Language Support** - Optimized for Polish HR terminology

## API Integration

The frontend communicates with the FastAPI backend through:

- `GET /api/search` - Main search endpoint
- `GET /api/autocomplete` - Autocomplete suggestions
- `GET /api/webinars` - Webinar listings with filters
- `GET /api/categories` - Available categories
- `GET /api/speakers` - Speaker information

## Build Output

Production builds are optimized for:
- Minimal bundle size (< 500KB)
- Fast loading on mobile devices
- Static file serving from FastAPI backend