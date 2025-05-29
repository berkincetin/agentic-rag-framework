#!/bin/bash
# Remote Deployment Script for Agentic RAG System
# Atlas University, Istanbul, Türkiye
# Bu script başka bir bilgisayarda Agentic RAG sistemini kurmak için kullanılır

set -e

# Renkler
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonksiyonlar
log_success() { echo -e "${GREEN}✓ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠ $1${NC}"; }
log_error() { echo -e "${RED}✗ $1${NC}"; }
log_info() { echo -e "${BLUE}ℹ $1${NC}"; }

# Parametreler
DOCKER_HUB_USERNAME=""
IMAGE_TAG="latest"
SKIP_BUILD=false

# Parametre parsing
while [[ $# -gt 0 ]]; do
    case $1 in
        -u|--username)
            DOCKER_HUB_USERNAME="$2"
            shift 2
            ;;
        -t|--tag)
            IMAGE_TAG="$2"
            shift 2
            ;;
        -s|--skip-build)
            SKIP_BUILD=true
            shift
            ;;
        -h|--help)
            echo "Kullanım:"
            echo ""
            echo "1. Image'ı Docker Hub'a push etmek için:"
            echo "   $0 -u yourusername"
            echo ""
            echo "2. Başka bilgisayarda çalıştırmak için:"
            echo "   $0 -u yourusername --skip-build"
            echo ""
            echo "3. Farklı tag kullanmak için:"
            echo "   $0 -u yourusername -t v1.0"
            exit 0
            ;;
        *)
            log_error "Bilinmeyen parametre: $1"
            exit 1
            ;;
    esac
done

log_info "Agentic RAG Remote Deployment Script"
log_info "Atlas University, Istanbul, Türkiye"
echo ""

# Docker kontrolü
if ! command -v docker &> /dev/null; then
    log_error "Docker yüklü değil!"
    log_info "Docker'ı şu adresten indirin: https://docs.docker.com/get-docker/"
    exit 1
fi

docker_version=$(docker --version)
log_success "Docker bulundu: $docker_version"

# Docker Compose kontrolü
if ! command -v docker-compose &> /dev/null; then
    log_error "Docker Compose yüklü değil!"
    log_info "Docker Compose'u şu adresten indirin: https://docs.docker.com/compose/install/"
    exit 1
fi

compose_version=$(docker-compose --version)
log_success "Docker Compose bulundu: $compose_version"

# Eğer Docker Hub username verilmişse ve build skip edilmemişse, image'ı push et
if [[ -n "$DOCKER_HUB_USERNAME" && "$SKIP_BUILD" == false ]]; then
    log_info "Docker Hub'a image push ediliyor..."
    
    # Docker Hub'a login
    log_info "Docker Hub'a login olun:"
    docker login
    
    # Image'ı tag'le
    image_name="${DOCKER_HUB_USERNAME}/agentic-rag:${IMAGE_TAG}"
    log_info "Image tag'leniyor: $image_name"
    docker tag agenticrag-agentic-rag:latest "$image_name"
    
    # Push et
    log_info "Image Docker Hub'a push ediliyor..."
    docker push "$image_name"
    
    log_success "Image başarıyla push edildi: $image_name"
    echo ""
    log_info "Başka bilgisayarda çalıştırmak için:"
    log_info "1. Bu script'i çalıştırın: $0 -u $DOCKER_HUB_USERNAME --skip-build"
    log_info "2. Veya manuel olarak:"
    log_info "   git clone <your-repo>"
    log_info "   cd agentic-rag"
    log_info "   # .env dosyasını oluşturun"
    log_info "   docker-compose pull"
    log_info "   docker-compose up -d"
fi

# Eğer SkipBuild flag'i varsa, image'ı pull et ve çalıştır
if [[ "$SKIP_BUILD" == true ]]; then
    if [[ -z "$DOCKER_HUB_USERNAME" ]]; then
        log_error "SkipBuild kullanırken username gerekli!"
        exit 1
    fi
    
    image_name="${DOCKER_HUB_USERNAME}/agentic-rag:${IMAGE_TAG}"
    
    # docker-compose.yml'yi güncelle
    log_info "docker-compose.yml güncelleniyor..."
    
    # Backup oluştur
    cp docker-compose.yml docker-compose.yml.backup
    
    # Build kısımlarını comment out et ve image ekle
    sed -i.tmp '
        /build:/s/^/# /
        /context:/s/^/# /
        /dockerfile:/s/^/# /
        /target:/s/^/# /
    ' docker-compose.yml
    
    # Image satırını ekle (agentic-rag service'inin altına)
    sed -i.tmp "/agentic-rag:/a\\
    image: $image_name" docker-compose.yml
    
    # Geçici dosyayı temizle
    rm -f docker-compose.yml.tmp
    
    log_success "docker-compose.yml güncellendi"
    
    # .env dosyası kontrolü
    if [[ ! -f ".env" ]]; then
        log_warning ".env dosyası bulunamadı!"
        log_info "Örnek .env dosyası oluşturuluyor..."
        
        cat > .env << EOF
# API Keys - LÜTFEN GERÇEK DEĞERLERLE DEĞİŞTİRİN
OPENAI_API_KEY=your_openai_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=false
LOG_LEVEL=INFO
EOF
        
        log_warning "LÜTFEN .env dosyasını gerçek API key'lerinizle güncelleyin!"
        log_info "Dosya konumu: $(pwd)/.env"
        
        # Kullanıcıdan onay al
        read -p "API key'leri güncellediniz mi? (y/N): " response
        if [[ "$response" != "y" && "$response" != "Y" ]]; then
            log_warning "Lütfen önce API key'leri güncelleyin, sonra tekrar çalıştırın."
            exit 0
        fi
    fi
    
    # Image'ı pull et
    log_info "Docker image'ı çekiliyor..."
    docker pull "$image_name"
    
    # Servisleri başlat
    log_info "Servisler başlatılıyor..."
    docker-compose up -d
    
    log_success "Agentic RAG sistemi başarıyla başlatıldı!"
    echo ""
    log_info "Erişim adresleri:"
    log_info "• API: http://localhost:8000"
    log_info "• API Dokümantasyonu: http://localhost:8000/docs"
    log_info "• Gradio UI: http://localhost:7860"
    log_info "• MongoDB Express: http://localhost:8081"
    echo ""
    log_info "Logları görmek için: docker-compose logs -f"
    log_info "Durdurmak için: docker-compose down"
    log_info "Backup'ı geri yüklemek için: mv docker-compose.yml.backup docker-compose.yml"
fi

# Eğer hiçbir parametre verilmemişse, yardım göster
if [[ -z "$DOCKER_HUB_USERNAME" && "$SKIP_BUILD" == false ]]; then
    log_info "Kullanım:"
    echo ""
    log_info "1. Image'ı Docker Hub'a push etmek için:"
    log_info "   $0 -u yourusername"
    echo ""
    log_info "2. Başka bilgisayarda çalıştırmak için:"
    log_info "   $0 -u yourusername --skip-build"
    echo ""
    log_info "3. Farklı tag kullanmak için:"
    log_info "   $0 -u yourusername -t v1.0"
    echo ""
    log_info "Yardım için: $0 --help"
fi
