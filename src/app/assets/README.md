# Lemonade App Icons 🍋

Professionelle Icons für die Lemonade Electron Desktop-Anwendung.

## 📦 Icon-Dateien

Alle Icons befinden sich in `assets/`:

| Datei | Größe | Verwendung |
|-------|-------|-----------|
| `icon.svg` | Skalierbar | Quelle (Vektor) |
| `icon_16.png` | 16x16px | Menüleiste, Taskbar |
| `icon_24.png` | 24x24px | UI-Elemente |
| `icon_32.png` | 32x32px | Fenster-Symbole |
| `icon_48.png` | 48x48px | Größere Symbole |
| `icon_64.png` | 64x64px | App-Fenster Header |
| `icon_128.png` | 128x128px | Start-Menü (Windows) |
| `icon_256.png` | 256x256px | **Windows Installer** ⭐ |
| `icon_512.png` | 512x512px | **macOS / Linux** ⭐ |

## 🎨 Icon-Design

- **Farben:** Gelb/Orange Farbverlauf (Lemonade-Theme)
- **Motiv:** Zwei verbundene Zitronen mit Blättern
- **Stil:** Modernes, einfaches Design mit Glanz-Effekten
- **Hintergrund:** Transparent (PNG) / Gelb (SVG)

## 🛠️ Icon generieren (Regeneration)

Falls du das Icon-Design ändern möchtest:

```bash
cd src/app/assets
python generate_icons.py
```

Das Skript regeneriert alle PNG-Dateien aus der SVG-Quelle.

## 📋 Integration in electron-builder

Die `package.json` ist bereits konfiguriert:

```json
"build": {
  "win": {
    "icon": "src/app/assets/icon_256.png"
  },
  "mac": {
    "icon": "src/app/assets/icon_512.png"
  },
  "linux": {
    "icon": "src/app/assets/icon_512.png"
  }
}
```

## 🚀 App bauen

```bash
# Windows
npm run build:win

# macOS
npm run build:mac

# Linux
npm run build:linux

# Alle Plattformen
npm run build
```

## 📝 SVG bearbeiten

Um das Icon-Design zu ändern:

1. Öffne `icon.svg` in einem SVG-Editor:
   - Figma (online, kostenlos)
   - Inkscape (lokal, kostenlos)
   - Adobe Illustrator

2. Ändere Farben, Formen, etc.

3. Speichere die SVG

4. Regeneriere die PNGs:
   ```bash
   python generate_icons.py
   ```

## 📸 Icon-Vorschau

Das Icon zeigt:
- 🍋 Zwei Zitronen (Lemonade = 2x die Kraft!)
- 🌿 Grüne Blätter (Frische)
- ⚡ Glanz-Effekte (Lebendigkeit)
- 💛 Gelb/Orange Farbverlauf

## ✅ Checkliste vor Release

- [ ] Icon-Design in allen Größen testen
- [ ] `npm run build:win/mac/linux` durchführen
- [ ] Installer/DMG/AppImage im Explorer anschauen
- [ ] Icon wird korrekt in Taskbar/Dock angezeigt
- [ ] Icon-Qualität auf verschiedenen Bildschirmen testen

---

**Erstellt:** 19. Januar 2026  
**Format:** PNG (optimiert) + SVG (Vektor)  
**Status:** ✅ Produktionsbereit
