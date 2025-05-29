# PowerShell script to run SQL tool tests

# Set PowerShell to use UTF-8 encoding
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Function to run a Python script and check its exit code
function Run-PythonScript {
    param (
        [string]$ScriptPath,
        [string]$Description
    )
    
    Write-Host "=== Running $Description ===" -ForegroundColor Cyan
    
    try {
        # Run the Python script
        python $ScriptPath
        
        # Check if the script ran successfully
        if ($LASTEXITCODE -eq 0) {
            Write-Host "$Description completed successfully!" -ForegroundColor Green
            return $true
        } else {
            Write-Host "$Description failed with exit code $LASTEXITCODE" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "Error running $Description: $_" -ForegroundColor Red
        return $false
    }
}

# Main script
Write-Host "=== SQL Tool Test Suite ===" -ForegroundColor Yellow
Write-Host "This script tests the SQL query tool with a sample SQLite database."
Write-Host "========================================" -ForegroundColor Yellow

# Step 1: Create the test database
$dbCreated = Run-PythonScript -ScriptPath "tests\create_test_db.py" -Description "Database Creation"

# Step 2: Run the SQL tool tests if the database was created successfully
if ($dbCreated) {
    $testsSucceeded = Run-PythonScript -ScriptPath "tests\test_sql_tool.py" -Description "SQL Tool Tests"
    
    # Summary
    if ($testsSucceeded) {
        Write-Host "`nAll tests completed successfully!" -ForegroundColor Green
    } else {
        Write-Host "`nSome tests failed. Please check the error messages above." -ForegroundColor Red
    }
} else {
    Write-Host "`nCannot run SQL tool tests because database creation failed." -ForegroundColor Red
}

# Clean up
Write-Host "`nDo you want to keep the test database? (Y/N)" -ForegroundColor Yellow
$response = Read-Host
if ($response.ToUpper() -eq "N") {
    if (Test-Path "test_db.sqlite") {
        Remove-Item "test_db.sqlite"
        Write-Host "Test database removed." -ForegroundColor Green
    } else {
        Write-Host "Test database not found." -ForegroundColor Yellow
    }
}
