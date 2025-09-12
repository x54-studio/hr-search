# Technical Feasibility

## Dlaczego wyszukiwanie semantyczne?
Pracownicy HR szukają rozwiązań problemów, nie konkretnych tytułów:
- Zapytanie: "jak zmotywować zespół"
- Powinno znaleźć: "Budowanie zaangażowania", "Motywacja pracowników", "Leadership"

Klasyczne keyword search tego nie załatwi.

## Stack technologiczny
- **Embeddingi**: paraphrase-multilingual-MiniLM-L12-v2 - wspiera polski + angielskie terminy HR
- **Baza wektorowa**: PostgreSQL + pgvector (wystarczy dla 1000 dokumentów)
- **Prefix search**: PostgreSQL z indeksem text_pattern_ops
- **Backend**: FastAPI (async, szybki, prosty deployment)
- **Frontend**: React + TypeScript

## Algorytm wyszukiwania hybrydowego
1. **Semantic search** (waga 0.6): cosine similarity na embeddingach
2. **Keyword search** (waga 0.4): PostgreSQL full-text search
3. **Fuzzy matching**: pg_trgm extension dla tolerancji błędów

## Mobile considerations
- Responsive design (nie PWA - zbędna komplikacja dla MVP)
- Touch targets minimum 44x44px
- Viewport meta tag przeciw auto-zoom
- Brak sztucznych opóźnień (instant search)

## Dlaczego NIE używamy gotowych rozwiązań?
- Algolia/Elasticsearch: overkill dla 1000 dokumentów + miesięczne koszty
- OpenAI embeddings: $0.13/1M tokenów - zbędny koszt, lokalne modele wystarczą
- Pinecone: dopiero przy 10k+ dokumentów ma sens

## Ryzyka techniczne
- **Jakość embeddingów**: Model multilingual może być gorszy od dedykowanego polskiego
- **Mieszanie języków**: "exit interview" vs "rozmowa wyjściowa" - różne embeddingi dla tego samego
- **Brak transkrypcji**: Wyszukiwanie tylko po metadanych ogranicza trafność
- **Cold start**: Pierwsze wczytanie modelu ~2-3s (można cache'ować w pamięci)