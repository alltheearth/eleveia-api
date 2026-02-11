# apps/contacts/selectors/guardian_selector.py
from django.db.models import QuerySet, Prefetch, Count, Q
from ..models import Guardian, Student


class GuardianSelector:
    """Queries otimizadas para Guardian."""

    @staticmethod
    def get_all_ativos() -> QuerySet[Guardian]:
        """Retorna todos os guardians ativos com alunos."""
        return Guardian.objects.filter(
            ativo=True
        ).select_related(
            'contato'
        ).prefetch_related(
            Prefetch(
                'students',
                queryset=Student.objects.filter(ativo=True)
            )
        ).annotate(
            total_alunos=Count('students', filter=Q(students__ativo=True))
        )

    @staticmethod
    def get_by_cpf(cpf: str) -> Guardian | None:
        """Busca guardian por CPF."""
        cpf_limpo = cpf.replace('.', '').replace('-', '').strip()
        try:
            return Guardian.objects.get(cpf=cpf_limpo)
        except Guardian.DoesNotExist:
            return None

    @staticmethod
    def get_by_siga_id(siga_id: str) -> Guardian | None:
        """Busca guardian pelo ID do SIGA."""
        try:
            return Guardian.objects.select_related('contato').get(
                siga_id=siga_id
            )
        except Guardian.DoesNotExist:
            return None

    @staticmethod
    def get_guardians_com_alunos_ativos() -> QuerySet[Guardian]:
        """Retorna apenas guardians que tem alunos ativos."""
        return Guardian.objects.filter(
            ativo=True,
            students__ativo=True
        ).distinct().select_related(
            'contato'
        ).prefetch_related(
            'students'
        )