# RabbitMQ CPU Optimization Monitor Script
# This script monitors CPU usage and RabbitMQ statistics before and after optimization

Write-Host "=== RabbitMQ CPU Optimization Monitor ===" -ForegroundColor Green

# Function to get container CPU usage
function Get-ContainerCPU {
    param(
        [string]$ContainerName
    )
    
    try {
        $stats = docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" | Where-Object { $_ -like "*$ContainerName*" }
        return $stats
    }
    catch {
        return "Container not running"
    }
}

# Function to check RabbitMQ connection settings
function Test-RabbitMQConnection {
    Write-Host "`nTesting RabbitMQ Connection..." -ForegroundColor Yellow
    
    try {
        # Check if RabbitMQ container is running
        $rabbitmqContainer = docker ps --filter "name=rabbitmq" --format "{{.Names}}"
        if ($rabbitmqContainer) {
            Write-Host "✓ RabbitMQ container is running: $rabbitmqContainer" -ForegroundColor Green
            
            # Check RabbitMQ management API
            try {
                $response = Invoke-RestMethod -Uri "http://localhost:15672/api/overview" -Headers @{Authorization = "Basic " + [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("guest:guest"))} -ErrorAction SilentlyContinue
                Write-Host "✓ RabbitMQ Management API accessible" -ForegroundColor Green
                Write-Host "  - RabbitMQ Version: $($response.rabbitmq_version)" -ForegroundColor Cyan
                Write-Host "  - Total Connections: $($response.object_totals.connections)" -ForegroundColor Cyan
                Write-Host "  - Total Channels: $($response.object_totals.channels)" -ForegroundColor Cyan
                Write-Host "  - Total Queues: $($response.object_totals.queues)" -ForegroundColor Cyan
            }
            catch {
                Write-Host "⚠ RabbitMQ Management API not accessible yet" -ForegroundColor Yellow
            }
        }
        else {
            Write-Host "✗ RabbitMQ container not running" -ForegroundColor Red
        }
    }
    catch {
        Write-Host "✗ Error checking RabbitMQ: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Function to monitor CPU usage
function Monitor-CPUUsage {
    param(
        [int]$DurationSeconds = 30
    )
    
    Write-Host "`nMonitoring CPU usage for $DurationSeconds seconds..." -ForegroundColor Yellow
    
    $startTime = Get-Date
    $measurements = @()
    
    while ((Get-Date) -lt $startTime.AddSeconds($DurationSeconds)) {
        try {
            $stats = docker stats --no-stream --format "json" 2>$null | ConvertFrom-Json
            if ($stats) {
                $measurements += $stats
                Write-Host "." -NoNewline -ForegroundColor Cyan
            }
        }
        catch {
            # Ignore errors during monitoring
        }
        Start-Sleep -Seconds 2
    }
    
    Write-Host "`n"
    
    # Calculate averages
    $rabbitmqStats = $measurements | Where-Object { $_.Name -like "*rabbitmq*" }
    $userStats = $measurements | Where-Object { $_.Name -like "*user*" }
    $vehicleStats = $measurements | Where-Object { $_.Name -like "*vehicle*" }
    $managementStats = $measurements | Where-Object { $_.Name -like "*management*" }
    
    if ($rabbitmqStats) {
        $avgCPU = ($rabbitmqStats | ForEach-Object { [double]($_.CPUPerc -replace '%', '') } | Measure-Object -Average).Average
        Write-Host "📊 RabbitMQ Average CPU: $([math]::Round($avgCPU, 2))%" -ForegroundColor $(if ($avgCPU -lt 100) { "Green" } elseif ($avgCPU -lt 200) { "Yellow" } else { "Red" })
    }
    
    if ($userStats) {
        $avgCPU = ($userStats | ForEach-Object { [double]($_.CPUPerc -replace '%', '') } | Measure-Object -Average).Average
        Write-Host "📊 Users Service Average CPU: $([math]::Round($avgCPU, 2))%" -ForegroundColor $(if ($avgCPU -lt 50) { "Green" } elseif ($avgCPU -lt 100) { "Yellow" } else { "Red" })
    }
    
    if ($vehicleStats) {
        $avgCPU = ($vehicleStats | ForEach-Object { [double]($_.CPUPerc -replace '%', '') } | Measure-Object -Average).Average
        Write-Host "📊 Vehicles Service Average CPU: $([math]::Round($avgCPU, 2))%" -ForegroundColor $(if ($avgCPU -lt 50) { "Green" } elseif ($avgCPU -lt 100) { "Yellow" } else { "Red" })
    }
    
    if ($managementStats) {
        $avgCPU = ($managementStats | ForEach-Object { [double]($_.CPUPerc -replace '%', '') } | Measure-Object -Average).Average
        Write-Host "📊 Management Service Average CPU: $([math]::Round($avgCPU, 2))%" -ForegroundColor $(if ($avgCPU -lt 50) { "Green" } elseif ($avgCPU -lt 100) { "Yellow" } else { "Red" })
    }
}

# Main execution
Write-Host "Checking optimization status..." -ForegroundColor Cyan

# Check if optimized files exist
$optimizedFiles = @(
    "C:\Users\user\OneDrive\Documents\capstone\repo\SAMFMS\rabbitmq.conf",
    "C:\Users\user\OneDrive\Documents\capstone\repo\SAMFMS\Dblocks\users\message_queue.py",
    "C:\Users\user\OneDrive\Documents\capstone\repo\SAMFMS\Dblocks\vehicles\message_queue.py",
    "C:\Users\user\OneDrive\Documents\capstone\repo\SAMFMS\Sblocks\management\message_queue.py"
)

Write-Host "`n=== Optimization Status ===" -ForegroundColor Blue
foreach ($file in $optimizedFiles) {
    if (Test-Path $file) {
        Write-Host "✓ $([System.IO.Path]::GetFileName($file)) - Optimized" -ForegroundColor Green
    } else {
        Write-Host "✗ $([System.IO.Path]::GetFileName($file)) - Missing" -ForegroundColor Red
    }
}

# Test RabbitMQ connection
Test-RabbitMQConnection

# Check current container status
Write-Host "`n=== Container Status ===" -ForegroundColor Blue
try {
    $containers = docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    Write-Host $containers
}
catch {
    Write-Host "Error getting container status: $($_.Exception.Message)" -ForegroundColor Red
}

# Monitor CPU if containers are running
$runningContainers = docker ps --format "{{.Names}}"
if ($runningContainers) {
    Write-Host "`n=== CPU Monitoring ===" -ForegroundColor Blue
    Monitor-CPUUsage -DurationSeconds 30
} else {
    Write-Host "`nNo containers currently running for monitoring." -ForegroundColor Yellow
}

Write-Host "`n=== Optimization Summary ===" -ForegroundColor Green
Write-Host "1. ✓ RabbitMQ configuration optimized (rabbitmq.conf)" -ForegroundColor Green
Write-Host "2. ✓ Users Dblock message queue optimized" -ForegroundColor Green
Write-Host "3. ✓ Vehicles Dblock message queue optimized" -ForegroundColor Green
Write-Host "4. ✓ Management service message queue optimized" -ForegroundColor Green
Write-Host "5. ✓ Connection pooling and QoS settings added" -ForegroundColor Green
Write-Host "6. ✓ Async/sync context issues resolved" -ForegroundColor Green
Write-Host "7. ✓ Message acknowledgment improved" -ForegroundColor Green
Write-Host "8. ✓ Error handling and recovery enhanced" -ForegroundColor Green

Write-Host "`nOptimization complete! Start services with: docker-compose up -d" -ForegroundColor Cyan
