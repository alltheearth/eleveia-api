# 🐳 Docker Quick Start - EleveIA

## 🚀 Início Rápido (3 comandos)

```bash
# 1. Configurar
cp .env.docker .env

# 2. Tornar script executável
chmod +x docker-manager.sh

# 3. Iniciar tudo
./docker-manager.sh start
```

**Pronto!** Acesse: http://localhost:8000/api/v1/

---

## 📋 Comandos Principais

```bash
./docker-manager.sh start              # Inicia tudo (recomendado na 1ª vez)
./docker-manager.sh start-simple       # Inicia sem migrations (uso diário)
./docker-manager.sh stop               # Para containers
./docker-manager.sh logs-web           # Ver logs
./docker-manager.sh shell              # Django shell
./docker-manager.sh createsuperuser    # Criar admin
./docker-manager.sh test               # Rodar testes
./docker-manager.sh help               # Ver todos os comandos
```

---

## 🎯 URLs Importantes

- **API**: http://localhost:8000/api/v1/
- **Admin**: http://localhost:8000/admin/
- **Swagger**: http://localhost:8000/api/v1/docs/
- **PostgreSQL**: localhost:5432

---

## 🔧 Comandos Docker Diretos

Se preferir usar Docker Compose diretamente:

```bash
# Start
docker-compose up -d --build

# Stop
docker-compose down

# Logs
docker-compose logs -f web

# Migrations
docker-compose exec web python manage.py migrate

# Shell
docker-compose exec web python manage.py shell

# Criar superuser
docker-compose exec web python manage.py createsuperuser
```

---

## 📊 Escolher Banco de Dados

### Opção 1: PostgreSQL Local (Docker) ✅ Recomendado

Já está configurado por padrão. Apenas rode:

```bash
./docker-manager.sh start
```

### Opção 2: Supabase (Externo)

1. Edite `.env`:
```bash
DB_HOST=aws-1-sa-east-1.pooler.supabase.com
DB_PORT=6543
DB_USER=postgres.ljeratmjitkxleakbywv
DB_PASSWORD=5ri*jPJuK@4jXK!
```

2. Edite `docker-compose.yml` e adicione ao serviço `db`:
```yaml
profiles: ["local-db"]
```

3. Inicie apenas o web:
```bash
docker-compose up web -d --build
```

---

## 🛠 Troubleshooting Rápido

### Erro: "Port already in use"
```bash
# Parar PostgreSQL local
sudo systemctl stop postgresql

# OU mudar porta no docker-compose.yml
ports:
  - "5433:5432"
```

### Migrations não aplicadas
```bash
./docker-manager.sh migrate
```

### Limpar tudo e começar do zero
```bash
./docker-manager.sh clean  # ⚠️ Apaga TUDO
./docker-manager.sh start
```

---

## 📖 Documentação Completa

Ver `DOCKER-GUIDE.md` para documentação detalhada.

---

## 🎯 Próximos Passos

1. ✅ Rodar `./docker-manager.sh start`
2. ✅ Criar superuser: `./docker-manager.sh createsuperuser`
3. ✅ Acessar admin: http://localhost:8000/admin/
4. ✅ Testar API: http://localhost:8000/api/v1/docs/
5. ✅ Desenvolver! 🚀

---

**Stack**: Docker | PostgreSQL 16 | Django 5.2 | DRF  
**Porta API**: 8000  
**Porta DB**: 5432