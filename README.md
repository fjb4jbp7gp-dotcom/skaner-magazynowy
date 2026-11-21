# Skaner magazynowy Support-Pharma

Aplikacja na iPhone (strona WWW / PWA) do skanowania opakowań w magazynie: kod produktu (GTIN/EAN/UPC lub kod QR
GS1), LOT i EXP. Tworzy listę zeskanowanych opakowań, porównuje ją z pack listą zamówienia i eksportuje CSV.

## Pliki
| Plik | Co to |
|---|---|
| `index.html` | cała aplikacja (jeden plik, po polsku) |
| `products.js` | baza produktów + indeks kodów (generowana, nie edytować ręcznie) |
| `build_products.py` | generator `products.js` ze źródeł (arkusz Ferris, cennik Curea 2026, indeks Subiekta) |
| `zxing-wasm-reader.js`, `zxing_reader.wasm` | silnik kodów ZXing C++ (WebAssembly, zxing-wasm 2.2.4) |
| `zxing.min.js` | silnik awaryjny (zxing-js 0.21.3) |
| `sw.js`, `manifest.webmanifest` | praca offline i ikona „Dodaj do ekranu początkowego” |
| `artefakt.html`, `build_artefakt.py` | ta sama aplikacja w wersji do publikacji jako artefakt claude.ai (tryb zdjęciowy) i jej generator |
| `wersja.txt` | numer opublikowanej wersji (aplikacja sprawdza go przy starcie) |
| `packlista_przyklad.csv` | przykład formatu pack listy |
| `packlisty/packlisty.enc` | pack listy dnia z Maca, zaszyfrowane (tworzy `SP AUTOMAT/bin/packlisty_skaner.py`) |

## Jak uruchomić na iPhonie
**Adres aplikacji (GitHub Pages): https://fjb4jbp7gp-dotcom.github.io/skaner-magazynowy/** – otworzyć w Safari,
Udostępnij → „Dodaj do ekranu początkowego”. Repozytorium: https://github.com/fjb4jbp7gp-dotcom/skaner-magazynowy
(aktualizacja = `git push`, Pages publikuje w ok. minutę).

Kamera na żywo działa tylko pod **https://** (wymóg Safari). Opcje:
1. **Hosting statyczny** (GitHub Pages, Netlify, Cloudflare Pages, własny serwer): wgrać cały folder. Otworzyć adres
   w Safari → Udostępnij → „Dodaj do ekranu początkowego”. Po pierwszym otwarciu działa offline.
2. **Artefakt claude.ai** (bez hostingu): wersja `artefakt.html`. W artefakcie Safari nie udostępnia kamery na żywo,
   więc aplikacja przełącza się w tryb „Zrób zdjęcie kodu” (zdjęcie → odczyt kodu). Dane sesji trafiają też do bazy
   artefaktu (kolekcja `sesje`), skąd agenci Claude mogą je czytać.

## Obsługa
Kamera czyta **wszystkie kody z kadru naraz** (zielona ramka = kod produktu, żółta = inny kod, np. LOT).
1. **Skieruj kamerę na etykietę.** Kod produktu (GS1-128 `(01)GTIN`, EAN/UPC, QR/DataMatrix GS1) i kod LOT z tej
   samej etykiety odczytują się w jednej klatce. Kod QR z (01)+(17)+(10) zapisuje pozycję od razu.
2. **EXP.** Na etykietach PolyMem data ważności jest tylko nadrukiem (klepsydra, np. `2031-06`), bez kodu.
   Wybierasz miesiąc i rok **raz na LOT** – aplikacja pamięta parę REF+LOT → EXP i kolejne opakowania tego LOT-u
   zapisuje sama. `2031-06` zapisuje się jako ostatni dzień miesiąca (`2031-06-30`).
3. **Następne opakowanie.** Zapisany kod jest blokowany, dopóki widać go w kadrze – odsuń telefon (ok. 1 s) i najedź
   na następną etykietę, albo dotknij „+1 takie samo”.

**Curea** (naklejka na pudełku): mały DataMatrix GS1 `(01)GTIN (17)EXP (10)LOT` + EAN-13 z tym samym GTIN. Kody
z tym samym GTIN są łączone w jedną pozycję, więc wystarczy jedna klatka z naklejką. Duży biały kod QR na pudełku
to adres strony producenta – jest pomijany. EXP z pack listy porównuje się po roku i miesiącu (`2031-08` pasuje
do `2031-08-01` z kodu).

