# SAMFMS Health Monitor PowerShell Script
# Monitors the health of all SAMFMS services

param(
    [switch]$Continuous,
    [int]$Interval = 30
)

# Configuration
$Services = @{
    'core' = @{ url = 'http://localhost:21004'; endpoint = '/health' }
    'frontend' = @{ url = 'http://localhost:21015'; endpoint = '/' }
    'nginx' = @{ url = 'http://localhost:21016'; endpoint = '/' }
    'rabbitmq' = @{ url = 'http://localhost:21001'; endpoint = '/' }
    'gps' = @{ url = 'http://localhost:21005'; endpoint = '/health' }
    'trip_planning' = @{ url = 'http://localhost:21006'; endpoint = '/health' }
    'vehicle_maintenance' = @{ url = 'http://localhost:21007'; endpoint = '/health' }
    'utilities' = @{ url = 'http://localhost:21008'; endpoint = '/health' }
    'security' = @{ url = 'http://localhost:21009'; endpoint = '/health' }
    'management' = @{ url = 'http://localhost:21010'; endpoint = '/health' }
    'micro_frontend' = @{ url = 'http://localhost:21011'; endpoint = '/health' }
}

$ApiRoutes = @(
    '/api/health',
    '/api/vehicles',
    '/api/auth/user-exists'
)

function Test-ServiceHealth {
    param(
        [string]$Name,
        [hashtable]$Config
    )
    
    $result = @{
        Name = $Name
        Status = 'Unknown'
        ResponseTime = $null
        Error = $null
        Url = "$($Config.url)$($Config.endpoint)"
    }
    
    try {
        $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
        $response = Invoke-WebRequest -Uri $result.Url -TimeoutSec 10 -UseBasicParsing -ErrorAction Stop
        $stopwatch.Stop()
        
        $result.ResponseTime = $stopwatch.ElapsedMilliseconds
        
        if ($response.StatusCode -eq 200) {
            $result.Status = 'Healthy'
        } else {
            $result.Status = "HTTP_$($response.StatusCode)"
        }
    }
    catch [System.Net.WebException] {
        $result.Status = 'Connection_Failed'
        $result.Error = $_.Exception.Message
    }
    catch [System.TimeoutException] {
        $result.Status = 'Timeout'
        $result.Error = 'Request timed out'
    }
    catch {
        $result.Status = 'Error'
        $result.Error = $_.Exception.Message
    }
    
    return $result
}

function Test-ApiRouting {
    $results = @()
    $coreUrl = 'http://localhost:21004'
    
    foreach ($route in $ApiRoutes) {
        $result = @{
            Route = $route
            Status = 'Unknown'
            ResponseTime = $null
            Error = $null
            Url = "$coreUrl$route"
        }
        
        try {
            $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
            $response = Invoke-WebRequest -Uri $result.Url -TimeoutSec 10 -UseBasicParsing -ErrorAction Stop
            $stopwatch.Stop()
            
            $result.ResponseTime = $stopwatch.ElapsedMilliseconds
            $result.Status = "HTTP_$($response.StatusCode)"
        }
        catch [System.Net.WebException] {
            $result.Status = 'Connection_Failed'
            $result.Error = $_.Exception.Message
        }
        catch [System.TimeoutException] {
            $result.Status = 'Timeout'
            $result.Error = 'Request timed out'
        }
        catch {
            $result.Status = 'Error'
            $result.Error = $_.Exception.Message
        }
        
        $results += $result
    }
    
    return $results
}

