$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (!(Test-Path '.\venv\Scripts\python.exe')) { throw 'No existe venv. Abre la carpeta CafeTrace que ya tiene tu entorno virtual.' }
# Determine source local IPv4 by asking Windows which local interface routes to an external address.
$ip = $null
try {
    $sock = [System.Net.Sockets.Socket]::new([System.Net.Sockets.AddressFamily]::InterNetwork, [System.Net.Sockets.SocketType]::Dgram, [System.Net.Sockets.ProtocolType]::Udp)
    $sock.Connect('8.8.8.8', 53)
    $ip = ([System.Net.IPEndPoint]$sock.LocalEndPoint).Address.ToString()
    $sock.Dispose()
} catch { }
if (-not $ip -or $ip -match '^127\.') {
    $ips = @(Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue | Where-Object { $_.IPAddress -notmatch '^(127\.|169\.254\.)' -and $_.PrefixOrigin -ne 'WellKnown' })
    if ($ips.Count -gt 0) { $ip = $ips[0].IPAddress }
}
if (-not $ip) { throw 'No se detectó una IP privada. Conecta el equipo a Wi-Fi o Ethernet y vuelve a intentar.' }
$env:CAFETRACE_PUBLIC_BASE_URL = "http://$($ip):8000"
$env:CAFETRACE_ALLOWED_HOSTS = "127.0.0.1,localhost,$ip"
Write-Host '--------------------------------------------------' -ForegroundColor DarkYellow
Write-Host 'CAFETRACE · ACCESO DESDE CELULAR' -ForegroundColor Yellow
Write-Host "Catálogo: http://$($ip):8000/explorar/" -ForegroundColor Cyan
Write-Host "Administración: http://$($ip):8000/acceder/" -ForegroundColor Cyan
Write-Host 'Abre ese catálogo en el celular conectado a la MISMA red Wi-Fi.' -ForegroundColor Yellow
Write-Host 'Si Windows pregunta por el firewall, permite red privada.' -ForegroundColor Yellow
Write-Host 'No abras el puerto 8000 en Internet; este servidor es solo de desarrollo.' -ForegroundColor Yellow
Write-Host 'Para detenerlo: Ctrl+C' -ForegroundColor Yellow
Write-Host '--------------------------------------------------' -ForegroundColor DarkYellow
& '.\venv\Scripts\python.exe' manage.py runserver 0.0.0.0:8000
