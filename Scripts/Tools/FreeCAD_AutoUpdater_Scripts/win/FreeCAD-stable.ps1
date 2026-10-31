#Requires -Version 5.1
# FreeCAD Stable (Windows) - descarga, instala, actualiza y ejecuta el bundle portable.
#
# Autocontenido: el bundle, el log y las marcas viven junto a este script.
# Equivalente Windows de linux/FreeCAD-stable.sh (misma CLI y semantica).
# Sin dependencias: HttpClient, Get-FileHash, Compress-Archive y toast WinRT.
# La extraccion .7z usa tar.exe, 7z instalado o 7zr.exe portable (automatico).
#
# Licencia: MIT (ver ../LICENSE).
# ---------------------------------------------------------------------------
# Rutas y constantes
# ---------------------------------------------------------------------------
$Script:SCRIPT = $PSCommandPath
$Script:Here = Split-Path -Parent $PSCommandPath
switch ($env:PROCESSOR_ARCHITECTURE) {
    'AMD64' { $Script:ARCH = 'x86_64' }
    # Sin rama ARM64: no hay build Windows-ARM64 de FreeCAD; cae al default
    # ('') y el guard de Invoke-Main lo rechaza con "arquitectura no soportada".
    default { $Script:ARCH = '' }
}
# -Filter solo entiende '*' y '?' (los corchetes serian literales en NTFS,
# pero el lab con pwsh en Linux los interpreta como clase: nunca meter '[]'
# en -Filter). El patron grueso va en -Filter; el fino (numerico, para no
# capturar la carpeta del weekly si ambos canales conviven) en DIR_REGEX.
$Script:DIR_PATTERN = 'FreeCAD_*-Windows-*'
$Script:DIR_REGEX = '^FreeCAD_[0-9]'
$Script:API = 'https://api.github.com/repos/FreeCAD/FreeCAD/releases/latest'
$Script:FEED = 'https://github.com/FreeCAD/FreeCAD/releases.atom'
$Script:DL_BASE = 'https://github.com/FreeCAD/FreeCAD/releases/download'
$Script:SEVENZR_URL = 'https://www.7-zip.org/a/7zr.exe'
$Script:UA = 'FreeCAD-Stable-Updater'
# PowerShell 5.1 no trae cargado System.Net.Http (lo necesita Save-UrlOnce);
# en PowerShell 7+ esta linea no hace nada.
try { Add-Type -AssemblyName System.Net.Http } catch { }
$Script:LOG = Join-Path $Script:Here '.freecad-stable.log'
$Script:LOCK = Join-Path $Script:Here '.freecad-stable.lock'
$Script:VERSION = '0.8.6'
$Script:SUITE = 'FreeCAD AutoUpdater Scripts'
$Script:NOSHORTCUT = Join-Path $Script:Here '.no-stable-shortcut'
$Script:NOASSOC = Join-Path $Script:Here '.no-stable-assoc'
$Script:NODESKTOP = Join-Path $Script:Here '.no-stable-desktop'
$Script:SEVENZR = Join-Path $Script:Here '.7zr.exe'
$Script:BACKUP_DIR = Join-Path $Script:Here '.cfg-backup-stable'
$Script:LNK = $null
if ($env:APPDATA) {
    $Script:LNK = Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\FreeCAD Stable.lnk'
}
$Script:DESK_LNK = $null
try {
    $d = [Environment]::GetFolderPath('Desktop')
    if ($d) { $Script:DESK_LNK = Join-Path $d 'FreeCAD Stable.lnk' }
} catch { }
$Script:PROG_ID = 'FreeCAD.Stable'
# ---------------------------------------------------------------------------
# Idioma (es/en automatico)
# ---------------------------------------------------------------------------
$Script:LANG_CODE = 'en'
try {
    if ((Get-Culture).Name -like 'es*') { $Script:LANG_CODE = 'es' }
} catch { }
function t($key) {
    switch ("$($Script:LANG_CODE):$key") {
        'es:title'             { 'FreeCAD Stable' }
        'en:title'             { 'FreeCAD Stable' }
        'es:name'              { 'FreeCAD Stable' }
        'en:name'              { 'FreeCAD Stable' }
        'es:generic'           { 'Version estable' }
        'en:generic'           { 'Stable release' }
        'es:comment'           { 'Modelador 3D parametrico (portable estable)' }
        'en:comment'           { 'Parametric 3D modeler (stable portable)' }
        'es:checking'          { 'Comprobando actualizaciones...' }
        'en:checking'          { 'Checking for updates...' }
        'es:no_local'          { 'Sin version local: descargando la ultima' }
        'en:no_local'          { 'No local version: downloading the latest' }
        'es:downloading'       { 'Descargando' }
        'en:downloading'       { 'Downloading' }
        'es:verifying'         { 'Verificando integridad...' }
        'en:verifying'         { 'Verifying integrity...' }
        'es:updated'           { 'Actualizado a' }
        'en:updated'           { 'Updated to' }
        'es:ready'             { 'Listo' }
        'en:ready'             { 'Done' }
        'es:err'               { 'Error' }
        'en:err'               { 'Error' }
        'es:err_arch'          { 'Arquitectura no soportada:' }
        'en:err_arch'          { 'Unsupported architecture:' }
        'es:err_download'      { 'No se pudo descargar; se usara la version actual.' }
        'en:err_download'      { 'Download failed; the current version will be used.' }
        'es:err_checksum'      { 'Checksum incorrecto; no se actualiza.' }
        'en:err_checksum'      { 'Checksum mismatch; not updating.' }
        'es:err_no_local'      { 'No hay version local ni se pudo descargar.' }
        'en:err_no_local'      { 'No local bundle and download failed.' }
        'es:err_check'         { 'No se pudo comprobar la ultima version (sin red?).' }
        'en:err_check'         { 'Could not check the latest version (offline?).' }
        'es:err_nowrite'       { 'La carpeta del script no tiene permiso de escritura:' }
        'en:err_nowrite'       { 'The script folder is not writable:' }
        'es:err_extract'       { 'No se pudo extraer el paquete descargado.' }
        'en:err_extract'       { 'Could not extract the downloaded package.' }
        'es:ask_shortcut'      { 'Crear un acceso en el menu de inicio para FreeCAD Stable?' }
        'en:ask_shortcut'      { 'Create a start menu shortcut for FreeCAD Stable?' }
        'es:shortcut_created'  { 'Acceso creado en el menu de inicio.' }
        'en:shortcut_created'  { 'Start menu shortcut created.' }
        'es:shortcut_removed'  { 'Acceso eliminado del menu de inicio.' }
        'en:shortcut_removed'  { 'Start menu shortcut removed.' }
        'es:ask_desktop'       { '¿Crear además un acceso directo en el Escritorio?' }
        'en:ask_desktop'       { 'Also create a Desktop shortcut?' }
        'es:desktop_created'   { 'Acceso directo creado en el Escritorio.' }
        'en:desktop_created'   { 'Desktop shortcut created.' }
        'es:desktop_removed'   { 'Acceso directo eliminado del Escritorio.' }
        'en:desktop_removed'   { 'Desktop shortcut removed.' }
        'es:ask_assoc'  { '¿Asociar los archivos .FCStd con FreeCAD Stable para abrirlos con doble clic?' }
        'en:ask_assoc'  { 'Associate .FCStd files with FreeCAD Stable to open them on double click?' }
        'es:assoc_set'  { 'Archivos .FCStd asociados con FreeCAD Stable.' }
        'en:assoc_set'  { '.FCStd files associated with FreeCAD Stable.' }
        'es:assoc_removed'{ 'Asociación de .FCStd eliminada.' }
        'en:assoc_removed'{ '.FCStd association removed.' }
        'es:uninstalled'       { 'FreeCAD Stable desinstalado.' }
        'en:uninstalled'       { 'FreeCAD Stable uninstalled.' }
        'es:confirm_uninstall' { 'Desinstalar FreeCAD Stable (borrar bundle, acceso, asociación y marcas)?' }
        'en:confirm_uninstall' { 'Uninstall FreeCAD Stable (remove bundle, shortcut, association and marks)?' }
        'es:check_ok'          { 'Estas en la ultima version:' }
        'en:check_ok'          { 'You are on the latest version:' }
        'es:check_new'         { 'Nueva version disponible:' }
        'en:check_new'         { 'New version available:' }
        default                { $key }
    }
}
# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
function Write-Log($msg) {
    try {
        $ts = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
        Add-Content -Path $Script:LOG -Value "$ts $msg" -ErrorAction Stop
        if ($Script:VERBOSE) { [System.Console]::Error.WriteLine("$msg") }
        $n = (Get-Content -Path $Script:LOG -ErrorAction SilentlyContinue | Measure-Object -Line).Lines
        if ($n -gt 500) {
            $tmp = "$($Script:LOG).tmp"
            Get-Content -Path $Script:LOG -Tail 300 -ErrorAction Stop | Set-Content -Path $tmp -ErrorAction Stop
            Move-Item -Path $tmp -Destination $Script:LOG -Force -ErrorAction Stop
        }
    } catch { }
}
function Send-Notify($text1, $text2) {
    try {
        [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
        $tpl = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent(
            [Windows.UI.Notifications.ToastTemplateType]::ToastText02)
        $texts = $tpl.GetElementsByTagName('text')
        $texts.Item(0).AppendChild($tpl.CreateTextNode([string]$text1)) | Out-Null
        if ($text2) { $texts.Item(1).AppendChild($tpl.CreateTextNode([string]$text2)) | Out-Null }
        $toast = [Windows.UI.Notifications.ToastNotification]::new($tpl)
        [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier((t title)).Show($toast)
    } catch { }
}
function Pad-Version($s) {
    return [regex]::Replace($s, '\d+', { $args[0].Value.PadLeft(10, '0') })
}
# Carpetas de bundle del canal estable (el regex numerico descarta la carpeta
# del weekly y el .old se conserva a proposito: lo limpia Install-FromArchive).
function Get-BundleDirs {
    @(Get-ChildItem -Path $Script:Here -Directory -Filter $Script:DIR_PATTERN `
        -ErrorAction SilentlyContinue | Where-Object { $_.Name -match $Script:DIR_REGEX })
}
# Devuelve @{ Dir, Exe, Tag, Name } del bundle local mas reciente, o $null.
function Get-LatestLocal() {
    $dirs = @(Get-BundleDirs | Sort-Object { Pad-Version $_.Name })
    if ($dirs.Count -eq 0) { return $null }
    $d = $dirs[-1]
    $exe = Join-Path $d.FullName 'FreeCAD.exe'
    if (-not (Test-Path -Path $exe)) {
        $found = Get-ChildItem -Path $d.FullName -Recurse -Filter 'FreeCAD.exe' `
            -ErrorAction SilentlyContinue | Select-Object -First 1
        if (-not $found) { return $null }
        $exe = $found.FullName
    }
    $tag = $null
    if ($d.Name -match '^FreeCAD_(.+)-Windows-') { $tag = $Matches[1] }
    return [pscustomobject]@{ Dir = $d.FullName; Exe = $exe; Tag = $tag; Name = $d.Name }
}
# OJO: no leer texto con Invoke-WebRequest en memoria. En PowerShell 5.1
# anuncia 'Accept-Encoding: gzip', el CDN comprime el sidecar y .Content
# devuelve los bytes gzip sin descomprimir ("52"/"57"): toda verificacion
# falla aunque la descarga sea perfecta. HttpClient no anuncia compresion.
function Get-UrlText($url, $timeoutSec = 20) {
    try {
        $h = New-Object System.Net.Http.HttpClient
        $h.Timeout = [TimeSpan]::FromSeconds($timeoutSec)
        $h.DefaultRequestHeaders.Add('User-Agent', $Script:UA)
        try {
            return $h.GetStringAsync($url).GetAwaiter().GetResult()
        } finally { $h.Dispose() }
    } catch { return $null }
}
function Test-UrlExists($url) {
    try {
        Invoke-WebRequest -Uri $url -Method Head -UseBasicParsing -UserAgent $Script:UA `
            -TimeoutSec 15 -ErrorAction Stop | Out-Null
        return $true
    } catch { return $false }
}
function Get-UrlFile($url, $dest, $timeoutSec = 60) {
    try {
        Invoke-WebRequest -Uri $url -UseBasicParsing -UserAgent $Script:UA -OutFile $dest `
            -TimeoutSec $timeoutSec -ErrorAction Stop
        return (Test-Path -Path $dest)
    } catch { return $false }
}
# Imprime @{ Tag, Url } de la ultima release estable (API; respaldo: feed Atom).
function Get-ReleaseStable() {
    try {
        $j = Invoke-RestMethod -Uri $Script:API -UserAgent $Script:UA -TimeoutSec 20 -ErrorAction Stop
        $tag = [string]$j.tag_name
        if ($tag -match '^[0-9.]+$') {
            $pat = '^FreeCAD_[0-9].*-Windows-' + $Script:ARCH + '.*\.7z$'
            $a = @($j.assets | Where-Object { $_.name -match $pat }) | Select-Object -First 1
            if ($a) { return [pscustomobject]@{ Tag = $tag; Url = [string]$a.browser_download_url } }
        }
    } catch { }
    $feed = Get-UrlText $Script:FEED 15
    if (-not $feed) { return $null }
    $tags = [regex]::Matches($feed, 'releases/tag/([^"<]+)') | ForEach-Object { $_.Groups[1].Value } `
        | Select-Object -Unique
    foreach ($tg in $tags) {
        if ($tg -notmatch '^[0-9.]+$') { continue }
        foreach ($cand in @("FreeCAD_${tg}-Windows-$($Script:ARCH)-py311.7z",
                            "FreeCAD_${tg}-Windows-$($Script:ARCH).7z")) {
            $u = "$($Script:DL_BASE)/$tg/$cand"
            if (Test-UrlExists $u) { return [pscustomobject]@{ Tag = $tg; Url = $u } }
        }
    }
    return $null
}
function Ask-YesNo($text) {
    try {
        Add-Type -AssemblyName System.Windows.Forms -ErrorAction Stop
        $r = [System.Windows.Forms.MessageBox]::Show($text, (t title), 'YesNo', 'Question')
        return ($r -eq 'Yes')
    } catch { return $false }
}
# ---------------------------------------------------------------------------
# Bloqueo (un solo update a la vez; espejo del flock)
# ---------------------------------------------------------------------------
$Script:LockStream = $null
function Lock-Update() {
    try {
        $Script:LockStream = [System.IO.File]::Open($Script:LOCK,
            [System.IO.FileMode]::OpenOrCreate,
            [System.IO.FileAccess]::ReadWrite,
            [System.IO.FileShare]::None)
        return $true
    } catch {
        Write-Log 'another update in progress'
        return $false
    }
}
function Unlock-Update() {
    if ($Script:LockStream) {
        try { $Script:LockStream.Close() } catch { }
        $Script:LockStream = $null
    }
}
# ---------------------------------------------------------------------------
# Descarga con progreso (espejo del dialogo de progreso)
# ---------------------------------------------------------------------------
function Save-UrlWithProgress($url, $dest, $statusPrefix) {
    $Script:LAST_DL_ERROR = $null
    for ($attempt = 1; $attempt -le 3; $attempt++) {
        if (Save-UrlOnce $url $dest "$statusPrefix (intento $attempt/3)") {
            return $true
        }
        Write-Log "download attempt $attempt/3 failed ($($Script:LAST_DL_ERROR))"
        Remove-Item -Path $dest -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds (2 * $attempt)
    }
    return $false
}
# Una descarga; $true solo si el fichero existe y (con tamaño conocido) cuadra.
function Save-UrlOnce($url, $dest, $statusPrefix) {
    $client = $null
    try {
        $client = New-Object System.Net.Http.HttpClient
        $client.Timeout = [TimeSpan]::FromMinutes(30)
        $resp = $client.GetAsync($url,
            [System.Net.Http.HttpCompletionOption]::ResponseHeadersRead).Result
        [void]$resp.EnsureSuccessStatusCode()
        $total = $resp.Content.Headers.ContentLength
        if (-not $total) { $total = 0 }
        $stream = $resp.Content.ReadAsStreamAsync().Result
        $file = [System.IO.File]::OpenWrite($dest)
        try {
            $buf = New-Object byte[] 81920
            $read = [long]0
            $stalls = 0
            $lastPct = -1
            $lastMb = -1
            do {
                $n = $stream.Read($buf, 0, $buf.Length)
                if ($n -gt 0) {
                    $file.Write($buf, 0, $n)
                    $read += $n
                    $stalls = 0
                } else {
                    # Lectura 0 prematura (la red a veces entrega el cuerpo
                    # tarde): esperar y reintentar, no darlo por EOF.
                    $stalls++
                    Start-Sleep -Milliseconds 200
                }
                if ($total -and $total -gt 0) {
                    $pct = [int](100 * $read / $total)
                    if ($pct -gt 100) { $pct = 100 }
                    $st = '{0} ({1}/{2} MiB)' -f $statusPrefix, [int]($read / 1MB), [int]($total / 1MB)
                } else {
                    $pct = 0
                    $st = '{0} ({1} MiB)' -f $statusPrefix, [int]($read / 1MB)
                }
                $mb = [int]($read / 1MB)
                if (($pct -ne $lastPct) -or ($mb -ne $lastMb)) {
                    $lastPct = $pct
                    $lastMb = $mb
                    Write-Progress -Activity (t title) -Status $st -PercentComplete $pct -Id 1
                }
            } while (($stalls -le 100) -and (($total -gt 0 -and $read -lt $total) -or ($total -le 0 -and ($n -gt 0 -or $stalls -le 100))))
        } finally {
            $file.Close()
            $stream.Close()
        }
        Write-Progress -Activity (t title) -Id 1 -Completed
        # Se verifica con los bytes leidos/escritos ($read), no re-preguntando
        # el tamaño al sistema: es la cuenta exacta de lo transferido.
        if ($total -and ($total -gt 0)) {
            if ($read -ne $total) {
                $Script:LAST_DL_ERROR = "leidos $read != $total"
                return $false
            }
        } elseif ($read -le 0) {
            $Script:LAST_DL_ERROR = 'descarga vacia'
            return $false
        }
        return $true
    } catch {
        $Script:LAST_DL_ERROR = $_.Exception.Message
        Write-Progress -Activity (t title) -Id 1 -Completed
        return $false
    } finally {
        if ($client) { $client.Dispose() }
    }
}
# ---------------------------------------------------------------------------
# Extraccion .7z (cascada: tar.exe -> 7z instalado -> 7zr.exe portable)
# ---------------------------------------------------------------------------
function Expand-SevenZip($archive, $destDir) {
    $tar = Get-Command tar.exe -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($tar) {
        & $tar.Source -xf $archive -C $destDir 2>$null
        if ($LASTEXITCODE -eq 0) { return $true }
    }
    $seven = Get-Command 7z.exe, 7za.exe, 7zr.exe -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($seven) {
        & $seven.Source x $archive "-o$destDir" -y | Out-Null
        if ($LASTEXITCODE -eq 0) { return $true }
    }
    if (-not (Test-Path -Path $Script:SEVENZR)) {
        if (-not (Get-UrlFile $Script:SEVENZR_URL $Script:SEVENZR 120)) { return $false }
    }
    & $Script:SEVENZR x $archive "-o$destDir" -y | Out-Null
    return ($LASTEXITCODE -eq 0)
}
# Extrae el .7z y deja una sola version instalada. Devuelve la carpeta o $null.
function Install-FromArchive($archive, $asset) {
    $tmp = Join-Path $Script:Here ('.' + $asset + '.extract')
    Remove-Item -Path $tmp -Recurse -Force -ErrorAction SilentlyContinue
    try { New-Item -ItemType Directory -Path $tmp -ErrorAction Stop | Out-Null } catch { return $null }
    if (-not (Expand-SevenZip $archive $tmp)) {
        Remove-Item -Path $tmp -Recurse -Force -ErrorAction SilentlyContinue
        return $null
    }
    $tops = @(Get-ChildItem -Path $tmp -ErrorAction SilentlyContinue)
    if ($tops.Count -eq 1 -and $tops[0].PSIsContainer) {
        $vroot = $tops[0].FullName
        $dest = Join-Path $Script:Here $tops[0].Name
    } else {
        $vroot = $tmp
        $base = $asset -replace '\.7z$', ''
        $dest = Join-Path $Script:Here $base
    }
    # Instalacion (casi) atomica: la version nueva se coloca ANTES de borrar
    # las viejas. Si el move falla, se restaura la anterior y no te quedas
    # sin ninguna.
    $stagedOld = $null
    if ((Test-Path -Path $dest) -and ($dest -ne $vroot)) {
        $stagedOld = "$dest.old"
        Remove-Item -Path $stagedOld -Recurse -Force -ErrorAction SilentlyContinue
        try { Move-Item -Path $dest -Destination $stagedOld -ErrorAction Stop } catch { return $null }
    }
    try { Move-Item -Path $vroot -Destination $dest -Force -ErrorAction Stop } catch {
        if ($stagedOld) {
            Move-Item -Path $stagedOld -Destination $dest -ErrorAction SilentlyContinue
        }
        return $null
    }
    if ($vroot -ne $tmp) {
        Remove-Item -Path $tmp -Recurse -Force -ErrorAction SilentlyContinue
    }
    # Solo ahora, con la nueva en su sitio, se borran las demas (incluido el
    # .old apartado, que tambien encaja en DIR_PATTERN).
    $destLeaf = Split-Path -Leaf $dest
    Get-BundleDirs |
        Where-Object { $_.Name -ne $destLeaf } |
        Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    $exe = Join-Path $dest 'FreeCAD.exe'
    if (-not (Test-Path -Path $exe)) {
        $found = Get-ChildItem -Path $dest -Recurse -Filter 'FreeCAD.exe' `
            -ErrorAction SilentlyContinue | Select-Object -First 1
        if (-not $found) { return $null }
    }
    return $dest
}
# ---------------------------------------------------------------------------
# Acceso al menu de inicio (al actualizador) + asociacion .FCStd (HKCU, sin admin)
# ---------------------------------------------------------------------------
function Write-Shortcut($path) {
    if (-not $path) { return }
    try {
        # El acceso apunta al script actualizador (comprueba, descarga y arranca);
        # la asociacion .FCStd sigue abriendo la app instalada directamente.
        $shell = New-Object -ComObject WScript.Shell
        $lnk = $shell.CreateShortcut($path)
        $ps = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
        if (-not (Test-Path -Path $ps)) { $ps = 'powershell.exe' }
        $lnk.TargetPath = $ps
        $lnk.Arguments = '-ExecutionPolicy Bypass -File "{0}"' -f $Script:SCRIPT
        $lnk.WorkingDirectory = $Script:Here
        $local = Get-LatestLocal
        if ($local) { $lnk.IconLocation = $local.Exe + ',0' }
        $lnk.Description = (t comment)
        $lnk.Save()
    } catch { }
}
# Un acceso "vigente" apunta al script actual y trabaja en esta carpeta: si no
# (carpeta movida), se regenera en vez de darlo por bueno.
function Test-ShortcutCurrent($path) {
    if (-not $path -or -not (Test-Path -Path $path)) { return $false }
    try {
        $shell = New-Object -ComObject WScript.Shell
        $lnk = $shell.CreateShortcut($path)
        $lnkArgs = [string]$lnk.Arguments
        $lnkWd = [string]$lnk.WorkingDirectory
        if (($lnkArgs -match [regex]::Escape($Script:SCRIPT)) -and ($lnkWd -eq $Script:Here)) { return $true }
        return $false
    } catch { return $false }
}
function New-Shortcut() {
    Remove-Item -Path $Script:NOSHORTCUT -Force -ErrorAction SilentlyContinue
    Write-Shortcut $Script:LNK
    Write-Log 'shortcut created'
}
function New-DesktopShortcut() {
    Remove-Item -Path $Script:NODESKTOP -Force -ErrorAction SilentlyContinue
    Write-Shortcut $Script:DESK_LNK
    Write-Log 'desktop shortcut created'
}
function Remove-Shortcut() {
    if ($Script:LNK) { Remove-Item -Path $Script:LNK -Force -ErrorAction SilentlyContinue }
    try {
        $cur = (Get-ItemProperty -Path 'HKCU:\Software\Classes\.fcstd' -Name '(Default)' `
            -ErrorAction SilentlyContinue).'(Default)'
        if ($cur -eq $Script:PROG_ID) {
            Remove-Item -Path 'HKCU:\Software\Classes\.fcstd' -Recurse -Force -ErrorAction SilentlyContinue
            Remove-Item -Path "HKCU:\Software\Classes\$($Script:PROG_ID)" -Recurse -Force `
                -ErrorAction SilentlyContinue
        }
    } catch { }
    try { New-Item -ItemType File -Path $Script:NOSHORTCUT -Force -ErrorAction Stop | Out-Null } catch { }
    Write-Log 'shortcut removed'
}
function Remove-DesktopShortcut() {
    if ($Script:DESK_LNK) { Remove-Item -Path $Script:DESK_LNK -Force -ErrorAction SilentlyContinue }
    try { New-Item -ItemType File -Path $Script:NODESKTOP -Force -ErrorAction Stop | Out-Null } catch { }
    Write-Log 'desktop shortcut removed'
}
function Test-AssocOwned() {
    try {
        $cur = (Get-ItemProperty -Path 'HKCU:\Software\Classes\.fcstd' -Name '(Default)' `
            -ErrorAction Stop).'(Default)'
        return ($cur -eq $Script:PROG_ID)
    } catch { return $false }
}
# Pertenencia + ruta vigente (self-heal tras mover la carpeta)
function Test-Assoc() {
    if (-not (Test-AssocOwned)) { return $false }
    try {
        $cmd = (Get-ItemProperty -Path "HKCU:\Software\Classes\$($Script:PROG_ID)\shell\open\command" `
            -Name '(Default)' -ErrorAction Stop).'(Default)'
        $local = Get-LatestLocal
        if (-not $local) { return $false }
        if ([string]$cmd -match [regex]::Escape($local.Exe)) { return $true }
        return $false
    } catch { return $false }
}
function Set-Assoc() {
    Remove-Item -Path $Script:NOASSOC -Force -ErrorAction SilentlyContinue
    try {
        $local = Get-LatestLocal
        if (-not $local) { return }
        New-Item -Path 'HKCU:\Software\Classes\.fcstd' -Force -ErrorAction Stop | Out-Null
        Set-ItemProperty -Path 'HKCU:\Software\Classes\.fcstd' -Name '(Default)' `
            -Value $Script:PROG_ID -ErrorAction Stop
        $cmd = '"{0}" "%1"' -f $local.Exe
        New-Item -Path "HKCU:\Software\Classes\$($Script:PROG_ID)\shell\open\command" `
            -Force -ErrorAction Stop | Out-Null
        Set-ItemProperty -Path "HKCU:\Software\Classes\$($Script:PROG_ID)\shell\open\command" `
            -Name '(Default)' -Value $cmd -ErrorAction Stop
        Write-Log 'assoc set'
    } catch { }
}
function Remove-Assoc() {
    try {
        $cur = (Get-ItemProperty -Path 'HKCU:\Software\Classes\.fcstd' -Name '(Default)' `
            -ErrorAction SilentlyContinue).'(Default)'
        if ($cur -eq $Script:PROG_ID) {
            Remove-Item -Path 'HKCU:\Software\Classes\.fcstd' -Recurse -Force -ErrorAction SilentlyContinue
            Remove-Item -Path "HKCU:\Software\Classes\$($Script:PROG_ID)" -Recurse -Force `
                -ErrorAction SilentlyContinue
        }
    } catch { }
    try { New-Item -ItemType File -Path $Script:NOASSOC -Force -ErrorAction Stop | Out-Null } catch { }
    Write-Log 'assoc removed'
}
function Request-Assoc() {
    if (Test-Assoc) { return }
    if (Test-AssocOwned) { Set-Assoc; return }
    if (Test-Path -Path $Script:NOASSOC) { return }
    if ($Script:ASSUME_YES -or (Ask-YesNo (t ask_assoc))) {
        Set-Assoc
        Send-Notify (t assoc_set)
    } else {
        try { New-Item -ItemType File -Path $Script:NOASSOC -Force -ErrorAction Stop | Out-Null } catch { }
    }
}
function Request-Shortcut() {
    if ($Script:LNK -and (Test-Path -Path $Script:LNK)) {
        if (-not (Test-ShortcutCurrent $Script:LNK)) { New-Shortcut }
        return
    }
    if (Test-Path -Path $Script:NOSHORTCUT) { return }
    if ($Script:ASSUME_YES -or (Ask-YesNo (t ask_shortcut))) {
        New-Shortcut
        Send-Notify (t shortcut_created)
    } else {
        try { New-Item -ItemType File -Path $Script:NOSHORTCUT -Force -ErrorAction Stop | Out-Null } catch { }
    }
}
function Request-DesktopShortcut() {
    if (-not $Script:DESK_LNK) { return }
    if (Test-Path -Path $Script:DESK_LNK) {
        if (-not (Test-ShortcutCurrent $Script:DESK_LNK)) { New-DesktopShortcut }
        return
    }
    if (Test-Path -Path $Script:NODESKTOP) { return }
    if ($Script:ASSUME_YES -or (Ask-YesNo (t ask_desktop))) {
        New-DesktopShortcut
        Send-Notify (t desktop_created)
    } else {
        try { New-Item -ItemType File -Path $Script:NODESKTOP -Force -ErrorAction Stop | Out-Null } catch { }
    }
}
# ---------------------------------------------------------------------------
# Backup de configuracion (espejo de backup_config)
# ---------------------------------------------------------------------------
function Backup-Config() {
    try {
        if (-not $env:APPDATA) { return }
        $src = Join-Path $env:APPDATA 'FreeCAD'
        if (-not (Test-Path -Path $src)) { return }
        $recent = Get-ChildItem -Path $Script:BACKUP_DIR -Filter '*.zip' -ErrorAction SilentlyContinue |
            Where-Object { $_.LastWriteTime -gt (Get-Date).AddMinutes(-10) } |
            Select-Object -First 1
        if ($recent) { return }
        New-Item -ItemType Directory -Path $Script:BACKUP_DIR -Force -ErrorAction Stop | Out-Null
        $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
        Compress-Archive -Path $src -DestinationPath (Join-Path $Script:BACKUP_DIR "freecad-cfg-$stamp.zip") `
            -CompressionLevel Optimal -ErrorAction Stop
        Get-ChildItem -Path $Script:BACKUP_DIR -Filter '*.zip' -ErrorAction SilentlyContinue |
            Sort-Object LastWriteTime -Descending |
            Select-Object -Skip 3 |
            Remove-Item -Force -ErrorAction SilentlyContinue
        Write-Log 'config backup saved'
    } catch { }
}
# ---------------------------------------------------------------------------
# Actualizacion
# ---------------------------------------------------------------------------
function Update-Stable() {
    if (-not (Lock-Update)) { return $false }
    try {
        Write-Progress -Activity (t title) -Status (t checking) -Id 1
        $rel = Get-ReleaseStable
        Write-Progress -Activity (t title) -Id 1 -Completed
        if (-not $rel) {
            Write-Log 'check failed (offline?)'
            return $false
        }
        $tag = $rel.Tag
        $url = $rel.Url
        $local = Get-LatestLocal
        if ($local -and ($local.Name -like "*${tag}-Windows-$($Script:ARCH)*")) {
            Write-Log "up to date ($tag)"
            return $true
        }
        $prefix = (t downloading)
        if (-not $local) {
            $prefix = (t no_local)
            Write-Log "no local version; downloading $tag"
            Send-Notify (t no_local) $tag
        }
        $asset = Split-Path -Leaf $url
        $tmp = Join-Path $Script:Here ('.' + $asset + '.part')
        Remove-Item -Path $tmp -Force -ErrorAction SilentlyContinue
        if (-not (Save-UrlWithProgress $url $tmp "$prefix $tag...")) {
            Remove-Item -Path $tmp -Force -ErrorAction SilentlyContinue
            Write-Log "download failed: $tag"
            Send-Notify (t err) (t err_download)
            return $false
        }
        Write-Progress -Activity (t title) -Status (t verifying) -PercentComplete 100 -Id 1
        $exp = Get-UrlText ($url + '-SHA256.txt') 15
        if ($exp) { $exp = ($exp -split '\s+')[0] }
        $act = $null
        try { $act = (Get-FileHash -Path $tmp -Algorithm SHA256 -ErrorAction Stop).Hash } catch { }
        Write-Progress -Activity (t title) -Id 1 -Completed
        # Fail-closed: sin sidecar no hay verificacion posible y NO se instala
        # (antes se instalaba sin verificar). Sin red, la version local sigue
        # usandose: este punto solo se alcanza tras descargar algo nuevo.
        if (-not $exp) {
            Remove-Item -Path $tmp -Force -ErrorAction SilentlyContinue
            Write-Log "sha256 sidecar unavailable: $tag (not updating)"
            Send-Notify (t err) (t err_checksum)
            return $false
        }
        if ((-not $act) -or ($exp.ToLowerInvariant() -ne $act.ToLowerInvariant())) {
            Remove-Item -Path $tmp -Force -ErrorAction SilentlyContinue
            Write-Log "sha256 mismatch: $tag (exp=$exp act=$act)"
            Send-Notify (t err) (t err_checksum)
            return $false
        }
        $dest = Install-FromArchive $tmp $asset
        Remove-Item -Path $tmp -Force -ErrorAction SilentlyContinue
        if (-not $dest) {
            Write-Log "install failed: $tag"
            Send-Notify (t err) (t err_extract)
            return $false
        }
        Write-Log "updated to $tag"
        Send-Notify ((t updated) + " $tag") (t ready)
        return $true
    } finally {
        Unlock-Update
    }
}
# ---------------------------------------------------------------------------
# Acciones
# ---------------------------------------------------------------------------
function Do-Check() {
    $rel = Get-ReleaseStable
    if (-not $rel) {
        Send-Notify (t err) (t err_check)
        [System.Console]::Error.WriteLine((t err_check))
        return $false
    }
    $tag = $rel.Tag
    $local = Get-LatestLocal
    if ($local -and ($local.Name -like "*${tag}-Windows-$($Script:ARCH)*")) {
        Send-Notify (t check_ok) $tag
        Write-Output "$((t check_ok)) $tag"
    } else {
        Send-Notify (t check_new) $tag
        Write-Output "$((t check_new)) $tag"
    }
    return $true
}
function Do-Uninstall() {
    if (-not $Script:ASSUME_YES) {
        if (-not (Ask-YesNo (t confirm_uninstall))) { return }
    }
    Get-BundleDirs | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Path $Script:Here -Filter '.FreeCAD_*.part' -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -match '^\.FreeCAD_[0-9]' } |
        Remove-Item -Force -ErrorAction SilentlyContinue
    if ($Script:LNK) { Remove-Item -Path $Script:LNK -Force -ErrorAction SilentlyContinue }
    if ($Script:DESK_LNK) { Remove-Item -Path $Script:DESK_LNK -Force -ErrorAction SilentlyContinue }
    try {
        $cur = (Get-ItemProperty -Path 'HKCU:\Software\Classes\.fcstd' -Name '(Default)' `
            -ErrorAction SilentlyContinue).'(Default)'
        if ($cur -eq $Script:PROG_ID) {
            Remove-Item -Path 'HKCU:\Software\Classes\.fcstd' -Recurse -Force -ErrorAction SilentlyContinue
            Remove-Item -Path "HKCU:\Software\Classes\$($Script:PROG_ID)" -Recurse -Force `
                -ErrorAction SilentlyContinue
        }
    } catch { }
    Remove-Item -Path $Script:LOG, $Script:LOCK, $Script:NOSHORTCUT, $Script:NOASSOC, $Script:NODESKTOP, $Script:SEVENZR -Force -ErrorAction SilentlyContinue
    Send-Notify (t uninstalled)
    Write-Output (t uninstalled)
}
function Show-Help() {
    $me = Split-Path -Leaf $Script:SCRIPT
    if ($Script:LANG_CODE -eq 'es') {
        @"

$($Script:SUITE) v$($Script:VERSION)

$((t name)) - bundle portable estable: descarga, instala, actualiza y ejecuta.



Uso: $me [opciones] [--] [argumentos de FreeCAD]



Opciones:

  --no-update         Arranca sin comprobar actualizaciones.

  --check             Solo comprueba si hay una version nueva (no descarga).

  --reinstall         Borra la version local y descarga de nuevo la ultima.

  --create-shortcut   Crea el acceso en el menu de inicio.

  --remove-shortcut   Elimina el acceso del menu de inicio.

  --create-desktop    Crea el acceso directo en el Escritorio.

  --remove-desktop    Elimina el acceso directo del Escritorio.

  --associate         Asocia los archivos .FCStd (abrir con doble clic).

  --remove-assoc      Quita la asociación de .FCStd.

  --uninstall         Desinstala (bundle, acceso, asociación, marcas, log).

  -y, --yes           No preguntar (asumir si).

  -v, --verbose       Mostrar informacion adicional.

  -h, --help          Muestra esta ayuda.



Todo lo que va despues de '--' se pasa a FreeCAD, p. ej.:

  $me -- --help

  $me -- mi_archivo.FCStd

"@
    } else {
        @"

$($Script:SUITE) v$($Script:VERSION)

$((t name)) - stable portable bundle: download, install, update and run.



Usage: $me [options] [--] [FreeCAD arguments]



Options:

  --no-update         Run without checking for updates.

  --check             Only check for a new version (no download).

  --reinstall         Remove the local version and download the latest again.

  --create-shortcut   Create the start menu shortcut.

  --remove-shortcut   Remove the start menu shortcut.

  --create-desktop    Create the Desktop shortcut.

  --remove-desktop    Remove the Desktop shortcut.

  --associate         Associate .FCStd files (open on double click).

  --remove-assoc      Remove the .FCStd association.

  --uninstall         Uninstall (bundle, shortcut, association, marks, log).

  -y, --yes           Do not prompt (assume yes).

  -v, --verbose       Show extra information.

  -h, --help          Show this help.



Everything after '--' is passed to FreeCAD, e.g.:

  $me -- --help

  $me -- my_file.FCStd

"@
    }
}
# ---------------------------------------------------------------------------
# Argumentos (misma CLI que linux/FreeCAD-stable.sh)
# ---------------------------------------------------------------------------
$Script:UPDATE = 1
$Script:ACTION = ''
$Script:ASSUME_YES = $false
$Script:VERBOSE = $false
$Script:FC_ARGS = @()
function Parse-Args($argv) {
    $Script:UPDATE = 1
    $Script:ACTION = ''
    $Script:ASSUME_YES = $false
    $Script:VERBOSE = $false
    $Script:FC_ARGS = @()
    $k = 0
    while ($k -lt $argv.Count) {
        $a = [string]$argv[$k]
        switch -Exact ($a) {
            '--' {
                if ($k + 1 -le $argv.Count - 1) { $Script:FC_ARGS += @($argv[($k + 1)..($argv.Count - 1)]) }
                $k = $argv.Count
            }
            '--no-update'       { $Script:UPDATE = 0 }
            '--check'           { $Script:ACTION = 'check' }
            '--reinstall'       { $Script:ACTION = 'reinstall' }
            '--create-shortcut' { $Script:ACTION = 'create-shortcut' }
            '--remove-shortcut' { $Script:ACTION = 'remove-shortcut' }
            '--create-desktop'  { $Script:ACTION = 'create-desktop' }
            '--remove-desktop'  { $Script:ACTION = 'remove-desktop' }
            '--associate'       { $Script:ACTION = 'associate' }
            '--remove-assoc'    { $Script:ACTION = 'remove-assoc' }
            '--uninstall'       { $Script:ACTION = 'uninstall' }
            { $_ -eq '-y' -or $_ -eq '--yes' }         { $Script:ASSUME_YES = $true }
            { $_ -eq '-v' -or $_ -eq '--verbose' }     { $Script:VERBOSE = $true }
            { $_ -eq '-h' -or $_ -eq '--help' }        { $Script:ACTION = 'help' }
            default             { $Script:FC_ARGS += $a }
        }
        $k++
    }
}
# ---------------------------------------------------------------------------
# Principal
# ---------------------------------------------------------------------------
function Invoke-Main($argv) {
    Parse-Args $argv
    if ([string]::IsNullOrEmpty($Script:ARCH)) {
        Send-Notify (t err) "$((t err_arch)) $($env:PROCESSOR_ARCHITECTURE)"
        [System.Console]::Error.WriteLine("$((t err_arch)) $($env:PROCESSOR_ARCHITECTURE)")
        exit 1
    }
    switch ($Script:ACTION) {
        'help'  { Show-Help; exit 0 }
        'check' { if (Do-Check) { exit 0 } else { exit 1 } }
    }
    try {
        $probe = Join-Path $Script:Here '.writetest'
        [System.IO.File]::WriteAllText($probe, 'x')
        Remove-Item -Path $probe -Force
    } catch {
        Send-Notify (t err) "$((t err_nowrite)) $($Script:Here)"
        [System.Console]::Error.WriteLine("$((t err_nowrite)) $($Script:Here)")
        exit 1
    }
    switch ($Script:ACTION) {
        'create-shortcut' { New-Shortcut; Send-Notify (t shortcut_created); exit 0 }
        'remove-shortcut' { Remove-Shortcut; Send-Notify (t shortcut_removed); exit 0 }
        'create-desktop'  { New-DesktopShortcut; Send-Notify (t desktop_created); exit 0 }
        'remove-desktop'  { Remove-DesktopShortcut; Send-Notify (t desktop_removed); exit 0 }
        'associate'       { Set-Assoc; Send-Notify (t assoc_set); exit 0 }
        'remove-assoc'    { Remove-Assoc; Send-Notify (t assoc_removed); exit 0 }
        'uninstall'       { Do-Uninstall; exit 0 }
    }
    if ($Script:ACTION -eq 'reinstall') {
        Get-BundleDirs | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    }
    if ($Script:UPDATE -eq 1) {
        Update-Stable | Out-Null
    }
    $local = Get-LatestLocal
    if (-not $local) {
        Send-Notify (t err) (t err_no_local)
        [System.Console]::Error.WriteLine((t err_no_local))
        exit 1
    }
    Request-Shortcut
    Request-DesktopShortcut
    Request-Assoc
    Backup-Config
    & $local.Exe @Script:FC_ARGS
}
if ($env:FC_TEST -ne '1') { Invoke-Main $args }
