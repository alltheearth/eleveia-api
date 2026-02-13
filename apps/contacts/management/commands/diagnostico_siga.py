"""
Script de Diagnóstico - Integração SIGA
========================================

Este script testa a integração com a API SIGA e identifica problemas.

COMO USAR:
    python manage.py shell < diagnostico_siga.py

OU:
    python manage.py shell
    >>> exec(open('diagnostico_siga.py').read())
"""

import requests
from django.contrib.auth.models import User
from apps.schools.models import School
from django.core.cache import cache
from django.utils import timezone

print("\n" + "=" * 70)
print("🔍 DIAGNÓSTICO - INTEGRAÇÃO SIGA")
print("=" * 70 + "\n")

# ========================================
# 1. VERIFICAR CONFIGURAÇÃO
# ========================================
print("1️⃣ VERIFICANDO CONFIGURAÇÃO\n")

try:
    # Pegar primeiro usuário com perfil
    user = User.objects.filter(id=3).first()

    if not user:
        print("❌ ERRO: Nenhum usuário com perfil encontrado!")
        print("   Crie um usuário com perfil antes de continuar.\n")
        exit()

    print(f"✓ Usuário: {user.username}")

    school = user.profile.school

    if not school:
        print("❌ ERRO: Usuário sem escola vinculada!")
        print("   Vincule o usuário a uma escola antes de continuar.\n")
        exit()

    print(f"✓ Escola: {school.school_name} (ID: {school.id})")

    token = school.application_token

    if not token or token.strip() == "":
        print("❌ ERRO CRÍTICO: Escola sem application_token configurado!")
        print("\n   SOLUÇÃO:")
        print("   1. Acesse o Django Admin")
        print("   2. Vá em Schools > Sua Escola")
        print("   3. Preencha o campo 'Token da Aplicação (SIGA)'")
        print("   4. Salve\n")
        exit()

    print(f"✓ Token: Configurado ({len(token)} caracteres)")
    print()

except Exception as e:
    print(f"❌ ERRO ao verificar configuração: {e}\n")
    exit()

# ========================================
# 2. TESTAR CONEXÃO COM SIGA
# ========================================
print("2️⃣ TESTANDO CONEXÃO COM SIGA\n")

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

print("   Endpoint: https://siga.activesoft.com.br/api/v0/lista_alunos_dados_sensiveis/")

try:
    response = requests.get(
        "https://siga.activesoft.com.br/api/v0/lista_alunos_dados_sensiveis/",
        headers=headers,
        timeout=30
    )

    print(f"   Status: {response.status_code}")

    if response.status_code == 401:
        print("   ❌ ERRO 401: Token inválido ou expirado!")
        print("\n   SOLUÇÃO:")
        print("   1. Verifique se o token está correto")
        print("   2. Solicite um novo token ao SIGA")
        print("   3. Atualize o campo 'application_token' no admin\n")
        exit()

    elif response.status_code == 403:
        print("   ❌ ERRO 403: Token sem permissão!")
        print("\n   SOLUÇÃO:")
        print("   1. Verifique as permissões do token no SIGA")
        print("   2. Solicite um token com permissões adequadas\n")
        exit()

    elif response.status_code != 200:
        print(f"   ❌ ERRO {response.status_code}: {response.text}")
        exit()

    print("   ✓ Conexão OK\n")

except requests.exceptions.Timeout:
    print("   ❌ ERRO: Timeout na conexão com SIGA")
    print("   A requisição demorou mais de 30 segundos.\n")
    exit()

except requests.exceptions.ConnectionError:
    print("   ❌ ERRO: Não foi possível conectar ao SIGA")
    print("   Verifique sua conexão com a internet.\n")
    exit()

except Exception as e:
    print(f"   ❌ ERRO inesperado: {e}\n")
    exit()

# ========================================
# 3. VERIFICAR ALUNOS
# ========================================
print("3️⃣ VERIFICANDO ALUNOS\n")

try:
    data = response.json()

    # Suporta diferentes formatos de resposta
    if isinstance(data, list):
        students = data
    elif isinstance(data, dict):
        students = data.get('results', [])
    else:
        print(f"   ❌ ERRO: Formato de resposta inesperado: {type(data)}\n")
        exit()

    print(f"   ✓ Total de alunos: {len(students)}")

    if len(students) == 0:
        print("\n   ⚠️ ATENÇÃO: Nenhum aluno encontrado!")
        print("   Possíveis causas:")
        print("   1. Escola não tem alunos cadastrados no SIGA")
        print("   2. Token sem permissão para ver alunos")
        print("   3. Filtro de período/status na API\n")
        exit()

    # Mostrar alguns alunos de exemplo
    print(f"\n   Exemplos de alunos:")
    for i, student in enumerate(students[:5], 1):
        name = student.get('nome', 'N/A')
        student_id = student.get('id', 'N/A')
        registration = student.get('matricula', 'N/A')
        print(f"   [{i}] {name[:40]:<40} ID: {student_id:<6} Matrícula: {registration}")

    if len(students) > 5:
        print(f"   ... e mais {len(students) - 5} alunos")

    print()

except Exception as e:
    print(f"   ❌ ERRO ao processar alunos: {e}\n")
    exit()

