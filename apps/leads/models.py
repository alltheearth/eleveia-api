from django.db import models

class Lead(models.Model):
    """Modelo para armazenar leads capturados pelo agente IA"""

    STATUS_CHOICES = [
        ('new', 'New'),
        ('contact', 'In Contact'),
        ('qualified', 'Qualified'),
        ('conversion', 'Conversion'),
        ('lost', 'Lost'),
    ]

    ORIGIN_CHOICES = [
        ('site', 'Site'),
        ('whatsapp', 'WhatsApp'),
        ('recommendation', 'Recommendation'),
        ('call', 'Call'),
        ('email', 'Email'),
        ('facebook', 'Facebook'),

        ('instagram', 'Instagram'),
    ]

    school = models.ForeignKey(
        'schools.Escola',
        on_delete=models.CASCADE,
        related_name='leads'
    )

    name = models.CharField(max_length=255)
    email = models.EmailField()
    telephone = models.CharField(max_length=20)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='novo'
    )
    origin = models.CharField(
        max_length=20,
        choices=ORIGIN_CHOICES,
        default='whatsapp'
    )

    observations = models.TextField(blank=True)
    interests = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    contacted_at = models.DateTimeField(null=True, blank=True)
    converted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Lead'
        verbose_name_plural = 'Leads'
        ordering = ['-created_at']


    def __str__(self):
        return f"{self.name}"
