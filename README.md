# Skaner magazynowy Support-Pharma

Aplikacja na iPhone (strona WWW / PWA) do skanowania opakowań w magazynie: kod produktu (GTIN/EAN/UPC lub kod QR
GS1), LOT i EXP. Tworzy listę zeskanowanych opakowań, porównuje ją z pack listą zamówienia i eksportuje CSV.

## Pliki
| Plik | Co to |
|---|---|
| `index.html` | cała aplikacja (jeden plik, po polsku) |
| `products.js` | baza produktów + indeks kodów (generowana, nie edytować ręcznie) |
| `build_products.py` | generator `products.js` ze źródeł (arkusz Ferris, cennik Curea 2026, indeks Subiekta) |
| `zxing.min.js` | biblioteka dekodująca kody (ZXing 0.21.3, kopia lokalna) |
| `sw.js`, `manifest.webmanifest` | praca offline i ikona „Dodaj do ekranu początkowego” |
| `artefakt.html` | ta sama aplikacja w wersji do publikacji jako artefakt claude.ai (tryb zdjęciowy) |
| `packlista_przyklad.csv` | przykład formatu pack listy |

## Jak uruchomić na iPhonie
Kamera na żywo działa tylko pod **https://** (wymóg Safari). Opcje:
1. **Hosting statyczny** (GitHub Pages, Netlify, Cloudflare Pages, własny serwer): wgrać cały folder. Otworzyć adres
   w Safari → Udostępnij → „Dodaj do ekranu początkowego”. Po pierwszym otwarciu działa offline.
2. **Artefakt claude.ai** (bez hostingu): wersja `artefakt.html`. W artefakcie Safari nie udostępnia kamery na żywo,
   więc aplikacja przełącza się w tryb „Zrób zdjęcie kodu” (zdjęcie → odczyt kodu). Dane sesji trafiają też do bazy
   artefaktu (kolekcja `sesje`), skąd agenci Claude mogą je czytać.

## Obsługa (3 kroki na opakowanie)
1. **Kod produktu** – EAN/UPC lub GS1-128 (PolyMem), kod QR/DataMatrix GS1 (Curea). Jeśli kod QR zawiera
   (01) GTIN + (17) EXP + (10) LOT, pozycja zapisuje się od razu.
2. **LOT** – kod kreskowy LOT (AI 10) albo zwykły tekst.
3. **EXP** – kod AI 17 (RRMMDD) albo data w dowolnym zapisie (2027-12-31, 31.12.2027, 12/2027, GRU 2027).

Nieznany kod → lista produktów (najpierw sprzedawane, filtr po marce z prefiksu GS1). Po wyborze kod jest
**zapamiętywany** (Więcej → Kody nauczone) – następny skan tego kodu rozpoznaje produkt automatycznie.
Przyciski: „Jak poprzednio” (przepisz LOT/EXP z ostatniej pozycji), „Zapisz bez LOT/EXP”, „Cofnij ostatni”.
Ustawienie „Ten sam produkt pod rząd” przepisuje LOT/EXP automatycznie (zeskanowany później LOT/EXP nadpisuje
ostatnią pozycję).

## Pack lista
Zakładka „Pack lista”: wklej linie `SKU lub nazwa ; LOT ; EXP ; ilość opakowań` (LOT/EXP opcjonalne), wczytaj plik
CSV albo dodaj pozycje z listy produktów. SKU = REF PolyMem (np. `5044`) lub kod artykułu Curea (np. `P1-100100-10`);
nazwy z Subiekta też działają. Postęp widać na ekranie skanowania: `7/10`, zielone „Zamówienie kompletne”,
czerwone **„ZA DUŻO: jest 11, miało być 10”** z innym dźwiękiem, żółte „Poza pack listą”.

## Eksport (Więcej)
* `skany_<sesja>.csv` – każdy skan: `lp;data_czas;sesja;sku;nazwa;marka;poziom;szt_w_opak;ilosc_opak;lot;exp;gtin;zrodlo;kod_surowy`
* `podsumowanie_<sesja>.csv` – grupy produkt+LOT+EXP: `sesja;sku;nazwa;lot;exp;ilosc_opak;szt_w_opak;ilosc_szt;pack_lista_ilosc;status`
  (status: `ok`, `brakuje`, `za_duzo`, `poza_lista`)
* `kody_nauczone.csv` – `kod;sku;poziom;nazwa;kiedy`. Skopiowany obok `build_products.py` zostaje wczytany do bazy
  przy następnym `python3 build_products.py`.
* JSON sesji (schowek) i kopia zapasowa wszystkich sesji (JSON).

Separator `;`, UTF-8 z BOM (Excel PL), daty ISO `RRRR-MM-DD`. `poziom` = `opakowanie` (kod pudełka) /
`sztuka` (kod saszetki) / `karton`. Na iPhonie eksport otwiera arkusz udostępniania (Pliki/iCloud, Mail, AirDrop).

## Baza produktów (`products.js`)
* PolyMem/Nursicare: REF, nazwy Subiekta, UPC i GTIN-14 pudełka/saszetki/kartonu z arkusza Ferris
  `R-071A,R36 FMC Product Master Data Sheet.xlsx` (108 REF). Literówka Subiekta „2686” zmapowana na Ferris 2868.
* Curea: kody artykułów z `Cennik 2026.xlsx` (P1, C1DUO, P2, C2), GTIN jednostkowe P1 10x10/10x20/10x30/15x15/20x20
  z wykazu refundacyjnego MZ (prefiks GS1 Curea: 426022363). **GTIN pudełek Curea nie są znane** – EUDAMED nie
  udostępnia filtra po producencie i ograniczył zapytania; kody uczą się przy pierwszym skanie.
* Nursicare: EAN-13 2735471314001 (plik `EAN-13Nursicare.svg`) + kody Ferris wariantów językowych 400-xx.
* `sprzedawany: true` = pozycja z indeksu Subiekta; reszta to katalog (do wyboru po zeskanowaniu nowego produktu).

Aktualizacja bazy: `python3 build_products.py` (wymaga podłączonego dysku TWARDY ZEW i openpyxl).
