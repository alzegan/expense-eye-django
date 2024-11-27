from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from decimal import Decimal


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='profile_pics', default='default.jpg')

    def __str__(self):
        return f'{self.user.username} Profile'

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    instance.profile.save()

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


class FinancialGoal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    target_amount = models.DecimalField(max_digits=10, decimal_places=2)
    current_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deadline = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    archived = models.BooleanField(default=False)
    achieved_date = models.DateTimeField(null=True, blank=True)

    def get_progress_percentage(self):
        if self.target_amount <= 0:
            return Decimal('0')
        progress = (self.current_amount / self.target_amount) * Decimal('100')
        return min(progress, Decimal('100'))


    def get_remaining_amount(self):
        return self.target_amount - self.current_amount

    def check_if_achieved(self):
        if not self.archived and self.current_amount >= self.target_amount:
            self.archived = True
            self.achieved_date = timezone.now()
            self.save()
            return True
        return False
    def archive_if_achieved(self):
        if not self.archived and self.current_amount >= self.target_amount:
            self.archived = True
            self.achieved_date = timezone.now()
            self.save()
