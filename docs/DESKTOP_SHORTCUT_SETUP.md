# Lemonade Quality Config Desktop Launcher - Erstellen

Dieses Skript erstellt automatisch einen Desktop-Shortcut für die Quality Config.

```powershell
# 1. Starten Sie PowerShell als Administrator
# 2. Führen Sie diesen Code aus:

$desktopPath = [Environment]::GetFolderPath("Desktop")
$shortcutPath = "$desktopPath\🍋 Lemonade Quality Config.lnk"
$targetScript = "C:\Users\tomwo\git\lemonade\tools\START_QUALITY_CONFIG.bat"

# Erstelle Windows-Verknüpfung
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $targetScript
$shortcut.WorkingDirectory = "C:\Users\tomwo\git\lemonade"
$shortcut.Description = "Startet Lemonade Server mit allen 4 Modellen (Option 1)"
$shortcut.IconLocation = "C:\Windows\System32\cmd.exe,0"  # Oder custom Icon
$shortcut.Save()

Write-Host "✓ Desktop-Shortcut erstellt: $shortcutPath"
```

## Alternative: Schneller PowerShell-Launcher

Erstelle eine `.ps1` Datei stattdessen:

```powershell
# Speichere als: C:\Users\tomwo\Desktop\Start-LemonadeQuality.ps1

& "C:\Users\tomwo\git\lemonade\tools\START_QUALITY_CONFIG.bat"
```

Dann als Verknüpfung:
```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\tomwo\Desktop\Start-LemonadeQuality.ps1"
```

## Manuelle Desktop-Verknüpfung (ohne Script)

1. **Rechtsklick auf Desktop** → **Neuer Ordner** → Nennen Sie ihn nicht
2. **Rechtsklick auf `START_QUALITY_CONFIG.bat`** → **Verknüpfung erstellen**
3. **Verschiebe** die Verknüpfung auf den Desktop
4. **Rechtsklick** → **Eigenschaften** → **Icon ändern...**

## Schnelle Verwendung

Nach Setup einfach **Doppelklick** auf den Desktop-Shortcut:

```
🍋 Lemonade Quality Config
```

Und alle 4 Modelle werden geladen! 🚀
