from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(
        max_length=254, unique=True, verbose_name='Email')
    username = models.CharField(
        unique=True, blank=False,
        max_length=150, validators=[AbstractUser.username_validator],
        verbose_name='Имя пользователя'
    )
    first_name = models.CharField(
        max_length=150, blank=False, verbose_name='Имя')
    last_name = models.CharField(
        max_length=150, blank=False, verbose_name='Фамилия')
    REQUIRED_FIELDS = ['username', 'last_name', 'first_name']
    USERNAME_FIELD = 'email'

    class Meta(AbstractUser.Meta):
        ordering = ['-date_joined']
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


class Subscription(models.Model):
    subscriber = models.ForeignKey(User, on_delete=models.CASCADE,
                                   related_name='subscriber',
                                   verbose_name='Подписчик')
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='subscribing',
                               verbose_name='Автор')
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(fields=['subscriber', 'author'],
                                    name='unique_follow')
        ]

    def __str__(self):
        return f'{self.subscriber.username} -> {self.author.username}'