**Sygnały (od v6).** Trzy rosnące tony + zielony błysk = pozycja ZAPISANA. Jedno krótkie „tuk” + żółty błysk =
krok przyjęty, skanuj dalej (np. Curea: produkt z EAN, czeka na kod z LOT). Dwa „pip-pip” + żółty błysk = potrzebne
dane na ekranie (EXP, liczba opakowań, wybór LOT). Niski brzęczyk = błąd lub ZA DUŻO. Fanfara + długi zielony błysk = pack lista KOMPLETNA (od v7). Produkt i LOT z tej samej
klatki dają jeden sygnał. Kamera jest przyklejona u góry ekranu i nie zmienia rozmiaru; podpowiedzi pokazują się
na podglądzie, a pasek pack listy ma stałą wysokość (2 linie, liczby na początku).

**PolyMem: case (od v6).** Pudełka PolyMem nie mają kodu LOT ani EXP; case ma kod produktu i kod LOT. Skanuj case –
aplikacja rozpoznaje go jako karton i **zawsze** pyta „Ile opakowań zostało w kartonie?” z przyciskami 1…N, gdzie
N = pełny karton z arkusza Ferris (np. 5044 = 4 op. × 15 szt.), podświetlony. Przy nowym LOT-cie na tym samym
ekranie jest pole EXP (raz na LOT, potem z pamięci). Ostatnie luźne pudełko: zeskanuj kod pudełka i wybierz LOT
z przycisków (LOT-y tego REF z sesji i z pamięci, z EXP). Curea zachowuje pamięć ilości na LOT.

**Kartony zbiorcze** (przyjęcie dostawy). Karton zapisuje się jako produkt „op. N szt.” z `poziom=karton`
i `ilosc_opak` = liczba opakowań w kartonie. Po rozpoznaniu produktu, LOT i EXP aplikacja pyta
„Ile opakowań w kartonie?” i pamięta odpowiedź **osobno dla każdego produktu i LOT-u** – kolejne kartony tego
samego LOT-u zapisują się same, a nowy LOT pyta ponownie z podpowiedzią ostatniej ilości. Podpowiedź bierze się
kolejno z: pamięci LOT-u, kodu kartonu `(37)`, ostatniej ilości dla produktu, danych producenta (PolyMem: arkusz
Ferris, np. REF 5077 = 2 opak.). Karton jest rozpoznawany, gdy:
* kod jest w bazie jako karton (PolyMem `(01)3…`, napis CASE),
* GTIN-14 kartonu to cyfra wskaźnikowa 1–8 + numer znanego opakowania, albo kod ma `(02)` GTIN zawartości,
* nieznany kod nauczono z zaznaczeniem „To kod kartonu zbiorczego”,
* włączony jest przełącznik **„Przyjmuję kartony zbiorcze”** na ekranie skanowania (gdy na kartonie jest ten sam
  kod co na pudełku).
Przycisk „To jedno opakowanie” cofa rozpoznanie kartonu. Zapamiętane ilości: Więcej → „Kartony: zapamiętane
ilości”. Ustawienie „pytaj przy każdym kartonie” wyłącza automatyczny zapis dla znanego LOT-u.

Nieznany kod produktu → lista produktów (najpierw sprzedawane, filtr po marce z prefiksu GS1). Po wyborze kod jest
**zapamiętywany** (Więcej → Kody nauczone). Kod bez GTIN (np. QR z samym tekstem) nie otwiera okna sam – pojawia się
podpowiedź z przyciskiem „To jest kod produktu”. Pasek pod podglądem pokazuje silnik, licznik klatek i widziane kody.
Przyciski: „Jak poprzednio”, „Zapisz bez LOT/EXP”, „Cofnij ostatni”, „Zoom 2×” i „Latarka” (gdy telefon je udostępnia).

**Wersja i odświeżanie.** Numer wersji widać w nagłówku („Skaner SP v4”) i na pasku pod podglądem, razem
z rozdzielczością kamery, czasem dekodowania i listą widzianych kodów. Aplikacja porównuje się z `wersja.txt`
i sama przeładowuje się do nowszej wersji. Przy publikacji zmienić numer w trzech miejscach: `WERSJA` w `index.html`,
`wersja.txt`, `CACHE` w `sw.js`. Przycisk **Klatka** na podglądzie zapisuje dokładnie ten obraz, który dostaje
dekoder (do diagnozy, gdy kod się nie czyta). Kamera pracuje w najwyższej dostępnej rozdzielczości (do 4K),
a dekoder czyta tylko widoczny fragment: szybko w małej skali i dokładnie w powiększeniu do 2× (małe DataMatrix).

