$desktopPath = [System.IO.Path]::Combine([System.Environment]::GetFolderPath('Desktop'), 'Lemonade.lnk')
$appPath = 'C:\Users\tomwo\git\lemonade\src\app'
$iconPath = 'C:\Users\tomwo\git\lemonade\src\app\assets\icon_256.png'
$npmExe = 'C:\Users\tomwo\AppData\Roaming\npm\npm.cmd'

# Erstelle WScript.Shell Objekt
$shell = New-Object -ComObject WScript.Shell

# Erstelle Shortcut
$shortcut = $shell.CreateShortcut($desktopPath)
$shortcut.TargetPath = $npmExe
$shortcut.Arguments = 'start'
$shortcut.WorkingDirectory = $appPath
$shortcut.Description = 'Starte Lemonade Electron App'
$shortcut.IconLocation = $iconPath

try {
    $shortcut.Save()
    Write-Host "✅ Lemonade App Shortcut erstellt!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📍 Desktop Shortcut: Lemonade.lnk" -ForegroundColor Cyan
    Write-Host "🎯 Ziel: Lemonade Electron App (npm start)" -ForegroundColor Cyan
    Write-Host "🎨 Icon: icon_256.png" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "🚀 Verwendung:" -ForegroundColor Yellow
    Write-Host "   Doppelklick auf Lemonade.lnk >> App startet automatisch"
} catch {
    Write-Host "❌ Fehler beim Erstellen: $_" -ForegroundColor Red
}
