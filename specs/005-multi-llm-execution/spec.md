# Feature Specification: Multi-Server-Instanzen für parallele Modellausführung

**Feature Branch**: `005-multi-llm-execution`  
**Created**: 2026-01-09  
**Status**: Draft  
**Input**: User description: "lemonade server muss mehrere llm gleichzeitig ausführen können - mehrere Server-Instanzen mit verschiedenen Ports lokal ausführen"

## Klarstellung

**Anforderung**: Mehrere Lemonade Server Prozesse gleichzeitig lokal ausführen, wobei jeder Prozess:
- Auf einem eigenen Port läuft (z.B. 8000, 8001, 8002)
- Ein spezifisches Modell lädt
- Unabhängig von anderen Instanzen arbeitet

**KEINE Code-Änderungen**: Dies ist eine Deployment-/Orchestrierungsaufgabe, keine Source-Code-Entwicklung.

## Clarifications

### Session 2026-01-09

- Q: Sollen mehrere Modelle in einem Server oder mehrere Server-Instanzen? → A: Mehrere unabhängige Server-Instanzen auf verschiedenen Ports
- Q: Code-Änderungen oder Deployment-Konfiguration? → A: Nur Deployment - keine Code-Änderungen

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Mehrere Server-Instanzen parallel starten (Priority: P1)

Ein Entwickler möchte mehrere LLM-Modelle gleichzeitig lokal zur Verfügung haben, ohne zwischen ihnen wechseln zu müssen. Jedes Modell läuft in einer eigenen Server-Instanz auf einem eigenen Port, sodass Anwendungen direkt mit dem gewünschten Modell kommunizieren können.

**Why this priority**: Dies ist die Kernfunktionalität - mehrere Server-Prozesse gleichzeitig zu starten und zu verwalten. Ohne diese Fähigkeit müsste der Nutzer manuell mehrere Terminals öffnen und jeden Server einzeln starten.

**Independent Test**: Vollständig testbar durch Starten von 2-3 Server-Instanzen mit verschiedenen Ports und Modellen, dann parallele Anfragen an verschiedene Ports senden. Erfolg wird durch erfolgreiche Antworten von allen Servern verifiziert.

**Acceptance Scenarios**:

1. **Given** kein Server läuft, **When** Nutzer startet 3 Server-Instanzen mit Ports 8000, 8001, 8002, **Then** alle 3 Server laufen parallel und sind erreichbar
2. **Given** Server-Instanz auf Port 8000 läuft mit Modell A, **When** Nutzer startet zweite Instanz auf Port 8001 mit Modell B, **Then** beide Server laufen unabhängig ohne Konflikt
3. **Given** mehrere Server-Instanzen laufen, **When** Nutzer sendet gleichzeitige Anfragen an verschiedene Ports, **Then** jeder Server verarbeitet seine Anfragen unabhängig
4. **Given** 3 Server-Instanzen laufen, **When** Nutzer stoppt eine Instanz, **Then** andere Instanzen laufen weiter ohne Unterbrechung

---

### User Story 2 - Server-Konfiguration per Skript (Priority: P2)

Nutzer benötigen ein einfaches Skript oder Tool, um mehrere Server-Instanzen mit vordefinierten Konfigurationen zu starten, anstatt jeden Server manuell in separaten Terminals zu starten.

**Why this priority**: Verbessert die Benutzererfahrung erheblich. Ohne Automatisierung ist die Verwaltung mehrerer Server fehleranfällig und zeitaufwendig.

**Independent Test**: Kann durch Ausführen eines Konfigurations-Skripts getestet werden, das automatisch mehrere Server startet und verifiziert, dass alle korrekt laufen.

**Acceptance Scenarios**:

1. **Given** Konfigurationsdatei mit 3 Server-Definitionen (Port, Modell), **When** Nutzer führt Start-Skript aus, **Then** alle 3 Server starten automatisch
2. **Given** mehrere Server laufen via Skript, **When** Nutzer führt Stop-Skript aus, **Then** alle Server werden sauber beendet
3. **Given** Konfigurationsdatei, **When** Nutzer ändert Portnummer, **Then** Server startet auf neuem Port beim nächsten Start

---

### User Story 3 - Port-Kollisionen vermeiden (Priority: P2)

System muss Port-Konflikte erkennen und verhindern, sodass nicht versehentlich zwei Server auf demselben Port starten.

**Why this priority**: Verhindert häufige Fehlerquelle. Wichtig für Zuverlässigkeit, aber nicht kritisch für Grundfunktionalität.

**Independent Test**: Testbar durch Versuch, zwei Server auf demselben Port zu starten - zweiter Start sollte fehlschlagen mit klarer Fehlermeldung.

**Acceptance Scenarios**:

