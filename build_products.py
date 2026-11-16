#!/usr/bin/env python3
"""Buduje products.js (baza produktów do skanera) ze źródeł:
 - arkusz Ferris "Product Master Data Sheet" (PolyMem, Nursicare: REF, UPC, GTIN-14)
 - cennik Curea 2026 (kody artykułów P1-…, C1DUO-…, P2-…, C2-…)
 - indeks towarów Subiekta (nazwy magazynowe = towary sprzedawane)
 - GTIN jednostkowe Curea z wykazu refundacyjnego MZ (2026-04-01)
Uruchom:  python3 build_products.py   → nadpisuje products.js obok skryptu.
"""
import csv, json, re, sys, datetime, openpyxl
from pathlib import Path

FERRIS = "/Volumes/TWARDY ZEW/SP/Archiwum/POLYMEM/PolyMem EAN kody/R-071A,R36 FMC Product Master Data Sheet.xlsx"
CUREA = "/Volumes/TWARDY ZEW/SP/CUREA/Cennik 2026.xlsx"
INDEKS = "/Users/paweljutkiewicz/Calude Code/SP AUTOMAT/MAGAZYN i FAKTURY/indeks_towarow.csv"
OUT = Path(__file__).with_name("products.js")

# GTIN jednostkowe Curea P1 (wykaz refundowanych wyrobów medycznych MZ, poz. 287-291, 2026-04-01)
CUREA_UNIT_GTIN = {"100100": "4260223630231", "100200": "4260223630248", "100300": "4260223630262",
                   "150150": "4260223630651", "200200": "4260223630255"}
NURSICARE_PL_EAN = "2735471314001"   # EAN-13 z pliku Broszury, IFU/EAN-13Nursicare.svg

def liczba(v):
    """Komórka arkusza → int; 'n/a', puste i teksty → 0."""
    try: return int(float(v))
    except (TypeError, ValueError): return 0

def gs1_check(digits):
    s = 0
    for i, ch in enumerate(reversed(digits)):
        s += int(ch) * (3 if i % 2 == 0 else 1)
    return str((10 - s % 10) % 10)

def valid_gtin(code):
    code = re.sub(r"\D", "", str(code))
    return len(code) in (8, 12, 13, 14) and gs1_check(code[:-1]) == code[-1]

def norm(code):
    """Klucz wyszukiwania: same cyfry, bez zer wiodących (GTIN-12/13/14 tego samego kodu = 1 klucz)."""
    return re.sub(r"\D", "", str(code)).lstrip("0")

products = []
by_sku = {}

def add(p):
    p.setdefault("kody", {"opakowanie": [], "sztuka": [], "karton": []})
    products.append(p); by_sku[p["sku"]] = p

# ---------- Ferris (PolyMem, OptiMem, Nursicare, SportsWrap) ----------
wb = openpyxl.load_workbook(FERRIS, data_only=True)
ws = wb["Master Data Sheet"]
ferris = {}
for r in ws.iter_rows(min_row=8, values_only=True):
    if r[0] is None: continue
    ref = str(r[0]).strip()
    rec = dict(ref=ref, nazwa_en=(r[11] or "").strip(), marka=(r[12] or "PolyMem").strip(),
               status=(r[2] or "").strip() if isinstance(r[2], str) else "", szt=liczba(r[29]), opak_w_kartonie=liczba(r[30]),
               wym_cm=(str(r[22]).strip() if r[22] else ""),
               upc_box=r[33], upc_pouch=r[34], gtin_box=r[36], gtin_pouch=r[37], gtin_case=r[35])
    ferris[ref] = rec

def ferris_codes(rec):
    k = {"opakowanie": [], "sztuka": [], "karton": []}
    for key, lvl in (("gtin_box", "opakowanie"), ("upc_box", "opakowanie"), ("gtin_pouch", "sztuka"),
                     ("upc_pouch", "sztuka"), ("gtin_case", "karton")):
        v = rec.get(key)
        if v and str(v).strip().lower() != "n/a":
            v = re.sub(r"\D", "", str(v))
            if v and valid_gtin(v) and v not in k[lvl]: k[lvl].append(v)
    return k

