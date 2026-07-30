$base = "C:\Users\WellingtonErvinoTesk\Documents\Claude\manual_suporte"

Add-Content -Path "$base\watchdog_log.txt" -Value "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') run_forever iniciado (PID $PID)"

# Loop de atualizacao a cada 5 minutos (roda para sempre)
while ($true) {
    # Reinicia o servidor web sempre que ele nao estiver escutando (ele pode ter sido derrubado)
    $serverRunning = Get-NetTCPConnection -LocalPort 8080 -State Listen -ErrorAction SilentlyContinue
    if (-not $serverRunning) {
        Add-Content -Path "$base\watchdog_log.txt" -Value "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') servidor web nao encontrado, reiniciando"
        Start-Process -FilePath "python.exe" -ArgumentList "-m http.server 8080 --bind 0.0.0.0" -WorkingDirectory $base -WindowStyle Minimized -RedirectStandardOutput "$base\server_out.log" -RedirectStandardError "$base\server_err.log"
    }
    try {
        powershell -ExecutionPolicy Bypass -File "$base\refresh_dashboard.ps1"
    } catch {
        Add-Content -Path "$base\refresh_log.txt" -Value "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ERRO NO LOOP: $($_.Exception.Message)"
    }
    Start-Sleep -Seconds 300
}
