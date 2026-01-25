# Implementation Tasks: Multi-Server-Instanzen für parallele Modellausführung

**Feature**: 005-multi-llm-execution  
**Branch**: `005-multi-llm-execution`  
**Date**: 2026-01-09

## Summary

Deployment-Lösung zum Ausführen mehrerer Lemonade Server Instanzen auf verschiedenen Ports. **Keine Source-Code-Änderungen** - nur Orchestrierungs-Skripte und Konfiguration.

**Total Tasks**: 19  
**MVP Scope**: Phase 1 (Setup) + Phase 2 (Foundational) + Phase 3 (User Story 1)

## Implementation Strategy

**MVP First (Phases 1-3)**: Grundlegende Funktionalität - manuelle Server-Starts und Basis-Konfiguration  
**Incremental Delivery**: Dann Automatisierung (Phase 4), Port-Validierung (Phase 5), Monitoring (Phase 6)  
**Polish Last (Phase 7)**: Dokumentation, Docker-Support, Cross-Platform

## Task Breakdown

### Phase 1: Setup (Project Initialization)

- [X] T001 Erstelle Verzeichnisstruktur für Scripts und Konfiguration
  - Erstelle `scripts/multi-server/` für Orchestrierungs-Skripte
  - Erstelle `scripts/multi-server/config/` für Beispiel-Konfigurationen
  - Erstelle `scripts/multi-server/logs/` und `scripts/multi-server/pids/` Verzeichnisse

### Phase 2: Foundational (Blocking Prerequisites)

- [X] T002 [P] Erstelle JSON Schema für Server-Konfiguration
  - Definiere Schema in `scripts/multi-server/config/server-config.schema.json`
  - Felder: name, port, model, llamacpp_backend, ctx_size, log_level
  - Validierungsregeln für Pflichtfelder und Datentypen

- [X] T003 [P] Erstelle Beispiel-Konfigurationsdatei
  - Erstelle `scripts/multi-server/config/example-config.json`
  - 3 Server-Instanzen: Ports 8000, 8001, 8002
  - Verschiedene Modelle: Llama-3.2-3B, Qwen3-0.6B, Phi-4-mini
  - Dokumentiere alle verfügbaren Optionen als Kommentare

### Phase 3: User Story 1 - Mehrere Server-Instanzen parallel starten (P1)

**Story Goal**: Nutzer kann mehrere Server-Prozesse gleichzeitig auf verschiedenen Ports starten

**Independent Test**: 
- Starte 3 Server-Instanzen auf Ports 8000, 8001, 8002
- Sende parallele Health-Check-Anfragen an alle Ports
- Verifiziere, dass alle Server antworten

**Implementation Tasks**:

- [X] T004 Erstelle PowerShell Start-Skript (Kern-Funktionalität)
  - Erstelle `scripts/multi-server/start-multi-server.ps1`
  - Lade JSON-Konfiguration
  - Iteriere über Server-Definitionen
  - Starte jeden Server mit Start-Process im Hintergrund
  - Speichere PIDs in `pids/server-{port}.pid`
  - Leite Logs nach `logs/server-{port}.log` um

- [X] T005 [US1] Implementiere Port-Prüfung vor Start
  - In start-multi-server.ps1: Prüfe Ports mit Get-NetTCPConnection
  - Bei belegtem Port: Zeige Warnung und überspringe Server
  - Sammle alle Port-Konflikte und zeige Zusammenfassung

- [X] T006 [P] [US1] Erstelle Linux Bash Start-Skript
  - Erstelle `scripts/multi-server/start-multi-server.sh`
  - Portiere PowerShell-Logik zu Bash
  - Verwende `lsof` oder `netstat` für Port-Prüfung
  - Verwende `nohup` für Hintergrund-Prozesse
  - POSIX-kompatibel für Ubuntu/Debian

- [X] T007 [US1] Teste manuellen Start von 3 Server-Instanzen
  - Teste start-multi-server.ps1 auf Windows
  - Teste start-multi-server.sh auf Linux (falls möglich)
  - Verifiziere parallele Ausführung mit Health-Checks
  - Dokumentiere Probleme und Edge Cases

### Phase 4: User Story 2 - Server-Konfiguration per Skript (P2)

