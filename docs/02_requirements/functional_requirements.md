# Functional Requirements

## FR-001: Wyszukiwanie semantyczne
- Input: zapytanie tekstowe (2-200 znaków)
- Output: lista maksymalnie 20 wyników rankingowanych wg podobieństwa
- Próg podobieństwa: 0.7 (cosine similarity)
- Czas odpowiedzi: < 200ms dla 95% zapytań

## FR-002: Autocomplete
- Aktywacja: od 1 znaku (natychmiast)
- Czas odpowiedzi: < 50ms
- Lista: 8-10 sugestii z formatem:
  - Tytuł webinaru (pogrubiony)
  - Fragment opisu (max 2 linie)
  - Prelegent + data (szare, mniejsze)
- Nawigacja klawiaturowa: strzałki góra/dół, Enter, Escape
- Hover: podświetlenie całego wiersza

## FR-003: Filtry
- Typ: webinar / PDF
- Kategoria: 8 kategorii HR (rekrutacja, rozwój, prawo pracy, etc.)
- Data: ostatnie 30/90/365 dni
- Filtry działają na już wyszukanych wynikach (post-filtering)

## FR-004: Wyświetlanie wyników
Każdy wynik zawiera:
- Miniaturka lub ikona typu
- Tytuł (bold dla dopasowanych słów)
- Opis (max 150 znaków)
- Prelegent + data + czas trwania
- Score podobieństwa (debug mode dla developera)

## FR-005: Interface wyszukiwania
- Centralne pole wyszukiwania (szerokość 600px na desktop)
- Placeholder: "Szukaj webinaru, tematu lub prelegenta..."
- Ikona lupy po lewej, X do czyszczenia po prawej
- Lista autocomplete pojawia się jako overlay
- Kliknięcie poza listą zamyka autocomplete

## FR-006: Mobile First Design
- Responsive design: 320px (iPhone SE) do 1920px (desktop)
- Touch-friendly: przyciski min 44x44px (iOS HIG)
- Autocomplete na mobile: pełna szerokość ekranu
- Soft keyboard: nie zasłania wyników
- Swipe do zamknięcia autocomplete
- Viewport: zapobieganie auto-zoom przy focus na input

## Wymagania niefunkcjonalne
- Dostępność: 99% w godzinach pracy (8-17)
- Concurrent users: min 10
- Browser support: Chrome/Firefox/Safari (ostatnie 2 wersje)