# ========================================
# 4. TESTAR BOLETOS
# ========================================
print("4️⃣ TESTANDO BOLETOS (primeiros 10 alunos)\n")

students_with_invoices = 0
students_without_invoices = 0
total_invoices = 0
errors = 0

print(f"   {'Aluno':<40} {'Boletos':<10} {'Status'}")
print("   " + "-" * 60)

for i, student in enumerate(students[:10], 1):
    student_id = student.get('id')
    student_name = student.get('nome', 'N/A')

    if not student_id:
        print(f"   [{i:2d}] {student_name[:40]:<40} {'N/A':<10} ❌ Sem ID")
        errors += 1
        continue

    try:
        r = requests.get(
            "https://siga.activesoft.com.br/api/v0/informacoes_boleto/",
            headers=headers,
            params={'id_aluno': student_id},
            timeout=10
        )

        if r.status_code == 200:
            data = r.json()
            invoices = data.get('resultados', [])
            num_invoices = len(invoices)

            if num_invoices > 0:
                students_with_invoices += 1
                total_invoices += num_invoices

                # Verificar status dos boletos
                paid = sum(1 for inv in invoices if inv.get('situacao_titulo') == 'LIQ')
                pending = num_invoices - paid

                status_text = f"✓ ({paid} pagos, {pending} pendentes)"
                print(f"   [{i:2d}] {student_name[:40]:<40} {num_invoices:<10} {status_text}")
            else:
                students_without_invoices += 1
                print(f"   [{i:2d}] {student_name[:40]:<40} {0:<10} ⚠️ Sem boletos")
        else:
            errors += 1
            print(f"   [{i:2d}] {student_name[:40]:<40} {'ERRO':<10} ❌ Status {r.status_code}")

    except requests.exceptions.Timeout:
        errors += 1
        print(f"   [{i:2d}] {student_name[:40]:<40} {'TIMEOUT':<10} ⏱️")

    except Exception as e:
        errors += 1
        print(f"   [{i:2d}] {student_name[:40]:<40} {'ERRO':<10} ❌ {str(e)[:20]}")

# ========================================
# 5. RESUMO E DIAGNÓSTICO
# ========================================
print("\n" + "=" * 70)
print("📊 RESUMO DO DIAGNÓSTICO")
print("=" * 70 + "\n")

print(f"Total de alunos no SIGA: {len(students)}")
print(f"Alunos testados: 10")
print(f"  • Com boletos: {students_with_invoices}")
print(f"  • Sem boletos: {students_without_invoices}")
print(f"  • Erros: {errors}")
print(f"Total de boletos: {total_invoices}")

if total_invoices > 0:
    avg_invoices = total_invoices / students_with_invoices if students_with_invoices > 0 else 0
    print(f"Média de boletos por aluno: {avg_invoices:.1f}")

# ========================================
# 6. VERIFICAR CACHE
# ========================================
print("\n" + "=" * 70)
print("💾 CACHE")
print("=" * 70 + "\n")

cache_key = f"all_invoices_school_{school.id}"
cached_data = cache.get(cache_key)

if cached_data:
    print(f"✓ Dados em cache encontrados")
    print(f"  • Total de alunos: {cached_data['summary']['total_students']}")
    print(f"  • Total de boletos: {cached_data['summary']['total_invoices']}")
    print(f"  • Última atualização: {cached_data['last_updated']}")
    print(f"\n  ⚠️ Para forçar atualização, execute:")
    print(f"     cache.delete('{cache_key}')")
else:
    print("  Sem dados em cache")

# ========================================
# 7. DIAGNÓSTICO FINAL
# ========================================
print("\n" + "=" * 70)
print("🎯 DIAGNÓSTICO FINAL")
print("=" * 70 + "\n")

if students_with_invoices == 0 and students_without_invoices > 0:
    print("❌ PROBLEMA IDENTIFICADO: Nenhum aluno possui boletos!\n")
    print("Possíveis causas:")
    print("1. Boletos não cadastrados no SIGA para esses alunos")
    print("2. Filtro de período/ano na API do SIGA")
    print("3. Boletos em outro sistema/módulo do SIGA")
    print("\nSolução:")
    print("• Verifique no SIGA web se esses alunos têm boletos cadastrados")
    print("• Contate o suporte do SIGA para verificar configurações da API")

elif students_with_invoices > 0:
    print("✅ INTEGRAÇÃO FUNCIONANDO!\n")
    print(f"A API retornou {total_invoices} boletos de {students_with_invoices} alunos.")
    print("\nSe a rota está retornando vazio:")
    print("1. Limpe o cache: cache.clear()")
    print("2. Substitua a view pela versão corrigida")
    print("3. Teste novamente a rota")

elif errors > 0:
    print("⚠️ PROBLEMAS DE CONECTIVIDADE\n")
    print(f"Ocorreram {errors} erros ao buscar boletos.")
    print("\nPossíveis causas:")
    print("• Conexão instável com SIGA")
    print("• Token com rate limit atingido")
    print("• Problemas temporários no servidor SIGA")

else:
    print("⚠️ DIAGNÓSTICO INCONCLUSIVO\n")
    print("Não foi possível determinar o problema.")
    print("Execute novamente ou contate o suporte.")

print("\n" + "=" * 70 + "\n")