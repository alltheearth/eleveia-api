# ===================================================================
# apps/faqs/models.py - ENGLISH VERSION
# ===================================================================
from django.db import models
from django.contrib.auth.models import User


class FAQ(models.Model):
    """Frequently Asked Questions"""

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    CATEGORY_CHOICES = [
        ('Admission', 'Admission'),
        ('Pricing', 'Pricing'),
        ('Uniform', 'Uniform'),
        ('Schedule', 'Schedule'),
        ('Documentation', 'Documentation'),
        ('Activities', 'Activities'),
        ('Meals', 'Meals'),
        ('Transport', 'Transport'),
        ('Pedagogical', 'Pedagogical'),
        ('General', 'General'),
    ]

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='created_faqs',
        null=True,
        blank=True,
        verbose_name='Created by'
    )

    school = models.ForeignKey(
        'schools.School',
        on_delete=models.CASCADE,
        related_name='faqs',
        verbose_name='School'
    )

    question = models.CharField(
        max_length=500,
        verbose_name='Question'
    )

    answer = models.TextField(
        blank=True,
        verbose_name='Answer'
    )

    category = models.CharField(
        max_length=100,
        choices=CATEGORY_CHOICES,
        verbose_name='Category'
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name='Status'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created at'
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated at'
    )

    class Meta:
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQs'
        db_table = 'faqs_faq'
        ordering = ['-created_at']

    def __str__(self):
        return self.question