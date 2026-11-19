# Trener · Siłownia – wersja 2 (aplikacja Androida)

To ta sama aplikacja co wersja 1, tylko zapakowana jako **prawdziwa aplikacja Androida**.
Największa różnica: **powiadomienie o końcu przerwy jest alarmem systemu**, więc przychodzi
nawet wtedy, gdy jesteś w innej aplikacji albo ekran jest wygaszony.

Wersja 1 (strona w Chrome) zostaje bez zmian. Dane obu wersji są osobne.

## Zawartość
- `www/` – aplikacja (to jest Twój `index.html` z dodatkiem obsługi natywnych powiadomień),
- `capacitor.config.json`, `package.json` – ustawienia opakowania Androida,
- `native/` – ikony, klucz podpisu i skrypt poprawek projektu,
- `.github/workflows/build-apk.yml` – instrukcja budowania APK w chmurze GitHuba (kopia w `workflow/`).

## Jak zbudować APK (bez komputera z Android Studio)
1. Na github.com utwórz **nowe repozytorium** (np. `silownia-android`), może być prywatne.
2. Wgraj do niego **całą zawartość tego folderu** (Add file → Upload files). Folder `.github` jest ukryty
   i niektóre systemy go pomijają. Jeśli go nie widać w repozytorium: Add file → Create new file,
   wpisz nazwę `.github/workflows/build-apk.yml` i wklej treść z pliku `workflow/build-apk.yml`.
3. Wejdź w zakładkę **Actions** → **Zbuduj APK** → **Run workflow**. Budowanie trwa kilka minut.
4. Po zakończeniu otwórz uruchomienie i pobierz z sekcji **Artifacts** plik **Silownia-APK**
   (to ZIP, w środku jest `app-debug.apk`).
5. Przenieś APK na telefon i zainstaluj. Android zapyta o zgodę na instalację z nieznanych źródeł,
   a Play Protect może ostrzec, bo aplikacja nie pochodzi ze sklepu. Wybierz „Zainstaluj mimo to”.

Każda zmiana plików w repozytorium sama uruchamia nowe budowanie. Nowy APK instaluje się **na poprzednim
bez utraty danych**, bo wszystkie wersje są podpisane tym samym kluczem (`native/debug.keystore`).
To klucz do własnego użytku, nie do sklepu Google Play.

## Przeniesienie danych z wersji 1
1. W wersji 1: Ustawienia i edycja planu → Dane → **Eksport** (zapisz plik JSON).
2. W wersji 2: Ustawienia i edycja planu → Dane → **Import** i wybierz ten plik.

Eksport w wersji 2 otwiera okno udostępniania telefonu: wybierz Dysk Google, Pliki albo wyślij sobie plik.

## Pierwsze uruchomienie
- Zezwól na **powiadomienia**.
- Jeśli telefon zapyta o **Alarmy i przypomnienia**, zezwól. Dzięki temu przerwa kończy się dokładnie o czasie.
- W Ustawieniach użyj „Wyślij test”, przełącz się na inną aplikację i sprawdź, czy powiadomienie przyjdzie.

## Co się zmieniło względem wersji 1
- Powiadomienia: alarm systemu (AlarmManager) zamiast usługi w przeglądarce.
- Brak service workera i pamięci podręcznej (nie są potrzebne, bo pliki są w aplikacji).
- Brak karty „Zainstaluj aplikację” i podpowiedzi o Chrome w Ustawieniach.
- Czarny ekran startowy, ikona aplikacji i biała ikona powiadomienia w pasku.

## Gdyby budowanie się nie udało
Otwórz nieudane uruchomienie w zakładce Actions, skopiuj komunikat błędu z czerwonego kroku
i wyślij go, a poprawię konfigurację. Pierwsze budowanie nowego projektu bywa kapryśne.
