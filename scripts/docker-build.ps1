# Docker build and deployment script for Agentic RAG System
# Developed by Atlas University, Istanbul, Türkiye
# PowerShell script for Windows environments

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("build", "start", "stop", "restart", "logs", "clean", "dev", "prod", "test")]
    [string]$Action = "build",
    
    [Parameter(Mandatory=$false)]
    [switch]$Force,
    
    [Parameter(Mandatory=$false)]
    [switch]$Verbose
)

# Colors for output
$Red = "`e[31m"
$Green = "`e[32m"
$Yellow = "`e[33m"
$Blue = "`e[34m"
$Reset = "`e[0m"

function Write-ColorOutput {
    param([string]$Message, [string]$Color = $Reset)
    Write-Host "${Color}$Message${Reset}"
}

function Write-Success {
    param([string]$Message)
    Write-ColorOutput "✓ $Message" $Green
}

function Write-Warning {
    param([string]$Message)
    Write-ColorOutput "⚠ $Message" $Yellow
}

function Write-Error {
    param([string]$Message)
    Write-ColorOutput "✗ $Message" $Red
}

function Write-Info {
    param([string]$Message)
    Write-ColorOutput "ℹ $Message" $Blue
}

function Test-DockerInstallation {
    Write-Info "Checking Docker installation..."
    
    try {
        $dockerVersion = docker --version
        Write-Success "Docker found: $dockerVersion"
    }
    catch {
        Write-Error "Docker is not installed or not in PATH"
        Write-Info "Please install Docker Desktop from: https://docs.docker.com/desktop/install/windows-install/"
        exit 1
    }
    
    try {
        $composeVersion = docker-compose --version
        Write-Success "Docker Compose found: $composeVersion"
    }
    catch {
        Write-Error "Docker Compose is not installed or not in PATH"
        exit 1
    }
}

function Test-EnvironmentFile {
    Write-Info "Checking environment configuration..."
    
    if (-not (Test-Path ".env")) {
        Write-Warning ".env file not found"
        Write-Info "Creating sample .env file..."
        
        $envContent = @"
# API Keys
OPENAI_API_KEY=your_openai_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=false
LOG_LEVEL=INFO
"@
        $envContent | Out-File -FilePath ".env" -Encoding UTF8
        Write-Warning "Please edit .env file with your actual API keys before starting the application"
        return $false
    }
    else {
        Write-Success ".env file found"
        
        # Check for required keys
        $envContent = Get-Content ".env"
        $hasOpenAI = $envContent | Where-Object { $_ -match "OPENAI_API_KEY=.+" }
        $hasTavily = $envContent | Where-Object { $_ -match "TAVILY_API_KEY=.+" }
        
        if (-not $hasOpenAI) {
            Write-Warning "OPENAI_API_KEY not set in .env file"
        }
        if (-not $hasTavily) {
            Write-Warning "TAVILY_API_KEY not set in .env file"
        }
        
        return ($hasOpenAI -and $hasTavily)
    }
}

function Build-Application {
    Write-Info "Building Agentic RAG Docker images..."
    
    $buildArgs = @("docker-compose", "build")
    if ($Verbose) { $buildArgs += "--verbose" }
    if ($Force) { $buildArgs += "--no-cache" }
    
    & $buildArgs[0] $buildArgs[1..($buildArgs.Length-1)]
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Docker images built successfully"
    }
    else {
        Write-Error "Failed to build Docker images"
        exit 1
    }
}

function Start-Application {
    param([string]$Environment = "prod")
    
    $composeFile = if ($Environment -eq "dev") { "docker-compose.dev.yml" } else { "docker-compose.yml" }
    Write-Info "Starting Agentic RAG application ($Environment environment)..."
    
    $startArgs = @("docker-compose")
    if ($Environment -eq "dev") { $startArgs += @("-f", $composeFile) }
    $startArgs += @("up", "-d")
    
    & $startArgs[0] $startArgs[1..($startArgs.Length-1)]
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Application started successfully"
        Write-Info "Services available at:"
        Write-Info "  • API: http://localhost:8000"
        Write-Info "  • API Docs: http://localhost:8000/docs"
        Write-Info "  • Gradio UI: http://localhost:7860"
        Write-Info "  • MongoDB Express: http://localhost:8081"
        
        if ($Environment -eq "dev") {
            Write-Info "Development mode: Hot reload enabled"
        }
    }
    else {
        Write-Error "Failed to start application"
        exit 1
    }
}

function Stop-Application {
    Write-Info "Stopping Agentic RAG application..."
    
    docker-compose down
    docker-compose -f docker-compose.dev.yml down 2>$null
    
    Write-Success "Application stopped"
}

function Show-Logs {
    Write-Info "Showing application logs..."
    docker-compose logs -f agentic-rag
}

function Clean-Application {
    Write-Info "Cleaning up Docker resources..."
    
    if ($Force) {
        Write-Warning "Force cleanup: This will remove all data!"
        docker-compose down -v --remove-orphans
        docker-compose -f docker-compose.dev.yml down -v --remove-orphans 2>$null
        docker system prune -f
    }
    else {
        docker-compose down --remove-orphans
        docker-compose -f docker-compose.dev.yml down --remove-orphans 2>$null
    }
    
    Write-Success "Cleanup completed"
}

function Test-Application {
    Write-Info "Testing application health..."
    
    # Wait for application to be ready
    $maxAttempts = 30
    $attempt = 0
    
    do {
        $attempt++
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8000/" -TimeoutSec 5
            if ($response.StatusCode -eq 200) {
                Write-Success "Application is healthy"
                return
            }
        }
        catch {
            Write-Info "Waiting for application... (attempt $attempt/$maxAttempts)"
            Start-Sleep -Seconds 2
        }
    } while ($attempt -lt $maxAttempts)
    
    Write-Error "Application health check failed"
    exit 1
}

# Main execution
Write-Info "Agentic RAG Docker Management Script"
Write-Info "Developed by Atlas University, Istanbul, Türkiye"
Write-Info ""

Test-DockerInstallation

switch ($Action) {
    "build" {
        Test-EnvironmentFile | Out-Null
        Build-Application
    }
    "start" {
        if (-not (Test-EnvironmentFile)) {
            Write-Error "Please configure .env file before starting"
            exit 1
        }
        Start-Application -Environment "prod"
    }
    "dev" {
        if (-not (Test-EnvironmentFile)) {
            Write-Error "Please configure .env file before starting"
            exit 1
        }
        Start-Application -Environment "dev"
    }
    "stop" {
        Stop-Application
    }
    "restart" {
        Stop-Application
        Start-Sleep -Seconds 2
        Start-Application -Environment "prod"
    }
    "logs" {
        Show-Logs
    }
    "clean" {
        Clean-Application
    }
    "test" {
        Test-Application
    }
    default {
        Write-Info "Usage: .\docker-build.ps1 -Action <action> [-Force] [-Verbose]"
        Write-Info "Actions: build, start, stop, restart, logs, clean, dev, prod, test"
    }
}
