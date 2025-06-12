#!/usr/bin/env powershell
# MongoDB Log Filter Script
# Filters out verbose MongoDB connection logs and shows only important messages

param(
    [string]$Service = "",
    [switch]$Follow = $false,
    [int]$Tail = 50,
    [switch]$Errors = $false,
    [switch]$Clean = $false,
    [switch]$Summary = $false
)

function Show-Usage {
    Write-Host "MongoDB Log Filter - Clean up verbose Docker logs" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor Yellow
    Write-Host "  .\filter-logs.ps1                    # View all services with filtering"
    Write-Host "  .\filter-logs.ps1 -Service gps       # View specific service"
    Write-Host "  .\filter-logs.ps1 -Follow            # Follow logs in real-time"
    Write-Host "  .\filter-logs.ps1 -Errors            # Show only errors and warnings"
    Write-Host "  .\filter-logs.ps1 -Clean             # Show only application logs (no MongoDB)"
    Write-Host "  .\filter-logs.ps1 -Summary           # Show service status summary"
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Yellow
    Write-Host "  .\filter-logs.ps1 -Service mongodb_core -Tail 20"
    Write-Host "  .\filter-logs.ps1 -Clean -Follow"
    Write-Host "  .\filter-logs.ps1 -Errors"
    exit
}

# Show usage if no parameters
if (-not $Service -and -not $Follow -and -not $Errors -and -not $Clean -and -not $Summary -and $Tail -eq 50) {
    Show-Usage
}

# Patterns to filter OUT (verbose MongoDB logs)
$FilterOut = @(
    "Connection accepted",
    "Connection ended", 
    "client metadata",
    "Received first command",
    "Interrupted operation",
    "WiredTiger message",
    "checkpoint snapshot",
    "negotiatedCompressors",
    "mongosh",
    "verbose_level"
)

# Patterns to HIGHLIGHT (important messages)
$Highlight = @(
    "ERROR",
    "WARN",
    "Failed",
    "Exception",
    "Timeout",
    "Unhealthy",
    "Started",
    "Listening",
    "Ready"
)

function Filter-MongoLogs {
    param([string]$LogLine)
    
    # Skip empty lines
    if ([string]::IsNullOrWhiteSpace($LogLine)) { return $false }
    
    # If Clean mode, skip MongoDB containers entirely
    if ($Clean -and $LogLine -match "mongodb_\w+-1") { return $false }
    
    # If Errors mode, only show errors/warnings
    if ($Errors) {
        return $LogLine -match "ERROR|WARN|Failed|Exception|Timeout|Unhealthy"
    }
    
    # Filter out verbose patterns
    foreach ($pattern in $FilterOut) {
        if ($LogLine -match $pattern) { return $false }
    }
    
    return $true
}

function Format-LogLine {
    param([string]$LogLine)
    
    # Highlight important messages
    foreach ($pattern in $Highlight) {
        if ($LogLine -match $pattern) {
            if ($pattern -match "ERROR|Failed|Exception|Timeout|Unhealthy") {
                return $LogLine -replace $pattern, "`e[31m$pattern`e[0m"  # Red
            } elseif ($pattern -match "WARN") {
                return $LogLine -replace $pattern, "`e[33m$pattern`e[0m"  # Yellow
            } else {
                return $LogLine -replace $pattern, "`e[32m$pattern`e[0m"  # Green
            }
        }
    }
    
    return $LogLine
}

function Show-Summary {
    Write-Host "`n=== SAMFMS Service Status Summary ===" -ForegroundColor Cyan
    
    try {
        $containers = docker-compose ps --format json | ConvertFrom-Json
        
        $services = @{
            "Infrastructure" = @("rabbitmq", "redis")
            "MongoDB" = @("mongodb_core", "mongodb_gps", "mongodb_trip_planning", "mongodb_vehicle_maintenance", "mongodb_security", "mongodb_users", "mongodb_vehicles", "mongodb_management")
            "Core Services" = @("mcore", "gps_service", "trip_planning_service", "vehicle_maintenance_service")
            "Other Services" = @("utilities_service", "security_service", "management_service", "micro_frontend_service")
            "D-blocks" = @("users_dblock", "vehicles_dblock", "gps_dblock")
            "Frontend" = @("frontend")
        }
        
        foreach ($category in $services.Keys) {
            Write-Host "`n$category:" -ForegroundColor Yellow
            
            foreach ($serviceName in $services[$category]) {
                $container = $containers | Where-Object { $_.Service -eq $serviceName }
                if ($container) {
                    $status = $container.State
                    $health = if ($container.Health) { $container.Health } else { "N/A" }
                    
                    $statusColor = switch ($status) {
                        "running" { "Green" }
                        "exited" { "Red" }
                        default { "Yellow" }
                    }
                    
                    $healthColor = switch ($health) {
                        "healthy" { "Green" }
                        "unhealthy" { "Red" }
                        "starting" { "Yellow" }
                        default { "Gray" }
                    }
                    
                    Write-Host "  ✓ " -NoNewline -ForegroundColor Green
                    Write-Host "$serviceName " -NoNewline
                    Write-Host "[$status]" -NoNewline -ForegroundColor $statusColor
                    if ($health -ne "N/A") {
                        Write-Host " [$health]" -ForegroundColor $healthColor
                    } else {
                        Write-Host ""
                    }
                } else {
                    Write-Host "  ✗ $serviceName [not found]" -ForegroundColor Red
                }
            }
        }
        
        Write-Host "`n=== Quick Commands ===" -ForegroundColor Cyan
        Write-Host "View clean logs:     .\filter-logs.ps1 -Clean -Follow"
        Write-Host "View errors only:    .\filter-logs.ps1 -Errors"
        Write-Host "View specific service: .\filter-logs.ps1 -Service gps_service"
        Write-Host ""
        
    } catch {
        Write-Host "Error getting container status: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Show summary mode
if ($Summary) {
    Show-Summary
    exit
}

# Build docker-compose logs command
$dockerCmd = "docker-compose logs"

if ($Service) {
    $dockerCmd += " $Service"
}

if ($Follow) {
    $dockerCmd += " -f"
} else {
    $dockerCmd += " --tail=$Tail"
}

Write-Host "Filtering logs (hiding verbose MongoDB connection logs)..." -ForegroundColor Green
if ($Clean) {
    Write-Host "Clean mode: Showing only application logs" -ForegroundColor Yellow
}
if ($Errors) {
    Write-Host "Error mode: Showing only errors and warnings" -ForegroundColor Yellow
}
Write-Host "Press Ctrl+C to stop`n" -ForegroundColor Gray

# Execute and filter
try {
    if ($Follow) {
        & cmd /c $dockerCmd | ForEach-Object {
            if (Filter-MongoLogs $_) {
                Write-Host (Format-LogLine $_)
            }
        }
    } else {
        $logs = & cmd /c $dockerCmd
        foreach ($line in $logs) {
            if (Filter-MongoLogs $line) {
                Write-Host (Format-LogLine $line)
            }
        }
    }
} catch {
    Write-Host "Error executing docker-compose logs: $($_.Exception.Message)" -ForegroundColor Red
}
