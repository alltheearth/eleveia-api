# apps/contacts/services.py
from django.utils import timezone
from typing import Dict, Any
from .models import Contato


class ContatoService:
    """Serviço para lógica de negócio de Contatos"""

    @staticmethod
    def registrar_interacao(contato: Contato) -> Contato:
        """
        Registra uma nova interação com o contato

        Args:
            contato: Instância do contato

        Returns:
            Contato atualizado
        """
        contato.ultima_interacao = timezone.now()
        contato.save(update_fields=['ultima_interacao', 'atualizado_em'])
        return contato

    @staticmethod
    def calcular_estatisticas(escola_id: int) -> Dict[str, Any]:
        """
        Calcula estatísticas de contatos da escola

        Args:
            escola_id: ID da escola

        Returns:
            Dicionário com estatísticas
        """
        from django.db.models import Count
        from datetime import timedelta

        hoje = timezone.now().date()
        sete_dias_atras = timezone.now() - timedelta(days=7)

        queryset = Contato.objects.filter(escola_id=escola_id)

        return {
            'total': queryset.count(),
            'ativos': queryset.filter(status='ativo').count(),
            'inativos': queryset.filter(status='inativo').count(),
            'por_origem': dict(
                queryset.values('origem')
                .annotate(total=Count('id'))
                .values_list('origem', 'total')
            ),
            'novos_hoje': queryset.filter(criado_em__date=hoje).count(),
            'interacoes_recentes': queryset.filter(
                ultima_interacao__gte=sete_dias_atras
            ).count()
        }