**Story Goal**: Automatisiertes Starten/Stoppen aller konfigurierten Server

**Independent Test**:
- Führe Start-Skript aus → alle Server starten
- Führe Stop-Skript aus → alle Server stoppen sauber
- Logs bestätigen korrekte Starts/Stops

**Implementation Tasks**:

- [X] T008 Erstelle PowerShell Stop-Skript
  - Erstelle `scripts/multi-server/stop-multi-server.ps1`
  - Lese alle PID-Dateien aus `pids/`
  - Stoppe Prozesse mit Stop-Process -Force
  - Lösche PID-Dateien nach erfolgreichem Stop
  - Behandle nicht existierende Prozesse gracefully

- [X] T009 [P] [US2] Erstelle Linux Bash Stop-Skript
  - Erstelle `scripts/multi-server/stop-multi-server.sh`
  - Portiere PowerShell Stop-Logik
  - Verwende `kill -TERM` für graceful shutdown
  - Fallback auf `kill -KILL` nach Timeout

- [X] T010 [US2] Implementiere Restart-Funktionalität
  - Erstelle `scripts/multi-server/restart-multi-server.ps1`
  - Rufe stop-multi-server.ps1 auf
  - Warte kurz (2-3 Sekunden)
  - Rufe start-multi-server.ps1 auf
  - Validiere erfolgreichen Restart

- [X] T011 [P] [US2] Erstelle Linux Restart-Skript
  - Erstelle `scripts/multi-server/restart-multi-server.sh`
  - Entsprechende Bash-Implementierung

### Phase 5: User Story 3 - Port-Kollisionen vermeiden (P2)

**Story Goal**: System erkennt und verhindert Port-Konflikte zuverlässig

**Independent Test**:
- Starte Server auf Port 8000
- Versuche zweiten Server auf Port 8000 zu starten
- Verifiziere klare Fehlermeldung und kein Start

**Implementation Tasks**:

- [X] T012 Erweitere Start-Skript um Validierung
  - In start-multi-server.ps1: Validiere Config vor Start
  - Prüfe auf doppelte Port-Definitionen in Config
  - Prüfe auf doppelte Modell-Namen
  - Zeige Validierungsfehler vor Start-Versuch

- [X] T013 [US3] Implementiere verbesserte Fehlerbehandlung
  - Catch und handle Start-Fehler pro Server
  - Logge Fehler in separates Error-Log
  - Fahre mit nächstem Server fort bei Fehler
  - Zeige Zusammenfassung: Erfolge vs. Fehler

### Phase 6: User Story 4 - Server-Status überwachen (P3)

**Story Goal**: Nutzer kann Status aller Server-Instanzen abfragen

**Independent Test**:
- Starte 3 Server
- Führe Status-Skript aus
- Verifiziere Anzeige aller Server mit Details (Port, Model, PID, Status)

**Implementation Tasks**:

- [X] T014 Erstelle PowerShell Status-Skript
  - Erstelle `scripts/multi-server/status-multi-server.ps1`
  - Lese Config und PID-Dateien
  - Prüfe Prozess-Status für jeden Server
  - Query Health-Endpoint für geladene Modelle
  - Formatierte Ausgabe mit Farben

- [X] T015 [P] [US4] Erstelle Linux Bash Status-Skript
  - Erstelle `scripts/multi-server/status-multi-server.sh`
  - Bash-Implementierung des Status-Checks
  - ANSI-Farben für formatierte Ausgabe

- [X] T016 [US4] Implementiere detaillierte Metriken-Anzeige
  - In status-multi-server.ps1: Zeige CPU/RAM-Nutzung pro Server
  - Zeige Uptime seit Start
  - Zeige letzte Request-Zeit aus Health-Endpoint
  - Optional: Anfragen pro Sekunde aus Logs

### Phase 7: Polish & Cross-Cutting Concerns

- [X] T017 [P] Erstelle README für Scripts
  - Erstelle `scripts/multi-server/README.md`
  - Dokumentiere alle Skripte und ihre Verwendung
  - Beispiele für typische Workflows
  - Troubleshooting-Sektion

