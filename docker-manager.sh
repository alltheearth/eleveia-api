# ===================================================================
# EleveIA - Docker Manager (Windows PowerShell)
# ===================================================================

param(
    [Parameter(Position=0)]
    [string]$Command = "help"
)

# Cores
function Write-Success { param($msg) Write-Host "✅ $msg" -ForegroundColor Green }
function Write-Error { param($msg) Write-Host "❌ $msg" -ForegroundColor Red }
function Write-Warning { param($msg) Write-Host "⚠️  $msg" -ForegroundColor Yellow }
function Write-Info { param($msg) Write-Host "ℹ️  $msg" -ForegroundColor Cyan }

function Show-Header {
    Write-Host "╔════════════════════════════════════════╗" -ForegroundColor Blue
    Write-Host "║  EleveIA - Docker Manager (Windows)   ║" -ForegroundColor Blue
    Write-Host "╚════════════════════════════════════════╝" -ForegroundColor Blue
    Write-Host ""
}

# ===================================================================
# COMANDOS
# ===================================================================

function Start-Full {
    Show-Header
    Write-Info "Iniciando EleveIA (setup completo)..."

    # Verificar .env
    if (-not (Test-Path .env)) {
        Write-Warning ".env não encontrado!"
        if (Test-Path .env.docker) {
            Copy-Item .env.docker .env
            Write-Success ".env criado com sucesso"
        } else {
            Write-Error "Arquivo .env.docker não encontrado!"
            return
        }
    }

    Write-Info "Parando containers antigos..."
    docker-compose down

    Write-Info "Iniciando containers..."
    docker-compose up -d --build

    Write-Info "Aguardando PostgreSQL (15 segundos)..."
    Start-Sleep -Seconds 15

    Write-Info "Executando migrations..."
    docker-compose exec web python manage.py migrate

    Write-Info "Coletando arquivos estáticos..."
    docker-compose exec web python manage.py collectstatic --noinput

    Write-Success "EleveIA iniciado com sucesso!"
    Write-Host ""
    Write-Info "📍 API: http://localhost:8000/api/v1/"
    Write-Info "📍 Admin: http://localhost:8000/admin/"
    Write-Info "📍 Docs: http://localhost:8000/api/v1/docs/"
}

function Start-Simple {
    Show-Header
    Write-Info "Iniciando containers..."
    docker-compose up -d
    Write-Success "Containers iniciados!"
}

function Stop-All {
    Show-Header
    Write-Info "Parando containers..."
    docker-compose stop
    Write-Success "Containers parados!"
}

function Restart-All {
    Show-Header
    Write-Info "Reiniciando containers..."
    docker-compose restart
    Write-Success "Containers reiniciados!"
}

function Remove-All {
    Show-Header
    Write-Warning "Removendo containers..."
    docker-compose down
    Write-Success "Containers removidos!"
}

function Remove-Volumes {
    Show-Header
    Write-Error "⚠️  ATENÇÃO: Isso vai APAGAR o banco de dados local!"
    $confirmation = Read-Host "Tem certeza? (y/N)"
    if ($confirmation -eq 'y' -or $confirmation -eq 'Y') {
        docker-compose down -v
        Write-Success "Containers e volumes removidos!"
    } else {
        Write-Info "Operação cancelada"
    }
}

function Show-Logs {
    docker-compose logs -f
}

function Show-LogsWeb {
    docker-compose logs -f web
}

function Show-LogsDb {
    docker-compose logs -f db
}

function Open-Shell {
    docker-compose exec web python manage.py shell
}

function Open-Bash {
    docker-compose exec web bash
}

function Run-Migrations {
    Write-Info "Criando migrations..."
    docker-compose exec web python manage.py makemigrations

    Write-Info "Aplicando migrations..."
    docker-compose exec web python manage.py migrate

    Write-Success "Migrations aplicadas!"
}

function Create-Superuser {
    docker-compose exec web python manage.py createsuperuser
}

function Run-Tests {
    Write-Info "Executando testes..."
    docker-compose exec web pytest
}

function Run-TestsCoverage {
    Write-Info "Executando testes com coverage..."
    docker-compose exec web pytest --cov --cov-report=html
    Write-Success "Coverage report gerado em htmlcov/"
}

