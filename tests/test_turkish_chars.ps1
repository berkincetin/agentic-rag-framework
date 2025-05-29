# PowerShell script to test Turkish character handling in the Agentic RAG API

# Set PowerShell to use UTF-8 encoding
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# API URL
$API_URL = "http://localhost:8000"

# Function to test a Turkish query
function Test-TurkishQuery {
    param (
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
        
        # Make the request with proper content type
        $response = Invoke-WebRequest -Method POST -Uri "$API_URL/bots/StudentBot/query" -Body $body -ContentType "application/json; charset=utf-8" -ErrorAction Stop
        
        # Parse the response
        $responseContent = $response.Content
        $responseJson = $responseContent | ConvertFrom-Json
        
        # Display the results
        Write-Host "Response received successfully!" -ForegroundColor Green
        Write-Host "Original query: $($responseJson.query)"
        Write-Host "Response: $($responseJson.response.Substring(0, [Math]::Min(100, $responseJson.response.Length)))..."
        
        # Verify Turkish characters in the response
        if ($responseJson.query -eq $Query) {
            Write-Host "✓ Query preserved Turkish characters correctly" -ForegroundColor Green
        } else {
            Write-Host "✗ Query did not preserve Turkish characters" -ForegroundColor Red
            Write-Host "  Original: $Query"
            Write-Host "  Received: $($responseJson.query)"
        }
        
        return $true
    }
    catch [System.Net.WebException] {
        if ($_.Exception.Response) {
            $statusCode = [int]$_.Exception.Response.StatusCode
            $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
            $responseBody = $reader.ReadToEnd()
            Write-Host "Error: Received status code $statusCode" -ForegroundColor Red
            Write-Host "Response: $responseBody" -ForegroundColor Red
        } else {
            Write-Host "Error: Could not connect to the API server. Make sure it's running." -ForegroundColor Red
        }
        return $false
    }
    catch {
        Write-Host "Error: $_" -ForegroundColor Red
        return $false
    }
}

# Main script
Write-Host "=== Turkish Character Handling Test ===" -ForegroundColor Yellow
Write-Host "This script tests the API's ability to handle Turkish characters."
Write-Host "Make sure the API server is running before executing this test."
Write-Host "API URL: $API_URL"
Write-Host "========================================" -ForegroundColor Yellow

# Turkish test queries with special characters
$testQueries = @(
    "Merhaba, nasılsın?",  # Basic greeting with ı
    "Öğrenci kayıt işlemleri nasıl yapılır?",  # Contains ö, ğ, ı
    "Şu anda çalışan dersler hangileri?",  # Contains ş, ç
    "İstanbul'daki üniversiteler",  # Contains İ, ü
    "Güz döneminde açılan dersler nelerdir?"  # Contains ü, ç, ı
)

# Test each query
$success = $true
foreach ($query in $testQueries) {
    $result = Test-TurkishQuery -Query $query -SessionId "test-turkish-chars"
    if (-not $result) {
        $success = $false
    }
    Write-Host ""
}

# Summary
if ($success) {
    Write-Host "All tests completed. Check the results above for any issues." -ForegroundColor Green
} else {
    Write-Host "Tests failed. Please check the error messages above." -ForegroundColor Red
}
