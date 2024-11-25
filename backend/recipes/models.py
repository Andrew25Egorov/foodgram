"""Модели приложения recipes."""
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import Model, UniqueConstraint

from foodgram import constants
from users.models import User


class Ingredient(Model):
    """Модель Ингредиента."""

    name = models.CharField(
        verbose_name='Название',
        max_length=constants.INGRED_NAME_MAX_LENGTH)
    measurement_unit = models.CharField(
        verbose_name='Единица измерения',
        max_length=constants.MEASUR_UNIT_NAME_MAX_LENGTH)

    class Meta:
        """Класс Meta для модели Ingredient."""
        ordering = ('name',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [UniqueConstraint(
                       fields=['name', 'measurement_unit'],
                       name='uniq_ingredient_fields')]

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Tag(Model):
    """Модель Тега."""

    name = models.CharField(
        verbose_name='Название тега',
        unique=True,
        max_length=constants.TAG_NAME_MAX_LENGTH)
    slug = models.SlugField(
        verbose_name='Уникальный слаг',
        unique=True,
        max_length=constants.TAG_SLUG_MAX_LENGTH)

    class Meta:
        """Класс Meta для модели Tag."""
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Recipe(Model):
    """Модель Рецепта."""

    name = models.CharField(
        verbose_name='Название',
        max_length=constants.RECIPE_NAME_MAX_LENGTH)
    author = models.ForeignKey(
        User,
        related_name='recipes',
        on_delete=models.CASCADE,
        verbose_name='Автор рецепта',
    )
    text = models.TextField('Описание')
    image = models.ImageField('Изображение', upload_to='recipes/')
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления',
        validators=[
            MinValueValidator(
                constants.COOKING_TIME_MIN_VALUE,
                message=f'Минимум {constants.COOKING_TIME_MIN_VALUE} минута.'
            ),
            MaxValueValidator(
                constants.COOKING_TIME_MAX_VALUE,
                message=f'Максимум {constants.COOKING_TIME_MAX_VALUE} минут.'
            )
        ],
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientRecipe',
        related_name='recipes',
        verbose_name='Ингредиенты',
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Теги'
    )

    class Meta:
        """Класс Meta для модели Recipe."""
        ordering = ('-id',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return f'Рецепт "{self.name}" составил: {self.author}'


class IngredientRecipe(Model):
    """Модель связи ингредиента (с количеством) и рецепта."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe',
        verbose_name='Рецепт',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredient',
        verbose_name='Ингредиент',
    )
    amount = models.PositiveSmallIntegerField(
        default=1,
        verbose_name='Количество',
        validators=[
            MinValueValidator(
                constants.AMOUNT_MIN_VALUE,
                message=f'Минимальное кол-во {constants.AMOUNT_MIN_VALUE}.'
            ),
            MaxValueValidator(
                constants.AMOUNT_MAХ_VALUE,
                message=f'Максимальное кол-во {constants.AMOUNT_MAХ_VALUE}.'
            )
        ]
    )

    class Meta:
        """Класс Meta для модели IngredientRecipe."""
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        constraints = [
            UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient'
            )
        ]

    def __str__(self):
        return (f'{self.recipe.name}: '
                f'{self.ingredient.name} - '
                f'{self.amount} '
                f'{self.ingredient.measurement_unit}')


class UserRecipe(Model):
    """Абстрактная модель."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )

    class Meta:
        """Класс Meta для модели UserRecipe."""
        abstract = True
        constraints = [
            UniqueConstraint(
                fields=['user', 'recipe'],
                name='uniq_user_recipe',
            )
        ]


class Favorite(UserRecipe):
    """Модель Избранное."""

    class Meta:
        """Класс Meta модели Favorite."""
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        default_related_name = 'favorite_recipe'

    def __str__(self):
        return f'{self.user} добавил "{self.recipe}" в Избранное'


class ShoppingCart(UserRecipe):
    """Модель Списка покупок."""

    class Meta:
        """Класс Meta модели ShoppingCart."""
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        default_related_name = 'shopping_recipe'

    def __str__(self):
        return f'{self.user} добавил "{self.recipe}" в список покупок'
