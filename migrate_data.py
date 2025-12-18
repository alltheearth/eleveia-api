"""
Script para migrar dados de eleveai_* para apps_*

Execute: python migrate_data.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection


def migrate_data():
    """Migra dados das tabelas antigas para novas"""

    with connection.cursor() as cursor:
        print("🔄 Iniciando migração de dados...\n")

        # 1. Migrar Escolas
        print("📋 Migrando Escolas...")
        try:
            cursor.execute("""
                INSERT INTO schools_escola 
                    (id, nome_escola, cnpj, token_mensagens, telefone, email, 
                     website, logo, cep, endereco, cidade, estado, complemento, 
                     sobre, niveis_ensino, criado_em, atualizado_em)
                SELECT 
                    id, nome_escola, cnpj, token_mensagens, telefone, email,
                    website, logo, cep, endereco, cidade, estado, complemento,
                    sobre, niveis_ensino, criado_em, atualizado_em
                FROM eleveai_escola
                WHERE id NOT IN (SELECT id FROM schools_escola)
            """)
            print(f"   ✅ {cursor.rowcount} escolas migradas")
        except Exception as e:
            print(f"   ⚠️  Erro: {e}")

        # 2. Migrar Perfis de Usuário
        print("\n📋 Migrando Perfis de Usuário...")
        try:
            cursor.execute("""
                INSERT INTO users_perfilusuario
                    (id, usuario_id, escola_id, tipo, ativo, criado_em, atualizado_em)
                SELECT 
                    id, usuario_id, escola_id, tipo, ativo, criado_em, atualizado_em
                FROM eleveai_perfilusuario
                WHERE id NOT IN (SELECT id FROM users_perfilusuario)
            """)
            print(f"   ✅ {cursor.rowcount} perfis migrados")
        except Exception as e:
            print(f"   ⚠️  Erro: {e}")

        # 3. Migrar Contatos
        print("\n📋 Migrando Contatos...")
        try:
            cursor.execute("""
                INSERT INTO contacts_contato
                    (id, usuario_id, escola_id, nome, email, telefone, 
                     data_nascimento, status, origem, ultima_interacao, 
                     observacoes, tags, criado_em, atualizado_em)
                SELECT 
                    id, usuario_id, escola_id, nome, email, telefone,
                    data_nascimento, status, origem, ultima_interacao,
                    observacoes, tags, criado_em, atualizado_em
                FROM eleveai_contato
                WHERE id NOT IN (SELECT id FROM contacts_contato)
            """)
            print(f"   ✅ {cursor.rowcount} contatos migrados")
        except Exception as e:
            print(f"   ⚠️  Erro: {e}")

        # 4. Migrar Eventos
        print("\n📋 Migrando Eventos...")
        try:
            cursor.execute("""
                INSERT INTO events_calendarioevento
                    (id, usuario_id, escola_id, data, evento, tipo, criado_em, atualizado_em)
                SELECT 
                    id, usuario_id, escola_id, data, evento, tipo, criado_em, atualizado_em
                FROM eleveai_calendarioevento
                WHERE id NOT IN (SELECT id FROM events_calendarioevento)
            """)
            print(f"   ✅ {cursor.rowcount} eventos migrados")
        except Exception as e:
            print(f"   ⚠️  Erro: {e}")

        # 5. Migrar FAQs
        print("\n📋 Migrando FAQs...")
        try:
            cursor.execute("""
                INSERT INTO faqs_faq
                    (id, usuario_id, escola_id, pergunta, resposta, 
                     categoria, status, criado_em, atualizado_em)
                SELECT 
                    id, usuario_id, escola_id, pergunta, resposta,
                    categoria, status, criado_em, atualizado_em
                FROM eleveai_faq
                WHERE id NOT IN (SELECT id FROM faqs_faq)
            """)
            print(f"   ✅ {cursor.rowcount} FAQs migradas")
        except Exception as e:
            print(f"   ⚠️  Erro: {e}")

        # 6. Migrar Documentos
        print("\n📋 Migrando Documentos...")
        try:
            cursor.execute("""
                INSERT INTO documents_documento
                    (id, usuario_id, escola_id, nome, arquivo, status, criado_em, atualizado_em)
                SELECT 
                    id, usuario_id, escola_id, nome, arquivo, status, criado_em, atualizado_em
                FROM eleveai_documento
                WHERE id NOT IN (SELECT id FROM documents_documento)
            """)
            print(f"   ✅ {cursor.rowcount} documentos migrados")
        except Exception as e:
            print(f"   ⚠️  Erro: {e}")

        # 7. Migrar Dashboard
        print("\n📋 Migrando Dashboard...")
        try:
            cursor.execute("""
                INSERT INTO dashboard_dashboard
                    (id, usuario_id, escola_id, status_agente, interacoes_hoje,
                     documentos_upload, faqs_criadas, leads_capturados,
                     taxa_resolucao, novos_hoje, atualizado_em)
                SELECT 
                    id, usuario_id, escola_id, status_agente, interacoes_hoje,
                    documentos_upload, faqs_criadas, leads_capturados,
                    taxa_resolucao, novos_hoje, atualizado_em
                FROM eleveai_dashboard
                WHERE id NOT IN (SELECT id FROM dashboard_dashboard)
            """)
            print(f"   ✅ {cursor.rowcount} dashboards migrados")
        except Exception as e:
            print(f"   ⚠️  Erro: {e}")

        # 8. Migrar Leads (se existir)
        print("\n📋 Migrando Leads...")
        try:
            cursor.execute("""
                INSERT INTO contacts_lead
                    (id, usuario_id, escola_id, nome, email, telefone,
                     status, origem, observacoes, interesses,
                     criado_em, atualizado_em, contatado_em, convertido_em)
                SELECT 
                    id, usuario_id, escola_id, nome, email, telefone,
                    status, origem, observacoes, interesses,
                    criado_em, atualizado_em, contatado_em, convertido_em
                FROM eleveai_lead
                WHERE id NOT IN (SELECT id FROM contacts_lead)
            """)
            print(f"   ✅ {cursor.rowcount} leads migrados")
        except Exception as e:
            print(f"   ⚠️  Erro: {e}")

        print("\n✅ Migração concluída!")
        print("\n⚠️  IMPORTANTE: Revise os dados migrados antes de deletar as tabelas antigas!")


if __name__ == '__main__':
    try:
        migrate_data()
    except Exception as e:
        print(f"\n❌ Erro na migração: {e}")
        import traceback

        traceback.print_exc()