# ---------- Subiekt (towary sprzedawane) ----------
subiekt = []
with open(INDEKS, encoding="utf-8-sig") as f:
    for row in csv.DictReader(f, delimiter=";"):
        subiekt.append((row["Nazwa_magazyn"].strip(), int(row["szt_w_opakowaniu"] or 1)))

def polymem_ref(name):
    m = re.search(r"REF:?\s*(\d{3,4})", name)
    if m: return m.group(1)
    m = re.match(r"^(\d{3,4})-1$", name)
    if m: return m.group(1)
    m = re.search(r"\b(\d{4})(?:-1)?\b", name)
    if m: return m.group(1)
    if "Finger No 2" in name: return "4402"
    return None

CUREA_SIZE = {"5,5x7,5": "055075", "5,5x13": "055130", "7,5x7,5": "075075", "10x10": "100100", "10x20": "100200",
              "10x30": "100300", "15x15": "150150", "20x20": "200200", "20x30": "200300", "11x11": "110110",
              "20x52": "200520", "16x16": "160160", "12x12": "120120"}

def curea_code(name, szt):
    n = name.lower().replace(" ", "")
    size = None
    for k, v in CUREA_SIZE.items():
        if k.replace(" ", "") + "cm" in n or k.replace(" ", "") in n: size = v; break
    if not size: return None
    if "border" in n: fam = "P1B"
    elif "drain" in n: fam = "P1D"
    elif "p2active" in n or "p2active" in n: fam = "C2"
    elif "active" in n: fam = "C1DUO"
    elif "p2" in n: fam = "P2"
    else: fam = "P1"
    return f"{fam}-{size}-{szt}"

def curea_family_size(code):
    m = re.match(r"^([A-Z0-9]+)-(\d{6})-(\d+)$", code)
    return (m.group(1), m.group(2), int(m.group(3))) if m else (None, None, None)

# ---------- Curea cennik 2026 ----------
wb = openpyxl.load_workbook(CUREA, data_only=True)
ws = wb["Sheet1"]
curea_catalog = {}
for r in ws.iter_rows(min_row=2, values_only=True):
    if not r[2]: continue
    code = str(r[2]).strip()
    curea_catalog[code] = dict(produkt=str(r[0]).strip(), rozmiar=str(r[1]).strip(), szt=int(r[3]))

# ---------- Składanie ----------
for name, szt in subiekt:
    lname = name.lower()
    if lname.startswith("polymem") or re.match(r"^\d{3,4}-1$", name):
        ref = polymem_ref(name)
        REF_FIX = {"2686": "2868"}   # literówka w Subiekcie: 2686 = Ferris 2868 (#8 Oval Silicone Border, op. 5 szt.)
        rec = ferris.get(ref) or ferris.get(REF_FIX.get(ref, ""))
        if not rec:
            print("UWAGA: brak w arkuszu Ferris:", name, ref, file=sys.stderr); rec = dict(ref=ref or name, nazwa_en="", marka="PolyMem", szt=szt, wym_cm="")
        codes = ferris_codes(rec)
        lvl = "opakowanie" if szt > 1 else "sztuka"
        sku = f"{ref}" if szt > 1 else f"{ref}-1"
        add(dict(sku=sku, marka="PolyMem", nazwa=name, nazwa_en=rec["nazwa_en"], ref=ref, poziom=lvl,
                 szt_w_opak=szt, sprzedawany=True, wym_cm=rec.get("wym_cm", ""), opak_w_kartonie=rec.get("opak_w_kartonie", 0),
                 kody={"opakowanie": codes["opakowanie"] if lvl == "opakowanie" else [],
                       "sztuka": codes["sztuka"], "karton": codes["karton"] if lvl == "opakowanie" else []}))
    elif lname.startswith("curea"):
        code = curea_code(name, szt)
        fam, size, _ = curea_family_size(code or "")
        unit = CUREA_UNIT_GTIN.get(size) if fam == "P1" else None
        add(dict(sku=code or name, marka="Curea", nazwa=name, nazwa_en=(curea_catalog.get(code, {}).get("produkt", "") + " " + curea_catalog.get(code, {}).get("rozmiar", "")).strip(),
                 ref=code, poziom="opakowanie" if szt > 1 else "sztuka", szt_w_opak=szt, sprzedawany=True,
                 wym_cm=curea_catalog.get(code, {}).get("rozmiar", ""),
                 kody={"opakowanie": [], "sztuka": [unit] if unit else [], "karton": []}))
    elif lname.startswith("nursicare"):
        rec = ferris.get("400-EN")
        box = [NURSICARE_PL_EAN] if valid_gtin(NURSICARE_PL_EAN) else []
        for k, v in ferris.items():
            if k.startswith("400-"):
                for c in ferris_codes(v)["opakowanie"]:
                    if c not in box: box.append(c)
        pouch = ferris_codes(rec)["sztuka"]
        lvl = "opakowanie" if szt > 1 else "sztuka"
        add(dict(sku="400" if szt > 1 else "400-1", marka="Nursicare", nazwa=name, nazwa_en=rec["nazwa_en"], ref="400",
                 poziom=lvl, szt_w_opak=szt, sprzedawany=True, wym_cm="",
                 kody={"opakowanie": box if lvl == "opakowanie" else [], "sztuka": pouch, "karton": []}))
    else:
        marka = name.split()[0]
        add(dict(sku=re.sub(r"[^A-Za-z0-9]+", "-", name).strip("-"), marka=marka, nazwa=name, nazwa_en="", ref="",
                 poziom="opakowanie" if szt > 1 else "sztuka", szt_w_opak=szt, sprzedawany=True, wym_cm=""))