Silnik kodów: ZXing C++ w WebAssembly (`zxing-wasm-reader.js` + `zxing_reader.wasm`, wersja 2.2.4, kopia lokalna).
Poprzedni silnik (zxing-js) nie czytał etykiet PolyMem z kamery; został jako awaryjny (`zxing.min.js`).

## Pack listy dnia (od v7)
Zakładka „Pack lista” → **Wczytaj pack listy**: telefon pobiera `packlisty/packlisty.enc` z repo (API GitHuba, zawsze
świeży plik) i odszyfrowuje go u siebie. Plik tworzy na Macu `SP AUTOMAT/bin/packlisty_skaner.py eksport` z:
* Allegro – `Zamówienia ALLEGRO/DD_MM_RRRR/pack_lista_….html` (skład listy dnia wysyłki, ANULOWANE, „Już nadane”,
  POBRANIE) + `stan/allegro_zamowienia/**/dane.csv` (punkt odbioru, odbiorca, miasto, pozycje z numerem oferty),
* poczta i sklepy – `Zamówienia MAIL/<NURSICARE|Nursicare HURT|Opatrunki|VET>/DD_MM_RR/HH-MM.html` + JSON przebiegu
  `agenci/poczta-spark-automat/data/packlisty/DDMMRR_HHMM.json`.

Jedna lista = jedno zamówienie. Nazwa: numer Paczkomatu albo punktu odbioru (InPost, Orlen, DPD, DHL…), kurier:
nazwisko + miasto (instytucja bez osoby: nazwa firmy + miasto). Dzień listy = dzień wysyłki (pt od 15:00, weekend
i dni wolne → najbliższy dzień roboczy, jak w `allegro.py`). Plik obejmuje 7 dni wstecz i 7 naprzód; domyślnie
otwiera się dziś albo najbliższy dzień z listami.

**Szyfrowanie.** Repo jest publiczne, więc dane klientów idą tylko zaszyfrowane: AES-256-CBC + HMAC-SHA256, klucz
w pęku kluczy Maca (usługa `sp-skaner-packlisty`). Klucz wpisuje się raz na telefonie: `python3 bin/packlisty_skaner.py
klucz` kopiuje go do schowka (wspólny schowek Mac–iPhone → „Wklej klucz”), a `klucz --qr` pokazuje kod QR na ekranie
Maca – wystarczy go zeskanować kamerą skanera. Plik zawiera tylko to, co potrzebne do pakowania: nazwę listy, klienta,
numer zamówienia, sposób dostawy, flagi i pozycje (bez adresów, telefonów i e-maili).

**Pozycje.** Mac mapuje towar na SKU: `config/skaner_mapowanie.csv` (np. `oferta 7381151822;400`), EAN, kod Curea,
REF/nr kat. PolyMem, Nursicare, rozmiar Curea z maila (op. 10 szt., 25 tylko gdy nazwa je podaje), dokładne słowa
nazwy (tylko poczta). Allegro bez wpisu w mapowaniu → pozycja „bez SKU”: po zeskanowaniu produktu skaner pyta, czy
to ta pozycja, i zapamiętuje odpowiedź (Więcej → `mapowanie_pozycji.csv` – dopisz do `config/skaner_mapowanie.csv`).
Zamówienie w sztukach, które dzieli się na całe opakowania, idzie jako opakowania (600 szt. → 40 op. po 15);
w przeciwnym razie pozycja jest w sztukach, liczonych po REF – przy pudełku z większą liczbą sztuk niż zostało
skaner pyta „Ile sztuk wydajesz z tego opakowania?”.

**Przełączanie.** Dotknięcie listy uruchamia ją (sesja = lista, skany zostają przy liście). Przycisk w nagłówku
i „Listy” na pasku skanowania otwierają listy dnia. Po skanie, który domyka listę w 100%, gra **fanfara**
(inna niż zapis pozycji) i pojawia się jeden przycisk **„Następna lista: …”** – następna niekompletna lista tego
dnia (najpierw nienadane). Listy ANULOWANE i WSTRZYMANE są oznaczone; skan na nich daje sygnał błędu.

