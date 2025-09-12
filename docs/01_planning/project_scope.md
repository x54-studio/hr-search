# Project Scope

## Problem
CEO firmy szkoleniowej HR posiada 500+ webinarów i prezentacji PDF. 
Pracownicy działów HR (klienci) tracą 15-30 minut na znalezienie potrzebnego materiału.
Brak efektywnej wyszukiwarki = frustacja klientów i niewykorzystany potencjał bazy wiedzy.

## Cele
- Redukcja czasu wyszukiwania do < 2 minut
- Znalezienie materiałów nawet bez znajomości dokładnych tytułów
- Interface intuicyjny dla pracowników HR (nie-technicznych)

## Ograniczenia
- Budżet: projekt portfolio (1-2 osoby)
- Czas: 4-6 tygodni na MVP
- Dane: tylko tytuły, opisy, prelegenci (brak transkrypcji)
- Język: materiały tylko po polsku
- Infrastruktura: pojedynczy serwer na początek

## Metryki sukcesu
- 80% zapytań zwraca trafny wynik w top 3
- Czas odpowiedzi wyszukiwarki < 200ms
- Autocomplete < 50ms

## MVP Timeline (4 tygodnie)
- Tydzień 1-2: Setup bazy, import danych, generowanie embeddingów
- Tydzień 3: API + search logic
- Tydzień 4: Frontend + integracja