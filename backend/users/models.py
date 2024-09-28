from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.db.models import UniqueConstraint


class User(AbstractUser):
    """Модель пользователя."""
    username = models.CharField(
        max_length=150,
        unique=True,
        help_text='Укажите username',
        validators=[UnicodeUsernameValidator()],
    )
    email = models.EmailField(
        unique=True,
        max_length=254,
        verbose_name='Электронная почта',
        help_text='Укажите электронную почту',
    )
    first_name = models.CharField(verbose_name='Имя', max_length=150,
                                  help_text='Укажите имя')
    last_name = models.CharField(verbose_name='Фамилия', max_length=150,
                                 help_text='Укажите фамилию')
    avatar = models.ImageField(
        upload_to='avatar/',
        null=True,
        verbose_name='Аватарка',
    )

    class Meta(AbstractUser.Meta):
        """Класс Meta для модели User."""
        ordering = ['id']
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Subscribe(models.Model):
    """Модель подписки на автора."""
    user = models.ForeignKey(
        User,
        related_name='subscriber',
        verbose_name="Подписчик",
        on_delete=models.CASCADE,
    )
    author = models.ForeignKey(
        User,
        related_name='subscribing',
        verbose_name="Автор",
        on_delete=models.CASCADE,
    )

    class Meta:
        """Класс Meta для модели Subscribe."""
        ordering = ['-id']
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            UniqueConstraint(fields=['user', 'author'],
                             name='uniq_user_subscribe')
        ]

    def __str__(self):
        return f'{self.user} подписан на {self.author}'
