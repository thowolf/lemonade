# Public → „privater Fork" (Mirror-Workflow)

Ein „privater Fork" von einem **öffentlichen** Repo geht über einen Mirror-Workflow, nicht über den Fork-Button. So kannst du z.B. Lemonade privat spiegeln und trotzdem Updates ziehen.

## 1. Öffentliches Repo lokal clonen

```bash
git clone https://github.com/lemonade-sdk/lemonade.git
cd lemonade
```

Das ist dein lokaler Mirror des öffentlichen Repos.[^1][^2]

## 2. Privates Repo auf GitHub anlegen

- Auf GitHub: **New Repository**.
- Name z.B. `lemonade-private`.
- Sichtbarkeit: **Private**.
- Keine Dateien initialisieren (kein README, keine License, kein .gitignore).[^2][^1]

## 3. Remote auf dein privates Repo umbiegen

Im geklonten Projekt:

```bash
git remote rename origin upstream    # Original-Repo heisst jetzt 'upstream'
git remote add origin git@github.com:DEINUSER/lemonade-private.git
```

- `upstream` zeigt auf das öffentliche Original.
- `origin` zeigt auf dein privates Repo (SSH- oder HTTPS-URL nehmen).[^2]

## 4. Code in dein privates Repo pushen

```bash
git push -u origin main
```

Jetzt liegt der komplette Stand des öffentlichen Repos in deinem **privaten** Repo; nur du (und ggf. deine Org) sehen es.[^1][^2]

## 5. Regelmässig Updates vom Original holen

Wenn das Public-Repo neue Commits bekommt:

```bash
# Aktuellen Stand vom Original holen
git fetch upstream

# In deinen main integrieren (rebase oder merge – rebase hält die History sauber)
git checkout main
git rebase upstream/main   # oder: git merge upstream/main

# Änderungen in dein privates Repo hochladen
git push --force-with-lease origin main   # bei rebase
```

Damit bleibt dein privater Mirror synchron, ohne dass deine Sichtbarkeit verloren geht.[^3][^4]

## 6. Eigene Arbeit in Feature-Branches

Für deine Anpassungen (z.B. MoE-Experimente):

```bash
git checkout -b feature/moe-tests
# Änderungen machen, committen
git add .
git commit -m "Add MoE routing experiment"
git push -u origin feature/moe-tests
```

- Deine Branches liegen **nur** im privaten Repo.
- `upstream` bleibt read-only Quelle für Updates.

## 7. Optional: Änderungen zurück zum Public-Repo

Wenn du etwas zurückgeben willst:

- Entweder ein separater **öffentlicher Fork** + PR.
- Oder Patch/Branch aus dem privaten Repo exportieren und im öffentlichen Fork wiederverwenden.[^5]

Damit hast du funktional einen „privaten Fork":

> öffentliches Projekt → lokaler Clone → privates Repo als origin → Original als upstream → sauberer Update- und Feature-Branch-Workflow.

---

**Hinweis zur Upstream-Integrität**: Überschreibe keine Dateien, die aus dem Original-Repo stammen (z. B. `docs/contribute.md`). Bewahre private Anpassungen in separaten Dateien oder klar markierten Bereichen, damit Upstream-Updates sich sauber mergen lassen.

[^1]: Mirror-Workflow avoids fork visibility issues.
[^2]: Use SSH for convenient push access; HTTPS works as well.
[^3]: Prefer `rebase` to keep history clean; `force-with-lease` is safer than `--force`.
[^4]: Keep feature branches private and short-lived if they are sensitive.
[^5]: When contributing back, prefer small, focused patches that are easy to review.
