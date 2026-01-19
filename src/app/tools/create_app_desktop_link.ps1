$desktopPath = [System.IO.Path]::Combine([System.Environment]::GetFolderPath('Desktop'), 'Lemonade.lnk')
$appPath = 'C:\Users\tomwo\git\lemonade\src\app'
$iconPath = 'C:\Users\tomwo\git\lemonade\src\app\assets\icon_256.png'
$npmExe = 'C:\Users\tomwo\AppData\Roaming\npm\npm.cmd'

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($desktopPath)
$shortcut.TargetPath = $npmExe
$shortcut.Arguments = 'start'
$shortcut.WorkingDirectory = $appPath
$shortcut.Description = 'Starte Lemonade Electron App'
$shortcut.IconLocation = $iconPath

$shortcut.Save()
Write-Host "OK - Shortcut erstellt" -ForegroundColor Green
