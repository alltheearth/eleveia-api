
class Lead(models.Model):
    """Modelo para armazenar leads capturados pelo agente IA"""
    STATUS_CHOICES = [
        ('novo', 'Novo'),
        ('contato', 'Em Contato'),
        ('qualificado', 'Qualificado'),
        ('conversao', 'Conversão'),
        ('perdido', 'Perdido'),
    ]

    ORIGEM_CHOICES = [
        ('site', 'Site'),
        ('whatsapp', 'WhatsApp'),
        ('indicacao', 'Indicação'),
        ('ligacao', 'Ligação'),
        ('email', 'Email'),
        ('facebook', 'Facebook'),
        ('instagram', 'Instagram'),
    ]

    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='leads',
        null=True,
        blank=True
    )
    escola = models.ForeignKey(
        Escola,
        on_delete=models.CASCADE,
        related_name='leads'
    )

    nome = models.CharField(max_length=255)
    email = models.EmailField()
    telefone = models.CharField(max_length=20)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='novo'
    )
    origem = models.CharField(
        max_length=20,
        choices=ORIGEM_CHOICES,
        default='site'
    )

    observacoes = models.TextField(blank=True)
    interesses = models.JSONField(default=dict, blank=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    contatado_em = models.DateTimeField(null=True, blank=True)
    convertido_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'Lead'
        verbose_name_plural = 'Leads'
        indexes = [
            models.Index(fields=['escola', 'status']),
            models.Index(fields=['criado_em']),
        ]

    def __str__(self):
        return f"{self.nome} - {self.get_status_display()}"


