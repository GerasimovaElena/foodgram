from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    first_name = models.CharField('Имя', max_length=150)
    last_name = models.CharField('Фамилия', max_length=150)
    avatar = models.ImageField(
        'Аватар',
        upload_to='users/avatars/',
        null=True,
        blank=True
    )
    is_subscribed = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.email


class Subscription(models.Model):
    user = models.ForeignKey(
        CustomUser,
        related_name='subscriptions',
        on_delete=models.CASCADE
    )
    subscribed_to = models.ForeignKey(
        CustomUser,
        related_name='subscribers',
        on_delete=models.CASCADE
    )

    class Meta:
        unique_together = ('user', 'subscribed_to')
