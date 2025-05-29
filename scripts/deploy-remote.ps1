# Remote Deployment Script for Agentic RAG System
# Atlas University, Istanbul, Türkiye
# Bu script başka bir bilgisayarda Agentic RAG sistemini kurmak için kullanılır

param(
    [Parameter(Mandatory=$false)]
    [string]$DockerHubUsername = "",
    
    [Parameter(Mandatory=$false)]
    [string]$ImageTag = "latest",
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipBuild
)

# Renkli çıktı için
$Green = "`e[32m"
$Yellow = "`e[33m"
$Red = "`e[31m"
$Blue = "`e[34m"
$Reset = "`e[0m"

function Write-Success { param([string]$Message); Write-Host "${Green}✓ $Message${Reset}" }
function Write-Warning { param([string]$Message); Write-Host "${Yellow}⚠ $Message${Reset}" }
function Write-Error { param([string]$Message); Write-Host "${Red}✗ $Message${Reset}" }
function Write-Info { param([string]$Message); Write-Host "${Blue}ℹ $Message${Reset}" }

Write-Info "Agentic RAG Remote Deployment Script"
Write-Info "Atlas University, Istanbul, Türkiye"
Write-Info ""

# Docker kontrolü
try {
    $dockerVersion = docker --version
    Write-Success "Docker bulundu: $dockerVersion"
} catch {
    Write-Error "Docker yüklü değil!"
    Write-Info "Docker Desktop'ı şu adresten indirin: https://docs.docker.com/desktop/"
    exit 1
}

# Docker Compose kontrolü
try {
    $composeVersion = docker-compose --version
    Write-Success "Docker Compose bulundu: $composeVersion"
} catch {
    Write-Error "Docker Compose yüklü değil!"
    exit 1
}

# Eğer Docker Hub username verilmişse, image'ı push et
if ($DockerHubUsername -and -not $SkipBuild) {
    Write-Info "Docker Hub'a image push ediliyor..."
    
    # Docker Hub'a login
    Write-Info "Docker Hub'a login olun:"
    docker login
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Docker Hub login başarısız!"
        exit 1
    }
    
    # Image'ı tag'le
    $imageName = "${DockerHubUsername}/agentic-rag:${ImageTag}"
    Write-Info "Image tag'leniyor: $imageName"
    docker tag agenticrag-agentic-rag:latest $imageName
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Image tag'leme başarısız!"
        exit 1
    }
    
    # Push et
    Write-Info "Image Docker Hub'a push ediliyor..."
    docker push $imageName
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Image başarıyla push edildi: $imageName"
        Write-Info ""
        Write-Info "Başka bilgisayarda çalıştırmak için:"
        Write-Info "1. Bu script'i çalıştırın: .\deploy-remote.ps1 -DockerHubUsername $DockerHubUsername -SkipBuild"
        Write-Info "2. Veya manuel olarak:"
        Write-Info "   git clone <your-repo>"
        Write-Info "   cd agentic-rag"
        Write-Info "   # .env dosyasını oluşturun"
        Write-Info "   docker-compose pull"
        Write-Info "   docker-compose up -d"
    } else {
        Write-Error "Image push başarısız!"
        exit 1
    }
}

# Eğer SkipBuild flag'i varsa, image'ı pull et ve çalıştır
if ($SkipBuild) {
    if (-not $DockerHubUsername) {
        Write-Error "SkipBuild kullanırken DockerHubUsername gerekli!"
        exit 1
    }
    
    $imageName = "${DockerHubUsername}/agentic-rag:${ImageTag}"
    
    # docker-compose.yml'yi güncelle
    Write-Info "docker-compose.yml güncelleniyor..."
    
    $composeContent = Get-Content "docker-compose.yml" -Raw
    $composeContent = $composeContent -replace "build:", "# build:"
    $composeContent = $composeContent -replace "context: \.", "# context: ."
    $composeContent = $composeContent -replace "dockerfile: Dockerfile", "# dockerfile: Dockerfile"
    $composeContent = $composeContent -replace "target: production", "# target: production"
    
    # Image satırını ekle
    $composeContent = $composeContent -replace "(agentic-rag:[\s\S]*?)(container_name:)", "agentic-rag:`n    image: $imageName`n    `$2"
    
    $composeContent | Out-File "docker-compose.yml" -Encoding UTF8
    
    Write-Success "docker-compose.yml güncellendi"
    
    # .env dosyası kontrolü
    if (-not (Test-Path ".env")) {
        Write-Warning ".env dosyası bulunamadı!"
        Write-Info "Örnek .env dosyası oluşturuluyor..."
        
        $envContent = @"
# API Keys - LÜTFEN GERÇEK DEĞERLERLE DEĞİŞTİRİN
OPENAI_API_KEY=your_openai_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=false
LOG_LEVEL=INFO
"@
        $envContent | Out-File ".env" -Encoding UTF8
        Write-Warning "LÜTFEN .env dosyasını gerçek API key'lerinizle güncelleyin!"
        Write-Info "Dosya konumu: $(Get-Location)\.env"
        
        # Kullanıcıdan onay al
        $response = Read-Host "API key'leri güncellediniz mi? (y/N)"
        if ($response -ne "y" -and $response -ne "Y") {
            Write-Warning "Lütfen önce API key'leri güncelleyin, sonra tekrar çalıştırın."
            exit 0
        }
    }
    
    # Image'ı pull et
    Write-Info "Docker image'ı çekiliyor..."
    docker pull $imageName
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Image pull başarısız!"
        exit 1
    }
    
    # Servisleri başlat
    Write-Info "Servisler başlatılıyor..."
    docker-compose up -d
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Agentic RAG sistemi başarıyla başlatıldı!"
        Write-Info ""
        Write-Info "Erişim adresleri:"
        Write-Info "• API: http://localhost:8000"
        Write-Info "• API Dokümantasyonu: http://localhost:8000/docs"
        Write-Info "• Gradio UI: http://localhost:7860"
        Write-Info "• MongoDB Express: http://localhost:8081"
        Write-Info ""
        Write-Info "Logları görmek için: docker-compose logs -f"
        Write-Info "Durdurmak için: docker-compose down"
    } else {
        Write-Error "Servis başlatma başarısız!"
        exit 1
    }
}

# Eğer hiçbir parametre verilmemişse, yardım göster
if (-not $DockerHubUsername -and -not $SkipBuild) {
    Write-Info "Kullanım:"
    Write-Info ""
    Write-Info "1. Image'ı Docker Hub'a push etmek için:"
    Write-Info "   .\deploy-remote.ps1 -DockerHubUsername 'yourusername'"
    Write-Info ""
    Write-Info "2. Başka bilgisayarda çalıştırmak için:"
    Write-Info "   .\deploy-remote.ps1 -DockerHubUsername 'yourusername' -SkipBuild"
    Write-Info ""
    Write-Info "3. Farklı tag kullanmak için:"
    Write-Info "   .\deploy-remote.ps1 -DockerHubUsername 'yourusername' -ImageTag 'v1.0'"
}
