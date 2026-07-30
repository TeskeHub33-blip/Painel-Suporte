$ErrorActionPreference = "Stop"
$base = "C:\Users\WellingtonErvinoTesk\Documents\Claude\manual_suporte"
Set-Location $base

# Trava simples para impedir que duas execucoes rodem ao mesmo tempo (evita commits/pushes
# concorrentes que corrompem o index.html publicado).
$lockFile = "$base\refresh.lock"
if (Test-Path $lockFile) {
    $lockAge = (Get-Date) - (Get-Item $lockFile).LastWriteTime
    if ($lockAge.TotalMinutes -lt 10) {
        Add-Content -Path "$base\refresh_log.txt" -Value "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') PULADO: outra execucao ja em andamento (lock com $([int]$lockAge.TotalSeconds)s)"
        exit 0
    }
}
Set-Content -Path $lockFile -Value (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

$token = "25185219-1513-4ea0-a02f-7839162405f2"
$nowUtc = [DateTime]::UtcNow
$todayStr = $nowUtc.ToString("yyyy-MM-dd")
$nowIso = $nowUtc.ToString("yyyy-MM-ddTHH:mm:ss")

function Invoke-Curl($url, $outFile) {
    & curl.exe -s $url -o $outFile
}

$MONTH_SELECT = "id,protocol,category,urgency,resolvedIn,slaSolutionDate,status,origin,createdDate,resolvedInFirstCall,actionCount,subject,ownerTeam,reopenedIn,tags"
$MONTH_EXPAND = "owner(`$select=businessName),clients,statusHistories"

function Get-MonthWindow($year, $month) {
    $start = Get-Date -Year $year -Month $month -Day 1
    $end = $start.AddMonths(1)
    return @{ start = $start.ToString("yyyy-MM-dd"); end = $end.ToString("yyyy-MM-dd"); mid = $start.AddDays(10).ToString("yyyy-MM-dd") }
}

function Fetch-Month($year, $month, $outFile) {
    $w = Get-MonthWindow $year $month
    $urlA = "https://api.movidesk.com/public/v1/tickets?token=$token&`$select=$MONTH_SELECT&`$expand=$MONTH_EXPAND&`$filter=resolvedIn%20ge%20$($w.start)T00:00:00Z%20and%20resolvedIn%20lt%20$($w.mid)T00:00:00Z&`$top=1000"
    $urlB = "https://api.movidesk.com/public/v1/tickets?token=$token&`$select=$MONTH_SELECT&`$expand=$MONTH_EXPAND&`$filter=resolvedIn%20ge%20$($w.mid)T00:00:00Z%20and%20resolvedIn%20lt%20$($w.end)T00:00:00Z&`$top=1000"
    Invoke-Curl $urlA "$base\_tmp_a.json"
    Invoke-Curl $urlB "$base\_tmp_b.json"
    $a = Get-Content "$base\_tmp_a.json" -Raw -Encoding UTF8 | ConvertFrom-Json
    $b = Get-Content "$base\_tmp_b.json" -Raw -Encoding UTF8 | ConvertFrom-Json
    $all = @($a) + @($b)
    $all | ConvertTo-Json -Depth 10 | Out-File -FilePath $outFile -Encoding utf8
}

try {
    # 1. Chamados abertos (agora com clients/organizacao e reopenedIn, para o relatorio de clientes)
    $urlOpen = "https://api.movidesk.com/public/v1/tickets?token=$token&`$select=id,protocol,subject,category,urgency,status,ownerTeam,createdDate,lastUpdate,tags,slaSolutionDate,reopenedIn&`$expand=owner(`$select=businessName),clients,statusHistories&`$filter=status%20ne%20%27Fechado%27%20and%20status%20ne%20%27Cancelado%27%20and%20status%20ne%20%27Resolvido%27&`$top=500"
    Invoke-Curl $urlOpen "$base\tickets_full.json"

    # 2. Resolvidos hoje
    $urlToday = "https://api.movidesk.com/public/v1/tickets?token=$token&`$select=id,protocol,subject,category,status,resolvedIn,resolvedInFirstCall,actionCount,createdDate,origin,ownerTeam&`$expand=owner(`$select=businessName)&`$filter=resolvedIn%20ge%20${todayStr}T00:00:00Z&`$top=200"
    Invoke-Curl $urlToday "$base\resolved_today.json"

    # 3. Resolvidos nos ultimos 3 meses (mes corrente sempre atualizado; meses passados sao fixos, so buscados uma vez)
    for ($offset = 0; $offset -le 2; $offset++) {
        $target = $nowUtc.AddMonths(-$offset)
        $outFile = "$base\resolved_month_$offset.json"
        if ($offset -eq 0 -or -not (Test-Path $outFile)) {
            Fetch-Month $target.Year $target.Month $outFile
        }
    }

    # 4. Gerar o HTML
    & python "$base\build_dashboard.py" $nowIso

    # 5. Publicar no GitHub Pages (index.html = copia do dashboard)
    Copy-Item "$base\dashboard_suporte.html" "$base\index.html" -Force
    Set-Location $base
    try {
        git add index.html *> $null
        $changed = git status --porcelain index.html
        if ($changed) {
            git commit -m "Atualizacao automatica $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" *> $null
            git push origin main *> $null
        }
    } catch {
        Add-Content -Path "$base\refresh_log.txt" -Value "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') AVISO git: $($_.Exception.Message)"
    }

    Add-Content -Path "$base\refresh_log.txt" -Value "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') OK"
} catch {
    Add-Content -Path "$base\refresh_log.txt" -Value "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ERRO: $($_.Exception.Message)"
} finally {
    Remove-Item -Path $lockFile -Force -ErrorAction SilentlyContinue
}
