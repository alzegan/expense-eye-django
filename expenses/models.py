from django.db import models
from django.contrib.auth.models import User


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"


class Expense(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    payment_method = models.CharField(max_length=10, choices=[
        ('cash', 'Gotówka'),
        ('card', 'Karta'),
        ('transfer', 'Przelew'),
        ('other', 'Inne')
    ])

    def __str__(self):
        return f"{self.amount} zł - {self.category} ({self.date})"
