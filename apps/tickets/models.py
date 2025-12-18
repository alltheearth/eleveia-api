from django.db import models

STATUS_CHOICES = [
    ('open', 'Open'),
    ('in_progress', 'In Progress'),
    ('pending', 'Pending'),
    ('closed', 'Closed'),
    ('resolved', 'Resolved')
    ]
PRIORITY_CHOISES = [
    ('high', 'High'),
    ('medium','Medium'),
    ('urgent', 'Urgent')
]


class Ticket(models.Model):
    """Modelo para armazenar informações dos Tickets"""

    title = models.CharField()
    school = models.ForeignKey(
        'schools.Escola',
        on_delete=models.CASCADE,
        related_name='tickets',
        help_text='Escola vinculada ao ticket'
    )
    description = models.CharField(max_length=250, blank=False, null=False)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOISES, default="medium")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Ticket'
        verbose_name_plural = 'Tickets'
        ordering = ['-created_at']

    def __str__(self):
        return self.title