function Show-Status {
    Show-Header
    docker-compose ps
}

function Create-Backup {
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupFile = "backup_$timestamp.sql"
    Write-Info "Criando backup: $backupFile"
    docker-compose exec -T db pg_dump -U postgres postgres > $backupFile
    Write-Success "Backup criado: $backupFile"
}

function Restore-Backup {
    param([string]$file)

    if (-not $file) {
        Write-Error "Uso: .\docker-manager.ps1 restore <arquivo.sql>"
        return
    }

    if (-not (Test-Path $file)) {
        Write-Error "Arquivo não encontrado: $file"
        return
    }

    Write-Warning "⚠️  Isso vai SUBSTITUIR o banco atual!"
    $confirmation = Read-Host "Tem certeza? (y/N)"
    if ($confirmation -eq 'y' -or $confirmation -eq 'Y') {
        Get-Content $file | docker-compose exec -T db psql -U postgres postgres
        Write-Success "Restore concluído!"
    } else {
        Write-Info "Operação cancelada"
    }
}

function Clean-All {
    Show-Header
    Write-Error "⚠️  ATENÇÃO: Isso vai remover TODOS containers, volumes e imagens!"
    $confirmation = Read-Host "Tem certeza? (y/N)"
    if ($confirmation -eq 'y' -or $confirmation -eq 'Y') {
        docker-compose down -v
        docker system prune -a --volumes -f
        Write-Success "Limpeza concluída!"
    } else {
        Write-Info "Operação cancelada"
    }
}

function Show-Help {
    Show-Header
    Write-Host "Uso: .\docker-manager.ps1 [comando]" -ForegroundColor White
    Write-Host ""
    Write-Host "Comandos disponíveis:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  start              - Inicia tudo (build + migrate + collectstatic)" -ForegroundColor Cyan
    Write-Host "  start-simple       - Inicia containers sem migrations" -ForegroundColor Cyan
    Write-Host "  stop               - Para containers" -ForegroundColor Cyan
    Write-Host "  restart            - Reinicia containers" -ForegroundColor Cyan
    Write-Host "  down               - Remove containers" -ForegroundColor Cyan
    Write-Host "  down-volumes       - Remove containers + volumes (⚠️ APAGA BANCO)" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  logs               - Ver todos os logs" -ForegroundColor Cyan
    Write-Host "  logs-web           - Ver logs do Django" -ForegroundColor Cyan
    Write-Host "  logs-db            - Ver logs do PostgreSQL" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  shell              - Django shell" -ForegroundColor Cyan
    Write-Host "  bash               - Bash no container" -ForegroundColor Cyan
    Write-Host "  migrate            - Executar migrations" -ForegroundColor Cyan
    Write-Host "  createsuperuser    - Criar superusuário" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  test               - Executar testes" -ForegroundColor Cyan
    Write-Host "  test-coverage      - Testes com coverage" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  status             - Status dos containers" -ForegroundColor Cyan
    Write-Host "  backup             - Backup do banco" -ForegroundColor Cyan
    Write-Host "  restore <file>     - Restore do banco" -ForegroundColor Cyan
    Write-Host "  clean              - Limpar tudo (⚠️ PERIGOSO)" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  help               - Mostra esta ajuda" -ForegroundColor Cyan
    Write-Host ""
}

# ===================================================================
# MAIN
# ===================================================================

switch ($Command) {
    "start" { Start-Full }
    "start-simple" { Start-Simple }
    "stop" { Stop-All }
    "restart" { Restart-All }
    "down" { Remove-All }
    "down-volumes" { Remove-Volumes }
    "logs" { Show-Logs }
    "logs-web" { Show-LogsWeb }
    "logs-db" { Show-LogsDb }
    "shell" { Open-Shell }
    "bash" { Open-Bash }
    "migrate" { Run-Migrations }
    "createsuperuser" { Create-Superuser }
    "test" { Run-Tests }
    "test-coverage" { Run-TestsCoverage }
    "status" { Show-Status }
    "backup" { Create-Backup }
    "restore" { Restore-Backup -file $args[0] }
    "clean" { Clean-All }
    "help" { Show-Help }
    default {
        Write-Error "Comando desconhecido: $Command"
        Write-Host ""
        Show-Help
    }
}