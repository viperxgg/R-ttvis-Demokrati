# Rättvis Demokrati — kampanjwebbplats

Kampanjwebbplats för **Rättvis Demokrati**, ett lokalt parti i Strömsunds kommun.
Kommunvalet · 13 september 2026 · [rattvisdemokrati.pro](https://rattvisdemokrati.pro)

## Struktur

- `index.html` — startsidan
- `aktuellt/`, `nyheter/`, `lag/`, `alvgarden/`, `kontakta/` — webbplatsens undersidor
- `assets/` — logotyp, foton, kampanjbilder och PDF-filer som används på webbplatsen
- `scripts/` — automatisk uppdatering av Kommunbevakningen
- `social/` — färdiga sociala medier-bilder och redigerbara HTML-original
- `design-export/` — designreferenser samt utskrifts- och QR-material

Webbplatsen är statisk HTML/CSS/JS och kräver ingen byggprocess.

## Kör lokalt

```
python -m http.server 8317 --directory .
```

Öppna sedan `http://localhost:8317`.

## Produktionsmaterial

Färdiga bilder för Facebook finns i `social/` tillsammans med redigerbara HTML-original. Öppna ett HTML-original i webbläsaren och exportera det i filnamnets angivna storlek.

QR-affischen kan återskapas med:

```
python -m pip install Pillow qrcode
python design-export/generate_a4_qr_poster.py
```

Skriptet skapar PNG, PDF och en fristående QR-kod som leder till webbplatsens HTTPS-adress.

## Status

**Lanserad:** [rattvisdemokrati.pro](https://rattvisdemokrati.pro)

GitHub Pages publicerar automatiskt från `main`. HTTPS är aktiverat och Kommunbevakningen uppdateras automatiskt två gånger per dygn via GitHub Actions.