# katalog Ferris – pozycje niesprzedawane (do wyboru z listy, gdy ktoś zeskanuje nowy produkt)
for ref, rec in ferris.items():
    if ref.startswith("400-"): continue
    if any(p.get("ref") == ref and p["szt_w_opak"] > 1 for p in products): continue
    codes = ferris_codes(rec)
    add(dict(sku=ref, marka=rec["marka"] or "PolyMem", nazwa=f"{rec['marka']} REF {ref} op. {rec['szt']} szt.", nazwa_en=rec["nazwa_en"],
             ref=ref, poziom="opakowanie", szt_w_opak=rec["szt"], sprzedawany=False, wym_cm=rec.get("wym_cm", ""), opak_w_kartonie=rec.get("opak_w_kartonie", 0), kody=codes))
# katalog Curea 2026 – pozycje niesprzedawane
for code, c in curea_catalog.items():
    if code in by_sku: continue
    fam, size, szt = curea_family_size(code)
    unit = CUREA_UNIT_GTIN.get(size) if fam == "P1" else None
    add(dict(sku=code, marka="Curea", nazwa=f"{c['produkt']} {c['rozmiar']} op. {c['szt']} szt.", nazwa_en=f"{c['produkt']} {c['rozmiar']}",
             ref=code, poziom="opakowanie", szt_w_opak=c["szt"], sprzedawany=False, wym_cm=c["rozmiar"],
             kody={"opakowanie": [], "sztuka": [unit] if unit else [], "karton": []}))

# kody nauczone w aplikacji (eksport "kody_nauczone.csv": kod;sku;poziom) – opcjonalnie
learned = Path(__file__).with_name("kody_nauczone.csv")
if learned.exists():
    with open(learned, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f, delimiter=";"):
            p = by_sku.get(row["sku"].strip())
            if p and row["kod"].strip():
                lvl = row.get("poziom", "opakowanie").strip() or "opakowanie"
                if row["kod"].strip() not in p["kody"].setdefault(lvl, []): p["kody"][lvl].append(row["kod"].strip())
    print("dodano kody z", learned.name)

# indeks kod → SKU (klucz znormalizowany)
index = {}
for p in products:
    for lvl, lst in p["kody"].items():
        for c in lst:
            index.setdefault(norm(c), []).append({"sku": p["sku"], "poziom": lvl})

out = {"wygenerowano": datetime.date.today().isoformat(), "zrodla": [FERRIS, CUREA, INDEKS, "wykaz refundacyjny MZ 2026-04-01 (Curea P1 GTIN 1 szt.)"],
       "produkty": products, "indeks_kodow": index}
OUT.write_text("// Wygenerowane przez build_products.py – nie edytuj ręcznie.\nwindow.PRODUKTY = " + json.dumps(out, ensure_ascii=False, indent=1) + ";\n", encoding="utf-8")
print(f"{len(products)} produktów ({sum(p['sprzedawany'] for p in products)} sprzedawanych), {len(index)} kodów → {OUT}")