function Show-HealthReport {
    param(
        [array]$ServiceResults,
        [array]$ApiResults
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $healthyCount = ($ServiceResults | Where-Object { $_.Status -eq 'Healthy' }).Count
    $totalCount = $ServiceResults.Count
    
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "🏥 SAMFMS Health Check Report" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "Timestamp: $timestamp" -ForegroundColor White
    Write-Host "Overall Status: " -NoNewline
    
    if ($healthyCount -eq $totalCount) {
        Write-Host "✅ HEALTHY" -ForegroundColor Green
    } else {
        Write-Host "⚠️  DEGRADED" -ForegroundColor Yellow
    }
    
    Write-Host "Services: $healthyCount/$totalCount healthy" -ForegroundColor White
    
    Write-Host ""
    Write-Host "📊 Service Status:" -ForegroundColor Yellow
    Write-Host "----------------------------------------" -ForegroundColor Gray
    
    foreach ($service in $ServiceResults) {
        $icon = switch ($service.Status) {
            'Healthy' { '✅' }
            'Connection_Failed' { '❌' }
            'Timeout' { '⏰' }
            'Error' { '❌' }
            default { '⚠️ ' }
        }
        
        $responseTime = if ($service.ResponseTime) { " ($($service.ResponseTime)ms)" } else { "" }
        $statusLine = "{0} {1,-15} {2}{3}" -f $icon, $service.Name, $service.Status, $responseTime
        
        switch ($service.Status) {
            'Healthy' { Write-Host $statusLine -ForegroundColor Green }
            'Connection_Failed' { Write-Host $statusLine -ForegroundColor Red }
            'Timeout' { Write-Host $statusLine -ForegroundColor Yellow }
            'Error' { Write-Host $statusLine -ForegroundColor Red }
            default { Write-Host $statusLine -ForegroundColor Yellow }
        }
        
        if ($service.Error) {
            Write-Host "    Error: $($service.Error)" -ForegroundColor Red
        }
    }
    
    Write-Host ""
    Write-Host "🔗 API Routing Tests:" -ForegroundColor Yellow
    Write-Host "----------------------------------------" -ForegroundColor Gray
    
    foreach ($api in $ApiResults) {
        $icon = if ($api.Status -eq 'HTTP_200') { '✅' } else { '❌' }
        $responseTime = if ($api.ResponseTime) { " ($($api.ResponseTime)ms)" } else { "" }
        $statusLine = "{0} {1,-30} {2}{3}" -f $icon, $api.Route, $api.Status, $responseTime
        
        if ($api.Status -eq 'HTTP_200') {
            Write-Host $statusLine -ForegroundColor Green
        } else {
            Write-Host $statusLine -ForegroundColor Red
        }
        
        if ($api.Error) {
            Write-Host "    Error: $($api.Error)" -ForegroundColor Red
        }
    }
    
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    
    # Show recommendations if there are issues
    $unhealthyServices = $ServiceResults | Where-Object { $_.Status -ne 'Healthy' }
    if ($unhealthyServices.Count -gt 0) {
        Write-Host ""
        Write-Host "⚠️  Issues Detected:" -ForegroundColor Yellow
        foreach ($service in $unhealthyServices) {
            Write-Host "  - $($service.Name): $($service.Status)" -ForegroundColor Red
        }
        
        Write-Host ""
        Write-Host "🔧 Recommendations:" -ForegroundColor Cyan
        Write-Host "  1. Check Docker containers: docker-compose ps" -ForegroundColor White
        Write-Host "  2. Check service logs: docker-compose logs <service-name>" -ForegroundColor White
        Write-Host "  3. Restart services: docker-compose restart <service-name>" -ForegroundColor White
        Write-Host "  4. Check port availability: netstat -an | findstr <port>" -ForegroundColor White
    }
}

function Start-HealthMonitoring {
    Write-Host "🏥 SAMFMS Health Monitor" -ForegroundColor Cyan
    Write-Host "========================" -ForegroundColor Cyan
    
    do {
        Write-Host ""
        Write-Host "🔍 Running health checks..." -ForegroundColor Yellow
        
        # Test individual services
        $serviceResults = @()
        foreach ($serviceName in $Services.Keys) {
            $result = Test-ServiceHealth -Name $serviceName -Config $Services[$serviceName]
            $serviceResults += $result
        }
        
        # Test API routing
        $apiResults = Test-ApiRouting
        
        # Show report
        Show-HealthReport -ServiceResults $serviceResults -ApiResults $apiResults
        
        if ($Continuous) {
            Write-Host ""
            Write-Host "⏰ Next check in $Interval seconds... (Ctrl+C to stop)" -ForegroundColor Gray
            Start-Sleep -Seconds $Interval
        }
    } while ($Continuous)
}

# Main execution
try {
    Start-HealthMonitoring
    
    # Exit with error code if any services are unhealthy
    $serviceResults = @()
    foreach ($serviceName in $Services.Keys) {
        $result = Test-ServiceHealth -Name $serviceName -Config $Services[$serviceName]
        $serviceResults += $result
    }
    
    $unhealthyCount = ($serviceResults | Where-Object { $_.Status -ne 'Healthy' }).Count
    if ($unhealthyCount -gt 0) {
        exit 1
    }
}
catch {
    Write-Host "❌ Health monitoring failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
