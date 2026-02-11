# apps/contacts/models/guardian.py
from django.db import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError


class Guardian(models.Model):
    """
    Modelo de Responsável/Guardião.
    Representa o responsável legal por um ou mais estudantes.
    """

    # Choices
    class TipoRelacionamento(models.TextChoices):
        PAI = 'PAI', 'Pai'
        MAE = 'MAE', 'Mãe'
        AVO = 'AVO', 'Avô/Avó'
        TIO = 'TIO', 'Tio/Tia'
        RESPONSAVEL_LEGAL = 'RESP', 'Responsável Legal'
        OUTRO = 'OUTRO', 'Outro'

    # Validadores
    cpf_validator = RegexValidator(
        regex=r'^\d{11}$',
        message='CPF deve conter exatamente 11 dígitos numéricos'
    )

    telefone_validator = RegexValidator(
        regex=r'^\d{10,11}$',
        message='Telefone deve conter 10 ou 11 dígitos'
    )

    # Campos Principais
    nome_completo = models.CharField(
        max_length=200,
        verbose_name='Nome Completo',
        help_text='Nome completo do responsável'
    )

    cpf = models.CharField(
        max_length=11,
        unique=True,
        validators=[cpf_validator],
        verbose_name='CPF',
        help_text='CPF sem pontuação'
    )

    rg = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='RG',
        help_text='RG do responsável'
    )

    data_nascimento = models.DateField(
        blank=True,
        null=True,
        verbose_name='Data de Nascimento'
    )

    # Contato
    email = models.EmailField(
        unique=True,
        verbose_name='E-mail Principal',
        help_text='E-mail para comunicação oficial'
    )

    email_secundario = models.EmailField(
        blank=True,
        null=True,
        verbose_name='E-mail Secundário'
    )

    telefone_principal = models.CharField(
        max_length=11,
        validators=[telefone_validator],
        verbose_name='Telefone Principal',
        help_text='Telefone celular com DDD (apenas números)'
    )

    telefone_secundario = models.CharField(
        max_length=11,
        blank=True,
        null=True,
        validators=[telefone_validator],
        verbose_name='Telefone Secundário'
    )

    # Endereço
    cep = models.CharField(
        max_length=8,
        blank=True,
        null=True,
        verbose_name='CEP',
        help_text='CEP sem pontuação'
    )

    logradouro = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='Logradouro'
    )

    numero = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        verbose_name='Número'
    )

    complemento = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Complemento'
    )

    bairro = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Bairro'
    )

    cidade = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Cidade'
    )

    estado = models.CharField(
        max_length=2,
        blank=True,
        null=True,
        verbose_name='Estado',
        help_text='Sigla do estado (ex: SP, RJ)'
    )

    # Relacionamentos
    tipo_relacionamento = models.CharField(
        max_length=10,
        choices=TipoRelacionamento.choices,
        default=TipoRelacionamento.RESPONSAVEL_LEGAL,
        verbose_name='Tipo de Relacionamento'
    )

    # Relacionamento com Contato (se você tiver model Contato separado)
    contato = models.OneToOneField(
        'contacts.Contato',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='guardian',
        verbose_name='Contato Vinculado',
        help_text='Contato geral vinculado a este guardian'
    )

    # Integração Externa
    siga_id = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        verbose_name='ID no Sistema SIGA',
        help_text='Identificador no sistema SIGA (se integrado)'
    )

    # Controle
    ativo = models.BooleanField(
        default=True,
        verbose_name='Ativo',
        help_text='Indica se o responsável está ativo no sistema'
    )

    aceite_termos = models.BooleanField(
        default=False,
        verbose_name='Aceitou Termos de Uso'
    )

    data_aceite_termos = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Data de Aceite dos Termos'
    )

    # Observações
    observacoes = models.TextField(
        blank=True,
        null=True,
        verbose_name='Observações',
        help_text='Observações internas sobre o responsável'
    )

    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criado em'
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Atualizado em'
    )

    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='guardians_criados',
        verbose_name='Criado por'
    )

    class Meta:
        db_table = 'guardians'
        verbose_name = 'Responsável'
        verbose_name_plural = 'Responsáveis'
        ordering = ['nome_completo']

        # Indexes para performance
        indexes = [
            models.Index(fields=['cpf'], name='idx_guardian_cpf'),
            models.Index(fields=['email'], name='idx_guardian_email'),
            models.Index(fields=['ativo', '-created_at'], name='idx_guardian_ativo_created'),
            models.Index(fields=['siga_id'], name='idx_guardian_siga'),
        ]

        # Constraints
        constraints = [
            models.CheckConstraint(
                check=models.Q(cpf__regex=r'^\d{11}$'),
                name='guardian_cpf_valido'
            ),
        ]

    def __str__(self):
        return f"{self.nome_completo} ({self.cpf})"

    def __repr__(self):
        return f"<Guardian: {self.nome_completo} - CPF: {self.cpf}>"

    # Properties
    @property
    def nome_resumido(self):
        """Retorna apenas o primeiro e último nome."""
        partes = self.nome_completo.split()
        if len(partes) <= 1:
            return self.nome_completo
        return f"{partes[0]} {partes[-1]}"

    @property
    def cpf_formatado(self):
        """Retorna CPF formatado: 000.000.000-00"""
        if not self.cpf or len(self.cpf) != 11:
            return self.cpf
        return f"{self.cpf[:3]}.{self.cpf[3:6]}.{self.cpf[6:9]}-{self.cpf[9:]}"

    @property
    def telefone_formatado(self):
        """Retorna telefone formatado: (00) 00000-0000"""
        if not self.telefone_principal:
            return ''
        tel = self.telefone_principal
        if len(tel) == 11:
            return f"({tel[:2]}) {tel[2:7]}-{tel[7:]}"
        elif len(tel) == 10:
            return f"({tel[:2]}) {tel[2:6]}-{tel[6:]}"
        return tel

    @property
    def endereco_completo(self):
        """Retorna endereço completo formatado."""
        partes = []

        if self.logradouro:
            endereco = self.logradouro
            if self.numero:
                endereco += f", {self.numero}"
            if self.complemento:
                endereco += f" - {self.complemento}"
            partes.append(endereco)

        if self.bairro:
            partes.append(self.bairro)

        if self.cidade and self.estado:
            partes.append(f"{self.cidade}/{self.estado}")

        if self.cep:
            partes.append(f"CEP: {self.cep}")

        return ', '.join(partes) if partes else ''

    @property
    def quantidade_alunos(self):
        """Retorna quantidade de alunos vinculados."""
        return self.students.filter(ativo=True).count()

    @property
    def tem_alunos_ativos(self):
        """Verifica se tem alunos ativos."""
        return self.students.filter(ativo=True).exists()

    # Métodos de Validação
    def clean(self):
        """Validações customizadas do modelo."""
        super().clean()

        # Validar CPF
        if self.cpf and not self._validar_cpf(self.cpf):
            raise ValidationError({
                'cpf': 'CPF inválido'
            })

        # Validar idade mínima (18 anos)
        if self.data_nascimento:
            from datetime import date
            hoje = date.today()
            idade = hoje.year - self.data_nascimento.year
            if idade < 18:
                raise ValidationError({
                    'data_nascimento': 'Responsável deve ter pelo menos 18 anos'
                })

        # Normalizar dados
        if self.cpf:
            self.cpf = self.cpf.replace('.', '').replace('-', '').strip()

        if self.email:
            self.email = self.email.lower().strip()

        if self.email_secundario:
            self.email_secundario = self.email_secundario.lower().strip()

    @staticmethod
    def _validar_cpf(cpf: str) -> bool:
        """
        Valida CPF usando algoritmo oficial.

        Args:
            cpf: CPF como string de 11 dígitos

        Returns:
            True se válido, False caso contrário
        """
        # Remove caracteres não numéricos
        cpf = ''.join(filter(str.isdigit, cpf))

        # Verifica se tem 11 dígitos
        if len(cpf) != 11:
            return False

        # Verifica se todos os dígitos são iguais
        if cpf == cpf[0] * 11:
            return False

        # Valida primeiro dígito verificador
        soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
        digito1 = 11 - (soma % 11)
        if digito1 > 9:
            digito1 = 0
        if int(cpf[9]) != digito1:
            return False

        # Valida segundo dígito verificador
        soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
        digito2 = 11 - (soma % 11)
        if digito2 > 9:
            digito2 = 0
        if int(cpf[10]) != digito2:
            return False

        return True

    # Métodos de Negócio (leves - lógica complexa vai em Services)
    def desativar(self):
        """Desativa o responsável e seus relacionamentos."""
        self.ativo = False
        self.save(update_fields=['ativo', 'updated_at'])

    def ativar(self):
        """Ativa o responsável."""
        self.ativo = True
        self.save(update_fields=['ativo', 'updated_at'])

    def aceitar_termos(self):
        """Registra aceite dos termos de uso."""
        from django.utils import timezone
        self.aceite_termos = True
        self.data_aceite_termos = timezone.now()
        self.save(update_fields=['aceite_termos', 'data_aceite_termos', 'updated_at'])