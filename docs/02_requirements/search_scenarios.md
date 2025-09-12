# Search Scenarios

## Scenariusz 1: Wyszukiwanie konceptualne
**Input:** "jak radzić sobie z wypaleniem zawodowym"
**Oczekiwane wyniki:**
1. "Wypalenie zawodowe - jak rozpoznać i przeciwdziałać" (score: 0.92)
2. "Stres w pracy - techniki zarządzania" (score: 0.83)
3. "Well-being w organizacji" (score: 0.78)

## Scenariusz 2: Wyszukiwanie po prelegencie
**Input:** "kowalski"
**Oczekiwane wyniki:**
- Wszystkie webinary gdzie "Kowalski" jest w polu speakers
- Sortowane po dacie (najnowsze pierwsze)
- Autocomplete pokazuje: "Jan Kowalski", "Anna Kowalska"

## Scenariusz 3: Błąd w pisowni + fuzzy
**Input:** "rekrutcja" (błąd)
**Autocomplete podpowiada:** 
- "Czy chodziło Ci o: rekrutacja?"
- Pokazuje wyniki dla "rekrutacja" mimo błędu

## Scenariusz 4: Fraza branżowa HR
**Input:** "exit interview"
**Oczekiwane wyniki:**
1. "Rozmowa wyjściowa z pracownikiem"
2. "Offboarding - dobre praktyki"
3. "Jak przeprowadzić exit interview"

## Scenariusz 5: Problem bez słów kluczowych
**Input:** "pracownik często się spóźnia co robić"
**Oczekiwane wyniki:**
1. "Dyscyplina pracy - aspekty prawne" (score: 0.81)
2. "Trudne rozmowy z pracownikami" (score: 0.79)
3. "Kodeks pracy - upomnienia i kary" (score: 0.75)

## Scenariusz 6: Krótkie zapytanie (1-2 znaki)
**Input:** "m"
**Autocomplete pokazuje:**
- "Motywacja pracowników"
- "Mobbing w miejscu pracy"
- "Magdalena Nowak" (prelegentka)

## Scenariusz 7: Puste wyniki
**Input:** "blockchain w HR"
**Oczekiwane zachowanie:**
- Komunikat: "Nie znaleziono wyników dla 'blockchain w HR'"
- Sugestia: "Sprawdź pisownię lub spróbuj innych słów kluczowych"
- Pokazanie 3 najpopularniejszych webinarów jako alternatywa

## Scenariusz 8: Mobile search
**Kontekst:** Użytkownik na telefonie w tramwaju
**Input:** Wpisuje jedną ręką "motyw"
**Oczekiwane:**
- Autocomplete pojawia się nad klawiaturą
- Duże obszary klikalne (cały wiersz)
- Możliwość przewijania listy jednym palcem

## Metryki sukcesu
- 80% zapytań zwraca trafny wynik w top 3
- Czas do kliknięcia w wynik < 10 sekund
- Bounce rate < 20% (użytkownik znajduje to czego szukał)