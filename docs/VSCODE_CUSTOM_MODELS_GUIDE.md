# VS Code GitHub Copilot - Custom Lemonade Models hinzufügen

## Übersicht

Diese Anleitung zeigt, wie du die 4 lokalen Lemonade-Modelle zu VS Code's GitHub Copilot hinzufügst, um sie direkt im Editor zu verwenden.

---

## Voraussetzungen

✓ Lemonade Server läuft auf `http://localhost:8000`  
✓ Alle 4 Modelle sind geladen:
- Qwen3-Next-80B @ 32k
- Qwen3-Coder-30B @ 64k  
- Gemma-3-4b @ 16k
- Whisper-Large-v3-Turbo

---

## Schritt-für-Schritt: Custom Model hinzufügen

### 1. AI Toolkit öffnen
- Öffne VS Code
- Klick auf **AI TOOLKIT** Symbol in der Sidebar (linke Seite)
- Oder: `Ctrl+Shift+A`

### 2. Models-Sektion erweitern
- Klick auf **MY RESOURCES** → **Models**
- Sehe die vorhandenen Model-Provider:
  - Microsoft Foundry
  - Custom
  - Windows AI API

### 3. Custom Model hinzufügen
- Klick auf **Custom** (oder das Menü)
- Wähle: **Add Custom Model**

---

## Modell-Konfiguration

Die Software führt dich durch 4 Schritte:

### **Schritt 1/4: API Endpoint URL**
```
Label: Enter OpenAI compatible chat completion endpoint URL

Input: http://localhost:8000/api/v1/chat/completions

Beschreibung: Das ist der Lemonade Server API Endpoint
```

### **Schritt 2/4: Model Name**
```
Label: Enter the exact model name as in the API

Input: [Model ID from /api/v1/models]

Beispiele:
  • Qwen3-Next-80B-A3B-Instruct-GGUF
  • Qwen3-Coder-30B-A3B-Instruct-GGUF
  • Gemma-3-4b-it-GGUF
  • Whisper-Large-v3-Turbo
```

### **Schritt 3/4: Display Name**
```
Label: Enter display model name. Default will be [Model Name]

Input: [Benutzerfreundlicher Name]

Beispiele:
  • Qwen3 Next 80B (Reasoning)
  • Qwen3 Coder 30B (Code)
  • Gemma 3 4B (Vision)
  • Whisper (Audio)
```

### **Schritt 4/4: API Key**
```
Label: Enter API key

Input: 1234

Hinweis: Lemonade Server benötigt keinen echten API Key
         Beliebiger Wert (z.B. "1234" oder "test") funktioniert
         
Speichern: Wird verschlüsselt unter $HOME/.aitk/models/my-models.yml
```

---

## Vollständiges Setup - Alle 4 Modelle

Wiederhole die Schritte 1-4 für jedes Modell:

### **Model 1: Reasoning**
| Feld | Wert |
|------|------|
| **Endpoint** | `http://localhost:8000/api/v1/chat/completions` |
| **Model Name** | `Qwen3-Next-80B-A3B-Instruct-GGUF` |
| **Display Name** | `Qwen3 Next 80B (Reasoning)` |
| **API Key** | `1234` |

### **Model 2: Coding** ← 64k Context!
| Feld | Wert |
|------|------|
| **Endpoint** | `http://localhost:8000/api/v1/chat/completions` |
| **Model Name** | `Qwen3-Coder-30B-A3B-Instruct-GGUF` |
| **Display Name** | `Qwen3 Coder 30B (64k Context)` |
| **API Key** | `1234` |

### **Model 3: Vision**
| Feld | Wert |
|------|------|
| **Endpoint** | `http://localhost:8000/api/v1/chat/completions` |
| **Model Name** | `Gemma-3-4b-it-GGUF` |
| **Display Name** | `Gemma 3 4B (Vision)` |
| **API Key** | `1234` |

### **Model 4: Audio**
| Feld | Wert |
|------|------|
| **Endpoint** | `http://localhost:8000/api/v1/chat/completions` |
| **Model Name** | `Whisper-Large-v3-Turbo` |
| **Display Name** | `Whisper Large (Audio)` |
| **API Key** | `1234` |

---

## Nach der Konfiguration

### Modelle verwenden
1. Öffne ein beliebiges Datei in VS Code
2. Öffne **GitHub Copilot Chat** (Ctrl+Shift+I oder Icon)
3. Klick auf Model-Selector oben (z.B. "Claude Haiku 4.5")
4. Wähle eines deiner Custom Models:
   - ✓ Qwen3 Next 80B (Reasoning)
   - ✓ Qwen3 Coder 30B (64k Context)
   - ✓ Gemma 3 4B (Vision)
   - ✓ Whisper Large (Audio)

