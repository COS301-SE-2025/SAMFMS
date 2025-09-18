#!/usr/bin/env pwsh

Write-Host "=====================================" -ForegroundColor Blue
Write-Host "  SAMFMS Algorithm Validation Tests" -ForegroundColor Blue
Write-Host "=====================================" -ForegroundColor Blue
Write-Host ""
Write-Host "Starting validation tests..." -ForegroundColor Green
Write-Host ""

# Change to script directory
Set-Location $PSScriptRoot

# Run the test script
node runAlgorithmTests.js

Write-Host ""
Write-Host "=====================================" -ForegroundColor Blue
Write-Host "Tests completed! Check test-results folder for detailed reports." -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Blue

# Keep window open if running interactively
if ($Host.Name -eq "ConsoleHost") {
    Write-Host "Press any key to continue..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}