from django.contrib.auth.models import AbstractUser
from django.core import validators
from django.db import models


class CustomUser(AbstractUser):
    email = models.EmailField(
        unique=True,
        error_messages={
            'unique': 'Данный email занят'
        },
    )
    username = models.CharField(
        unique=True,
        error_messages={
            'unique': 'Данный username занят'
        },
        validators=[
            validators.RegexValidator(
                regex=r'^[\w.@+-]+$',
                message=(
                    'Username может содержать только буквы, цифры и '
                    'символы @ . + - _'
                ),
                code='invalid_username'
            )
        ],
        max_length=150
    )
    first_name = models.CharField('Имя', max_length=150)
    last_name = models.CharField('Фамилия', max_length=150)
    avatar = models.ImageField(
        'Аватар',
        upload_to='users/avatars/',
        null=True,
        blank=True
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Subscription(models.Model):
    user = models.ForeignKey(
        CustomUser,
        verbose_name='Подписчик',
        related_name='subscriptions',
        on_delete=models.CASCADE
    )
    subscribed_to = models.ForeignKey(
        CustomUser,
        verbose_name='Подписки',
        related_name='subscribers',
        on_delete=models.CASCADE
    )

    class Meta:
        unique_together = ('user', 'subscribed_to')
        verbose_name = 'Подписки'
        verbose_name_plural = 'Подписки'
