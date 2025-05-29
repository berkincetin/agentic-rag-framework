# PowerShell script to test the SQL tool through the API

# Set PowerShell to use UTF-8 encoding
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# API URL
$API_URL = "http://localhost:8000"

# Function to test a query
function Test-Query {
    param (
        [string]$BotName,
        [string]$Query,
        [string]$SessionId
    )
    
    Write-Host "Testing query: $Query" -ForegroundColor Cyan
    
    try {
        # Create the request body
        $body = @{
            query = $Query
            session_id = $SessionId
        } | ConvertTo-Json
        
        # Make the request
        $response = Invoke-WebRequest -Uri "$API_URL/bots/$BotName/query" -Method Post -Body $body -ContentType "application/json; charset=utf-8"
        
        # Parse the response
        $result = $response.Content | ConvertFrom-Json
        
        Write-Host "Response status: $($response.StatusCode)" -ForegroundColor Green
        Write-Host "Response content type: $($response.Headers['Content-Type'])" -ForegroundColor Green
        
        # Check if the response contains tool responses
        if ($result.tool_responses) {
            Write-Host "Tool responses found!" -ForegroundColor Green
            
            # Check for SQL tool response
            $sqlResponses = $result.tool_responses | Where-Object { $_.tool_name -eq "SQLQueryTool" }
            
            if ($sqlResponses) {
                $sqlResponse = $sqlResponses[0].content
                
                Write-Host "SQL Tool was used!" -ForegroundColor Green
                Write-Host "SQL Query: $($sqlResponse.query)" -ForegroundColor Yellow
                Write-Host "Success: $($sqlResponse.success)" -ForegroundColor Yellow
                Write-Host "Results count: $($sqlResponse.count)" -ForegroundColor Yellow
                
                # Display a sample of the results if any
                if ($sqlResponse.count -gt 0) {
                    Write-Host "Sample result:" -ForegroundColor Yellow
                    $sqlResponse.results[0] | ConvertTo-Json
                }
            } else {
                Write-Host "SQL Tool was NOT used in the response." -ForegroundColor Red
            }
        }
        
        # Display the bot's response
        Write-Host "`nBot response:" -ForegroundColor Magenta
        Write-Host $result.response
        
        return $true
    } catch {
        Write-Host "Error: $_" -ForegroundColor Red
        Write-Host "Status Code: $($_.Exception.Response.StatusCode)" -ForegroundColor Red
        
        if ($_.Exception.Response) {
            $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
            $reader.BaseStream.Position = 0
            $reader.DiscardBufferedData()
            $responseBody = $reader.ReadToEnd()
            Write-Host "Response body: $responseBody" -ForegroundColor Red
        }
        
        return $false
    }
}

# Main script
Write-Host "=== SQL Tool API Test (Fixed) ===" -ForegroundColor Yellow
Write-Host "This script tests the SQL query tool through the API."
Write-Host "Make sure the API server is running before executing this test."
Write-Host "API URL: $API_URL"
Write-Host "========================================" -ForegroundColor Yellow

# Test queries
$testQueries = @(
    # Direct SQL queries
    "Show me all staff members in the Computer Science department",
    "What is the budget for the Computer Science department?",
    "List all facilities"
)

# Test each query with the AdminBot (which has the SQL tool enabled)
$botName = "AdminBot"
$sessionId = "test-sql-api-fixed"

$success = $true
foreach ($query in $testQueries) {
    $result = Test-Query -BotName $botName -Query $query -SessionId $sessionId
    if (-not $result) {
        $success = $false
    }
    Write-Host "`n" -ForegroundColor Yellow
}

# Summary
if ($success) {
    Write-Host "All tests completed successfully!" -ForegroundColor Green
} else {
    Write-Host "Some tests failed. Check the error messages above." -ForegroundColor Red
}
