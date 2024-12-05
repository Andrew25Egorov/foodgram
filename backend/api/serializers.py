from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework.exceptions import ValidationError
from rest_framework.fields import IntegerField, SerializerMethodField
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.serializers import (ModelSerializer, ReadOnlyField,
                                        UniqueTogetherValidator)

from foodgram import constants
from recipes.models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                            ShoppingCart, Tag)
from users.models import Subscribe, User


class AvatarSerializer(UserSerializer):
    """Аватар."""

    avatar = Base64ImageField(required=True)

    class Meta:
        """Класс Meta."""

        model = User
        fields = ('avatar',)

    def validate(self, data):
        """Валидация поля аватара."""
        if 'avatar' not in data:
            raise ValidationError(
                {'errors': 'Поле avatar обязательно.'})
        return data


class UserReadSerializer(UserSerializer):
    """Чтение информации о пользователе и подписке."""

    is_subscribed = SerializerMethodField(read_only=True)

    class Meta:
        """Класс Meta."""

        model = User
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name',
                  'is_subscribed', 'avatar')

    def get_is_subscribed(self, author):
        """Проверка наличия подписки."""
        request = self.context.get('request')
        return (
            request and request.user.is_authenticated
            and Subscribe.objects.filter(user=request.user,
                                         author=author).exists()
        )


class UserCreateSerializers(UserCreateSerializer):
    """Создание нового пользователя."""

    class Meta:
        """Класс Meta."""

        model = User
        fields = ('id', 'email', 'username',
                  'first_name', 'last_name', 'password')


class SubscriptionsSerializer(UserReadSerializer):
    """Список авторов, на которых подписан пользователь."""

    recipes = SerializerMethodField()
    recipes_count = SerializerMethodField()

    class Meta(UserReadSerializer.Meta):
        """Класс Meta."""

        fields = ('email', 'id', 'avatar',
                  'username', 'first_name',
                  'last_name', 'is_subscribed',
                  'recipes', 'recipes_count')
        read_only_fields = ('email', 'avatar', 'first_name',
                            'last_name', 'username')

    def get_recipes_count(self, author):
        """Количество подписок на рецепт автора."""
        return author.recipes.count()

    def get_recipes(self, author):
        """Получение списка рецептов автора."""
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit', None)
        recipes = author.recipes.all()
        if limit is not None:
            recipes = recipes[:int(limit)]
        serializer = RecipeSerializer(recipes, many=True, read_only=True)
        return serializer.data


class SubscribeSerializer(ModelSerializer):
    """Подписка на автора."""

    class Meta:
        """Класс Meta."""

        model = Subscribe
        fields = ('user', 'author')
        validators = [UniqueTogetherValidator(
            queryset=Subscribe.objects.all(),
            fields=('user', 'author'),
            message='Вы уже подписаны на этого автора.')
        ]

    def validate(self, data):
        """Валидация подписки на себя."""
        if self.context['request'].user == data['author']:
            raise ValidationError('Нельзя подписаться на самого себя.')
        return data

    def to_representation(self, instance):
        """Метод представления данных."""
        return SubscriptionsSerializer(
            instance.author,
            context={'request': self.context.get('request')}
        ).data


class IngredientSerializer(ModelSerializer):
    """Список ингредиентов с единицами измерения."""

    class Meta:
        """Класс Meta."""

        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class TagSerializer(ModelSerializer):
    """Список тегов."""

    class Meta:
        """Класс Meta."""

        model = Tag
        fields = ('id', 'name', 'slug')


class RecipeSerializer(ModelSerializer):
    """Список рецептов без ингредиентов."""

    image = Base64ImageField()

    class Meta:
        """Класс Meta."""

        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('name', 'image', 'cooking_time')


class RecipeIngredientSerializer(ModelSerializer):
    """Список ингредиентов с количеством для рецепта."""

    id = ReadOnlyField(source='ingredient.id')
    name = ReadOnlyField(source='ingredient.name')
    measurement_unit = ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        """Класс Meta."""

        model = IngredientRecipe
        fields = ('id', 'name',
                  'measurement_unit', 'amount')


