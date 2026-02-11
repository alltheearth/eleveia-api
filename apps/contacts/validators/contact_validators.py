# apps/contacts/validators/contact_validators.py
from django.core.exceptions import ValidationError
from ..models import Contato
import re


class ContatoValidator:
    """Validações de negócio para Contatos."""

    @staticmethod
    def validar_email_unico(email: str) -> None:
        """
        Valida se o email já não está em uso.

        Raises:
            ValidationError: Se email já existe
        """
        if Contato.objects.filter(email=email).exists():
            raise ValidationError(f'Email {email} já está em uso.')

    @staticmethod
    def validar_telefone(telefone: str) -> None:
        """
        Valida formato de telefone brasileiro.

        Args:
            telefone: Telefone a validar

        Raises:
            ValidationError: Se telefone inválido
        """
        if not telefone:
            raise ValidationError('Telefone é obrigatório.')

        # Remove caracteres não numéricos
        apenas_numeros = re.sub(r'\D', '', telefone)

        # Valida se tem 10 ou 11 dígitos
        if len(apenas_numeros) not in [10, 11]:
            raise ValidationError(
                'Telefone deve ter 10 ou 11 dígitos (DDD + número).'
            )

    @staticmethod
    def validar_dados_completos(data: dict) -> None:
        """
        Valida se todos os dados obrigatórios estão presentes.

        Args:
            data: Dicionário com dados do contato

        Raises:
            ValidationError: Se faltam dados obrigatórios
        """
        campos_obrigatorios = ['nome', 'email', 'telefone']
        campos_faltantes = []

        for campo in campos_obrigatorios:
            if not data.get(campo):
                campos_faltantes.append(campo)

        if campos_faltantes:
            raise ValidationError(
                f'Campos obrigatórios faltando: {", ".join(campos_faltantes)}'
            )