1. **Given** Server läuft auf Port 8000, **When** zweiter Server versucht auf Port 8000 zu starten, **Then** Fehler wird gemeldet und zweiter Server startet nicht
2. **Given** Konfiguration mit doppeltem Port, **When** Start-Skript ausgeführt wird, **Then** Fehler wird vor dem Start erkannt und gemeldet
3. **Given** Port ist bereits von anderem Prozess belegt, **When** Server versucht zu starten, **Then** klare Fehlermeldung zeigt Port-Konflikt

---

### User Story 4 - Server-Status überwachen (Priority: P3)

Nutzer möchten sehen, welche Server-Instanzen laufen, welche Modelle geladen sind und auf welchen Ports sie erreichbar sind.

**Why this priority**: Nützlich für Debugging und Übersicht, aber nicht essentiell für Basisfunktionalität.

**Independent Test**: Testbar durch Status-Abfrage nach Start mehrerer Server - sollte alle laufenden Instanzen mit Details auflisten.

**Acceptance Scenarios**:

1. **Given** 3 Server-Instanzen laufen, **When** Nutzer führt Status-Befehl aus, **Then** Liste zeigt alle 3 Server mit Ports und Modellen
2. **Given** Server-Instanz läuft, **When** Modell geladen wird, **Then** Status zeigt geladenes Modell
3. **Given** Server wurde gestoppt, **When** Status abgefragt wird, **Then** Server erscheint nicht mehr in Liste

---

### Edge Cases

- Was passiert, wenn ein Server-Prozess abstürzt während andere weiterlaufen?
- Wie wird mit unzureichendem Speicher umgegangen wenn mehrere große Modelle gleichzeitig laufen?
- Was passiert bei System-Neustart - starten Server automatisch neu?
- Wie werden Logs von mehreren Server-Instanzen getrennt gehalten?
- Was passiert wenn Port in Konfiguration bereits vom OS reserviert ist?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUSS mehrere Lemonade Server Prozesse gleichzeitig auf demselben Rechner ausführen können
- **FR-002**: Jeder Server-Prozess MUSS auf einem eindeutigen Port konfigurierbar sein
- **FR-003**: Jeder Server-Prozess MUSS ein spezifisches Modell beim Start laden können
- **FR-004**: System MUSS Port-Konflikte erkennen und verhindern (zweier Server auf gleichem Port)
- **FR-005**: Server-Instanzen MÜSSEN unabhängig voneinander starten und stoppen können
- **FR-006**: Nutzer MUSS Konfigurationsdatei oder Skript verwenden können, um mehrere Server-Instanzen zu definieren
- **FR-007**: System MUSS alle laufenden Server-Instanzen mit Status anzeigen können (Port, Modell, PID)
- **FR-008**: Logs von verschiedenen Server-Instanzen MÜSSEN voneinander getrennt sein
- **FR-009**: Beim Stoppen aller Instanzen MÜSSEN alle Server-Prozesse sauber beendet werden
- **FR-010**: System MUSS klare Fehlermeldungen bei Port-Konflikten oder Startfehlern liefern
- **FR-011**: Jede Server-Instanz MUSS ihre eigene Backend-Konfiguration haben können (llamacpp backend, ctx-size, etc.)
- **FR-012**: System MUSS mit unzureichendem Speicher umgehen können (graceful degradation)
- **FR-013**: Startup- und Betriebs-Skripte (PowerShell/Bash) MÜSSEN syntaktisch gültig sein und eine parser-basierte Smoke-Test-Abdeckung haben (z. B. `pwsh` Parse-Check in CI).

### Key Entities

- **Server-Instanz**: Ein laufender Lemonade Server Prozess mit spezifischem Port, Modell und Konfiguration
- **Konfigurationsdatei**: Definiert alle Server-Instanzen (Port, Modell, Einstellungen)
- **Orchestrator/Manager**: Skript oder Tool zum Starten/Stoppen/Verwalten mehrerer Server-Instanzen

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Nutzer können mindestens 3 Server-Instanzen gleichzeitig auf verschiedenen Ports starten
- **SC-002**: Jede Server-Instanz lädt ihr zugewiesenes Modell erfolgreich
- **SC-003**: Parallele Anfragen an verschiedene Ports werden ohne Interferenz verarbeitet
- **SC-004**: Port-Konflikte werden zu 100% erkannt bevor Server startet
- **SC-005**: Server-Instanzen können in unter 5 Sekunden gestartet werden (nach Modell-Ladezeit)
- **SC-006**: System-Ressourcennutzung (CPU, RAM) ist bei mehreren Instanzen vorhersehbar
- **SC-007**: PowerShell/Bash startup-scripts parsen fehlerfrei mit parser-basiertem Smoke-Test (`pwsh` ParseFile check) und sind in CI abgesichert
