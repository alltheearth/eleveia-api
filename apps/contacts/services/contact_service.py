# apps/contacts/services/contact_service.py
from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Dict, Any
from ..models import Contato
from ..validators import ContatoValidator


class ContatoService:
    """
    Responsável por ESCRITA e lógica de negócio.
    Toda operação que modifica dados passa por aqui.
    """

    @staticmethod
    @transaction.atomic
    def criar_contato(data: Dict[str, Any]) -> Contato:
        """
        Cria um novo contato com validações de negócio.

        Args:
            data: Dicionário com dados do contato

        Returns:
            Contato criado

        Raises:
            ValidationError: Se dados inválidos
        """
        # Validação de negócio
        ContatoValidator.validar_email_unico(data.get('email'))
        ContatoValidator.validar_telefone(data.get('telefone'))

        # Criação do contato
        contato = Contato.objects.create(**data)

        # Lógica adicional (ex: enviar email, criar log, etc)
        ContatoService._enviar_email_boas_vindas(contato)
        ContatoService._criar_log_auditoria('CONTATO_CRIADO', contato)

        return contato

    @staticmethod
    @transaction.atomic
    def atualizar_contato(contato_id: int, data: Dict[str, Any]) -> Contato:
        """Atualiza um contato existente."""
        try:
            contato = Contato.objects.get(id=contato_id)
        except Contato.DoesNotExist:
            raise ValidationError("Contato não encontrado")

        # Atualizar campos
        for field, value in data.items():
            setattr(contato, field, value)

        contato.full_clean()  # Validação Django
        contato.save()

        return contato

    @staticmethod
    def _enviar_email_boas_vindas(contato: Contato) -> None:
        """Método privado para enviar email."""
        # Lógica de envio de email
        pass

    @staticmethod
    def _criar_log_auditoria(acao: str, contato: Contato) -> None:
        """Método privado para auditoria."""
        # Lógica de auditoria
        pass