### Model bearbeiten
- **Edit**: Rechtsklick auf Model → **Edit**
- **Delete**: Rechtsklick auf Model → **Delete**
- **Manage Models**: Klick auf "Manage Models..." Button

---

## Speicherort der Konfiguration

Deine Custom Models werden gespeichert unter:

```
$HOME/.aitk/models/my-models.yml
```

**Windows**: `C:\Users\[USERNAME]\.aitk\models\my-models.yml`

Beispiel Dateiinhalt:
```yaml
models:
  - name: Qwen3-Next-80B-A3B-Instruct-GGUF
    displayName: Qwen3 Next 80B (Reasoning)
    apiEndpoint: http://localhost:8000/api/v1/chat/completions
    apiKey: 1234
    
  - name: Qwen3-Coder-30B-A3B-Instruct-GGUF
    displayName: Qwen3 Coder 30B (64k Context)
    apiEndpoint: http://localhost:8000/api/v1/chat/completions
    apiKey: 1234
```

---

## Troubleshooting

### ❌ "Model not found"
**Problem**: VS Code kann das Modell nicht finden  
**Lösung**: 
- Verifiziere Endpoint: `curl http://localhost:8000/api/v1/models`
- Stelle sicher, dass Lemonade Server läuft
- Überprüfe exakten Model Name (Case-sensitive!)

### ❌ "Connection refused"
**Problem**: VS Code kann sich nicht mit Lemonade Server verbinden  
**Lösung**:
- Lemonade Server ist nicht aktiv: `lemonade-server serve --port 8000`
- Port ist falsch: Benutze `http://localhost:8000`
- Firewall blockiert: Lokale Verbindung sollte funktionieren

### ❌ "Invalid API Key"
**Problem**: API Key wird nicht akzeptiert  
**Lösung**:
- Lemonade benötigt keinen echten Key
- Beliebiger Wert funktioniert (z.B. "1234", "test", "key")
- Im Feld nicht leerlassen

### ⚠️ Modell antwortet langsam
**Problem**: Responses dauern zu lange  
**Lösung**:
- Überprüfe VRAM Auslastung (sollte ~98 GB bei Option 1 sein)
- Reduze `max_tokens` in Chat-Anfrage
- Nutze kleineres Modell (Gemma statt Qwen80B)

---

## Best Practices

### Modelle für verschiedene Tasks
```
┌─────────────────────────────────────────────────┐
│ TASK              │ EMPFOHLENES MODELL         │
├─────────────────────────────────────────────────┤
│ Code-Generierung  │ Qwen3 Coder 30B (64k) ⭐  │
│ Code-Review       │ Qwen3 Coder 30B (64k) ⭐  │
│ Reasoning         │ Qwen3 Next 80B            │
│ Quick Answer      │ Gemma 3 4B                │
│ Audio-Transkript  │ Whisper Large             │
└─────────────────────────────────────────────────┘
```

### Tips für beste Ergebnisse
1. **Coder-Task**: Nutze Qwen3-Coder (optimiert für Code)
2. **Lange Kontexte**: Nutze 64k Context bei Coder (Option 1)
3. **Schnelle Antworten**: Gemma ist schneller (~2.1s latency)
4. **Komplexe Probleme**: Qwen3-Next für Best-in-Class Reasoning

---

## Integration mit GitHub Copilot Workflow

### Szenario: Code-Review im Editor
```
1. Öffne Code-Datei in VS Code
2. Wähle Qwen3 Coder 30B aus Model-Selector
3. Schreibe Prompt: "@codebase Review this function"
4. Erhalte detaillierte Analyse mit 64k Context!
```

### Szenario: Multi-Model Workflow
```
1. Quick Question → Gemma 3 (schnell)
2. Detaillierte Analyse → Qwen3 Next 80B (powerful)
3. Code-Implementierung → Qwen3 Coder 30B (specialized)
```

---

## Nächste Schritte

Nach Setup kannst du:
- ✅ Alle 4 Lemonade-Modelle in VS Code nutzen
- ✅ Code mit 64k Context schreiben/reviewen
- ✅ Multimodale Workflows aufbauen (Code + Vision + Audio)
- ✅ 100% lokal ohne Cloud-Abhängigkeit

**Viel Erfolg! 🚀**

---

**Lemonade Version**: v9.1.3  
**VS Code AI Toolkit**: Latest  
**Konfiguration**: Option 1 (Qwen3-Coder @ 64k)
