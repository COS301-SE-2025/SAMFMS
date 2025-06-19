# PowerShell script to process invitation system maintenance tasks
# This script should be scheduled to run periodically

# Script Configuration
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$LOG_FILE = Join-Path $SCRIPT_DIR "invitation_maintenance.log"

function Write-Log {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Message,
        
        [Parameter(Mandatory=$false)]
        [string]$Level = "INFO"
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "$timestamp [$Level] $Message"
    
    Write-Output $logMessage
    Add-Content -Path $LOG_FILE -Value $logMessage
}

function Run-PythonScript {
    param(
        [Parameter(Mandatory=$true)]
        [string]$ScriptName,
        
        [Parameter(Mandatory=$true)]
        [string]$Description
    )
    
    $scriptPath = Join-Path $SCRIPT_DIR $ScriptName
    
    Write-Log "Starting $Description..."
    
    try {
        $output = & python $scriptPath 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Log "Successfully completed $Description"
        }
        else {
            Write-Log "Failed to run $Description - Exit code: $LASTEXITCODE" -Level "ERROR"
        }
        
        # Log output from the script
        foreach ($line in $output) {
            Write-Log "  > $line" -Level "SCRIPT"
        }
    }
    catch {
        Write-Log "Error running $Description: $($_.Exception.Message)" -Level "ERROR"
    }
}

# Main script execution
Write-Log "===== Starting Invitation System Maintenance ====="

# Process email queue
Run-PythonScript -ScriptName "process_email_queue.py" -Description "email queue processor"

# Clean up expired invitations
Run-PythonScript -ScriptName "cleanup_invitations.py" -Description "invitation cleanup"

Write-Log "===== Completed Invitation System Maintenance ====="