- [X] T018 [P] Erstelle Docker Compose Konfiguration (Optional)
  - Erstelle `scripts/multi-server/docker-compose.yml`
  - Service-Definition pro Server-Instanz
  - Volume-Mappings für Model-Cache
  - Port-Mappings

- [X] T019 Integration in Lemonade Documentation
  - Aktualisiere docs/server/ mit Multi-Server-Anleitung
  - Verlinke neue Scripts aus Hauptdokumentation
  - Füge FAQ-Einträge hinzu für häufige Fragen

- [ ] T020 Add parser-based startup-script validation and CI smoke-test
  - Create `tests/verify_start_lemonade_syntax.ps1` to run `Parser]::ParseFile()` and fail on syntax errors
  - Add CI job (or Azure/gha check) that runs the PowerShell parse check on PRs affecting `scripts/**/*.ps1` or `docs/**/*.ps1`
  - **Acceptance**: `pwsh -NoProfile -File tests/verify_start_lemonade_syntax.ps1` returns exit code 0 on main branch; PRs that introduce parse errors fail the job

## Dependencies (Story Completion Order)

```
Phase 1 (Setup) → Phase 2 (Foundational)
                         ↓
Phase 3 (US1: Parallel Start) ← MVP Delivery Point
                         ↓
Phase 4 (US2: Automation) ← Can parallelize with Phase 5
                         ↓
Phase 5 (US3: Port Validation)
                         ↓
Phase 6 (US4: Monitoring)
                         ↓
Phase 7 (Polish)
```

**Key Dependencies**:
- T001 (Setup) must complete before all others
- T002, T003 (Config) can run in parallel after T001
- T004 (Core Start Script) blocks T005, T007, T008
- T006 (Linux Start) can run parallel to T004, T005
- T008-T011 (Stop/Restart) depend on T004
- T012-T013 (Validation) can integrate into T004 or run after
- T014-T016 (Monitoring) can start after T004 completes
- T017-T019 (Documentation) can run anytime after core scripts exist

## Parallel Execution Examples

**Per User Story**:

**US1 (Parallel Start)**:
- T006 (Linux Start) can develop while T004 (PowerShell Start) is being written
- T007 (Testing) waits for both T004 and T006

**US2 (Automation)**:
- T009 (Linux Stop) parallel to T008 (PowerShell Stop)
- T011 (Linux Restart) parallel to T010 (PowerShell Restart)

**US3 (Port Validation)**:
- T012 and T013 can be done sequentially on same script

**US4 (Monitoring)**:
- T015 (Linux Status) parallel to T014 (PowerShell Status)
- T016 (Metrics) extends T014 after completion

**Phase 7 (Polish)**:
- T017, T018, T019 all independent - can run fully parallel

## Validation Criteria

Each phase must meet these criteria before proceeding:

**Phase 3 (US1) - MVP Gate**:
- ✅ 3 Server-Instanzen starten erfolgreich
- ✅ Alle laufen auf korrekten Ports
- ✅ Health-Checks bestätigen alle Server online
- ✅ Parallele Inference-Requests funktionieren

**Phase 4 (US2)**:
- ✅ Stop-Skript beendet alle Server sauber
- ✅ Restart-Skript funktioniert ohne manuelle Eingriffe
- ✅ Keine Zombie-Prozesse nach Stop

**Phase 5 (US3)**:
- ✅ Port-Konflikte werden 100% erkannt
- ✅ Klare Fehlermeldungen bei Problemen
- ✅ Kein Server startet bei Port-Konflikt

**Phase 6 (US4)**:
- ✅ Status zeigt alle laufenden Server akkurat
- ✅ Geladene Modelle werden korrekt angezeigt
- ✅ PID und Port-Informationen stimmen

**Phase 7 (Polish)**:
- ✅ Documentation vollständig und klar
- ✅ Docker Compose funktioniert (wenn implementiert)
- ✅ Alle Scripts haben Help-Text

## Notes

- **Keine Code-Änderungen**: Alle Tasks sind reine Scripting/Config-Arbeiten
- **Cross-Platform**: PowerShell-Versionen haben Bash-Äquivalente
- **Constitution Compliant**: Developer Experience First (einfache Skripte), Cross-Platform Support
- **Incremental Delivery**: MVP nach Phase 3 lieferbar, Rest sind Verbesserungen