**CSV: wszystkie listy dnia** – naraz `pack_<dzień>_WSZYSTKIE.csv` i po jednym `pack_<dzień>_<lista>.csv`
(na iPhonie jeden arkusz udostępniania → „Zapisz w Plikach”). Kolumny:
`dzien;lista;zrodlo;nr_zamowienia;klient;status_listy;sku;nazwa;nazwa_z_zamowienia;zamowiono;jednostka;wydano_lacznie;lot;exp;wydano_z_lot;ilosc_szt_z_lot;status_pozycji`.
Wiersz = pozycja listy × (LOT, EXP); pozycja bez skanów ma jeden wiersz z zerem. `status_listy`: `komplet`, `w_toku`,
`nie_rozpoczeta`, `za_duzo`, `anulowane`, `wstrzymane`; `status_pozycji`: `ok`, `brakuje`, `za_duzo`, `nierozpoznana`,
`poza_lista`. `jednostka`: `op` albo `szt`.

**Aktualizacja na Macu** – launchd `pl.support-pharma.sp-packlisty-skaner` (wzór w `SP AUTOMAT/launchd/`) co 10 minut;
plik zmienia się i trafia na GitHub tylko wtedy, gdy zmieniła się treść list. Log: `SP AUTOMAT/logs/packlisty_skaner.log`.
Podgląd bez zapisu: `python3 bin/packlisty_skaner.py podglad [--dzien RRRR-MM-DD]`.

## Pack lista ręczna
Zakładka „Pack lista” → „Ręczna pack lista”: wklej linie `SKU lub nazwa ; LOT ; EXP ; ilość opakowań` (LOT/EXP opcjonalne), wczytaj plik
CSV albo dodaj pozycje z listy produktów. SKU = REF PolyMem (np. `5044`) lub kod artykułu Curea (np. `P1-100100-10`);
nazwy z Subiekta też działają. Postęp widać na ekranie skanowania: `7/10`, zielone „Komplet”,
czerwone **„ZA DUŻO: jest 11, miało być 10”** z innym dźwiękiem, czerwone „Nie ma na liście”.

## Eksport (Więcej)
* `skany_<sesja>.csv` – każdy skan: `lp;data_czas;sesja;sku;nazwa;marka;poziom;szt_w_opak;ilosc_opak;lot;exp;gtin;zrodlo;kod_surowy`
* `podsumowanie_<sesja>.csv` – grupy produkt+LOT+EXP: `sesja;sku;nazwa;lot;exp;ilosc_opak;szt_w_opak;ilosc_szt;pack_lista_ilosc;status`
  (status: `ok`, `brakuje`, `za_duzo`, `poza_lista`)
* `kody_nauczone.csv` – `kod;sku;poziom;nazwa;kiedy`. Skopiowany obok `build_products.py` zostaje wczytany do bazy
  przy następnym `python3 build_products.py`.
* JSON sesji (schowek) i kopia zapasowa wszystkich sesji (JSON).

Separator `;`, UTF-8 z BOM (Excel PL), daty ISO `RRRR-MM-DD`. `poziom` = `opakowanie` (kod pudełka) /
`sztuka` (kod saszetki) / `karton` (kod kartonu zbiorczego; `ilosc_opak` = liczba opakowań w kartonie). Na iPhonie eksport otwiera arkusz udostępniania (Pliki/iCloud, Mail, AirDrop).

## Baza produktów (`products.js`)
* PolyMem/Nursicare: REF, nazwy Subiekta, UPC i GTIN-14 pudełka/saszetki/kartonu z arkusza Ferris
  `R-071A,R36 FMC Product Master Data Sheet.xlsx` (108 REF). Literówka Subiekta „2686” zmapowana na Ferris 2868.
* Curea: kody artykułów z `Cennik 2026.xlsx` (P1, C1DUO, P2, C2), GTIN jednostkowe P1 10x10/10x20/10x30/15x15/20x20
  z wykazu refundacyjnego MZ (prefiks GS1 Curea: 426022363). Z etykiety potwierdzony GTIN pudełka
  P1-100100-10: 4260223630026. **Pozostałe GTIN pudełek Curea nie są znane** – EUDAMED nie
  udostępnia filtra po producencie i ograniczył zapytania; kody uczą się przy pierwszym skanie.
* Nursicare: EAN-13 2735471314001 (plik `EAN-13Nursicare.svg`) + kody Ferris wariantów językowych 400-xx.
* `sprzedawany: true` = pozycja z indeksu Subiekta; reszta to katalog (do wyboru po zeskanowaniu nowego produktu).

Aktualizacja bazy: `python3 build_products.py` (wymaga podłączonego dysku TWARDY ZEW i openpyxl).
