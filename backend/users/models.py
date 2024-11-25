"""Модели приложения users."""
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.db.models import Model, UniqueConstraint

from foodgram import constants


class User(AbstractUser):
    """Модель пользователя."""

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'username']

    username = models.CharField(
        max_length=constants.USERNAME_MAX_LENGTH,
        unique=True,
        help_text='Укажите username',
        validators=[UnicodeUsernameValidator()],
    )
    email = models.EmailField(
        unique=True,
        max_length=constants.EMAIL_MAX_LENGTH,
        verbose_name='Электронная почта',
        help_text='Укажите электронную почту',
    )
    first_name = models.CharField(
        verbose_name='Имя',
        max_length=constants.FIRST_NAME_MAX_LENGTH,
        help_text='Укажите имя'
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=constants.LAST_NAME_MAX_LENGTH,
        help_text='Укажите фамилию'
    )
    avatar = models.ImageField(
        upload_to='avatar/',
        null=True,
        verbose_name='Аватарка',
    )

    class Meta:
        """Класс Meta для модели User."""
        ordering = ['username']
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Subscribe(Model):
    """Модель подписки на автора."""
    user = models.ForeignKey(
        User,
        related_name='subscriber',
        verbose_name='Подписчик',
        on_delete=models.CASCADE,
    )
    author = models.ForeignKey(
        User,
        related_name='subscribing',
        verbose_name='Автор',
        on_delete=models.CASCADE,
    )

    class Meta:
        """Класс Meta для модели Subscribe."""
        ordering = ['user']
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            UniqueConstraint(fields=['user', 'author'],
                             name='uniq_user_subscribe')
        ]

    def __str__(self):
        return f'{self.user} подписан на {self.author}'
