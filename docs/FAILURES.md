# Niekompletne dane i aktualizacja baseline

Nieudany odczyt ACL lub ADS nie oznacza braku zmian. W trybie `--extended`
wynik zawiera `INCOMPLETE` i `ok: false`, nawet gdy dwie próby zwróciły takie same
wartości UNKNOWN. Strumień ADS bez hasha także pozostaje niezweryfikowany.

Nowy baseline nie jest tworzony z niekompletnych danych rozszerzonych.
Niekompletny odczyt nie zastępuje istniejącego baseline przy update.
Poprawna aktualizacja nadal wymaga `--accept-changes` i zapisuje wcześniejszy
baseline w osobnym pliku `.bak`. Błąd atomowego zapisu zachowuje poprzedni plik.

Uszkodzone wpisy baseline są odrzucane przed porównaniem lub aktualizacją.
`UNCHANGED` oznacza zgodność porównanych danych, ale `INCOMPLETE` ma pierwszeństwo
przy ustalaniu końcowego powodzenia weryfikacji.
