-- Idempotent seed data for development/testing

-- Seed: categories (authoritative taxonomy)
INSERT INTO categories (name, slug) VALUES
  ('Rekrutacja i selekcja', 'rekrutacja-selekcja'),
  ('Onboarding', 'onboarding'),
  ('Offboarding', 'offboarding'),
  ('Szkolenia i rozwój (L&D)', 'szkolenia-rozwoj'),
  ('Ocena wyników i feedback', 'ocena-wynikow-feedback'),
  ('Zarządzanie talentami i sukcesja', 'talent-sukcesja'),
  ('Wynagrodzenia i benefity', 'wynagrodzenia-benefity'),
  ('Prawo pracy i compliance (RODO/BHP)', 'prawo-pracy-compliance'),
  ('Relacje z pracownikami', 'employee-relations'),
  ('Kultura organizacyjna i zaangażowanie', 'kultura-zaangazowanie'),
  ('Różnorodność i inkluzja (D&I)', 'diversity-inclusion'),
  ('Well-being i BHP', 'wellbeing-bhp')
ON CONFLICT (slug) DO NOTHING;

-- Seed: tags (starter set)
INSERT INTO tags (name, slug) VALUES
  -- Rekrutacja i selekcja
  ('rekrutacja', 'rekrutacja'),
  ('selekcja', 'selekcja'),
  ('sourcing', 'sourcing'),
  ('ATS', 'ats'),
  ('opis stanowiska', 'job-description'),
  ('rozmowa kwalifikacyjna', 'rozmowa-kwalifikacyjna'),
  ('candidate experience', 'candidate-experience'),
  ('talent acquisition', 'talent-acquisition'),

  -- Onboarding / Offboarding
  ('onboarding', 'onboarding'),
  ('offboarding', 'offboarding'),
  ('exit interview', 'exit-interview'),

  -- L&D / Ocena
  ('szkolenia', 'szkolenia'),
  ('rozwój', 'rozwoj'),
  ('kompetencje', 'kompetencje'),
  ('reskilling', 'reskilling'),
  ('upskilling', 'upskilling'),
  ('feedback', 'feedback'),
  ('ocena pracownicza', 'ocena-pracownicza'),

  -- Talenty i sukcesja
  ('zarządzanie talentami', 'zarzadzanie-talentami'),
  ('plan sukcesji', 'plan-sukcesji'),

  -- Wynagrodzenia i benefity
  ('wynagrodzenia', 'wynagrodzenia'),
  ('benefity', 'benefity'),
  ('pay equity', 'pay-equity'),
  ('widełki płacowe', 'widelki-placowe'),
  ('PPK', 'ppk'),
  ('PPE', 'ppe'),
  ('kafeteria', 'kafeteria'),

  -- Prawo pracy i compliance
  ('prawo pracy', 'prawo-pracy'),
  ('RODO', 'rodo'),
  ('BHP', 'bhp'),
  ('czas pracy', 'czas-pracy'),
  ('dyscyplinarka', 'dyscyplinarka'),
  ('umowa o pracę', 'umowa-o-prace'),
  ('zlecenie', 'zlecenie'),

  -- Kultura / Zaangażowanie
  ('kultura organizacyjna', 'kultura-organizacyjna'),
  ('zaangażowanie', 'zaangazowanie'),
  ('komunikacja wewnętrzna', 'komunikacja-wewnetrzna'),
  ('wartości organizacyjne', 'wartosci-organizacyjne'),

  -- D&I
  ('diversity & inclusion', 'diversity-inclusion'),
  ('równość', 'rownosc'),
  ('antydyskryminacja', 'antydyskryminacja'),

  -- Well-being i BHP
  ('well-being', 'well-being'),
  ('stres', 'stres'),
  ('wypalenie zawodowe', 'wypalenie-zawodowe'),
  ('zdrowie psychiczne', 'zdrowie-psychiczne'),
  ('ergonomia', 'ergonomia'),

  -- Analityka HR / Praca zdalna
  ('HR analytics', 'hr-analytics'),
  ('KPI', 'kpi'),
  ('OKR', 'okr'),
  ('dashboardy', 'dashboardy'),
  ('remote work', 'remote-work'),
  ('hybrydowa praca', 'hybrid-work')
ON CONFLICT (slug) DO NOTHING;