class RecipeReadSerializer(ModelSerializer):
    """Сериализатор для вывода информации о рецепте."""

    author = UserReadSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = SerializerMethodField()
    is_favorited = SerializerMethodField(read_only=True)
    is_in_shopping_cart = SerializerMethodField(read_only=True)
    image = Base64ImageField()

    class Meta:
        """Класс Meta."""

        model = Recipe
        fields = ('id', 'tags',
                  'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart',
                  'name', 'image',
                  'text', 'cooking_time')

    def get_ingredients(self, obj):
        """Получение списка ингредиентов."""
        ingredients = IngredientRecipe.objects.filter(recipe=obj)
        return RecipeIngredientSerializer(ingredients, many=True).data

    def get_is_favorited(self, obj):
        """Проверка добавления рецепта в избранное."""
        request = self.context.get('request')
        return (
            request and request.user.is_authenticated
            and Favorite.objects.filter(user=request.user,
                                        recipe=obj).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        """Проверка нахождения рецепта в списке покупок."""
        request = self.context.get('request')
        return (
            request and request.user.is_authenticated
            and ShoppingCart.objects.filter(user=request.user,
                                            recipe=obj).exists()
        )


class RecipeIngredientCreateSerializer(ModelSerializer):
    """Ингредиент с количеством для создания рецепта."""

    id = PrimaryKeyRelatedField(queryset=Ingredient.objects.all(),
                                write_only=True)
    amount = IntegerField(max_value=constants.AMOUNT_MAХ_VALUE,
                          min_value=constants.AMOUNT_MIN_VALUE)

    class Meta:
        """Класс Meta."""

        model = IngredientRecipe
        fields = ('id', 'amount')


class RecipeCreateSerializer(ModelSerializer):
    """Создание, изменение или удаление рецепта."""

    author = UserReadSerializer(read_only=True)
    tags = PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True)
    ingredients = RecipeIngredientCreateSerializer(many=True)
    image = Base64ImageField()
    cooking_time = IntegerField(max_value=constants.COOKING_TIME_MAX_VALUE,
                                min_value=constants.COOKING_TIME_MIN_VALUE)

    class Meta:
        """Класс Meta."""

        model = Recipe
        fields = ('id', 'ingredients',
                  'tags', 'author',
                  'name', 'image',
                  'text', 'cooking_time')

    def validate(self, obj):
        """Валидация заполнения полей."""
        required_fields = ['ingredients', 'tags', 'name',
                           'text', 'cooking_time']

        if 'id' not in self.initial_data:
            required_fields.append('image')

        for field in required_fields:
            if not obj.get(field):
                raise ValidationError(f'{field} - Заполните это поле!')
        return obj

    def validate_ingredients(self, value):
        """Валидация по ингредиенту."""
        if not value:
            raise ValidationError('Нужен хотя бы один ингредиент!')

        ingredients = set()
        for item in value:
            ingredient_id = item['id']
            if ingredient_id in ingredients:
                raise ValidationError('Ингредиенты не могут повторяться!')
            ingredients.add(ingredient_id)
        return value

    def validate_tags(self, value):
        """Валидация по тегам."""
        if not value:
            raise ValidationError('Нужно выбрать хотя бы один тег!')
        if len(value) != len(set(value)):
            raise ValidationError('Теги должны быть уникальными!')
        return value

    def create(self, validated_data):
        """Метод создания рецепта."""
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_ingredients_amounts(ingredients, recipe)
        return recipe

    def update(self, recipe, validated_data):
        """Метод редактирования рецепта."""
        if 'tags' in validated_data:
            recipe.tags.set(validated_data.pop('tags'))

        if 'ingredients' in validated_data:
            ingredients = validated_data.pop('ingredients')
            recipe.ingredients.clear()
            self.create_ingredients_amounts(ingredients, recipe)

        return super().update(recipe, validated_data)

    @staticmethod
    def create_ingredients_amounts(ingredients, recipe):
        """Добавление ингредиентов с количеством."""
        IngredientRecipe.objects.bulk_create([
            IngredientRecipe(ingredient=i['id'],
                             recipe=recipe,
                             amount=i['amount'])
            for i in ingredients
        ])

    def to_representation(self, recipe):
        """Метод представления данных."""
        context = {'request': self.context.get('request')}
        return RecipeReadSerializer(recipe, context=context).data


class ShoppingCartSerializer(ModelSerializer):
    """Добавление в список покупок."""

    class Meta:
        """Класс Meta."""

        model = ShoppingCart
        fields = (
            'user',
            'recipe'
        )

    def validate(self, attrs):
        """Валидация добавления в покупки."""
        user = attrs['user']
        recipe = attrs['recipe']
        if user.shopping_recipe.filter(recipe=recipe).exists():
            raise ValidationError(
                {'recipe': 'Уже есть в списке.'}
            )
        return attrs

    def to_representation(self, instance):
        """Метод представления данных."""
        return RecipeSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data


class FavoriteSerializer(ModelSerializer):
    """Добавление в избранное."""

    class Meta:
        """Класс Meta."""

        model = Favorite
        fields = (
            'user',
            'recipe'
        )

    def validate(self, attrs):
        """Валидация добавления в избранное."""
        user = attrs['user']
        recipe = attrs['recipe']
        if user.favorite_recipe.filter(recipe=recipe).exists():
            raise ValidationError(
                {'recipe': 'Уже добавлен в избранное.'}
            )
        return attrs

    def to_representation(self, instance):
        """Метод представления данных."""
        return RecipeSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data
