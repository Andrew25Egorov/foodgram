# from django.contrib.auth.password_validation import validate_password
# from django.core import exceptions as django_exceptions
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.fields import IntegerField, SerializerMethodField
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.serializers import ModelSerializer, ReadOnlyField
from rest_framework.validators import UniqueTogetherValidator
# from django.db import transaction
# from django.shortcuts import get_object_or_404

from recipes.models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                            ShoppingCart, Tag)
from users.models import Subscribe, User


class AvatarSerializer(UserSerializer):
    """Аватар."""

    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ('avatar',)

    def validate(self, data):
        if 'avatar' not in data:
            raise ValidationError(
                {'errors': 'Поле avatar обязательно.'})
        return data


class UserReadSerializer(UserSerializer):
    """Сериализатор для чтения информации о пользователе и подписке."""

    is_subscribed = SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name',
                  'avatar', 'is_subscribed')

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
        model = User
        fields = ('id', 'email', 'username',
                  'first_name', 'last_name', 'password')

    def validate(self, attrs):
        invalid_usernames = ['admin', 'me', 'set_password', 'first_name',
                             'last_name', 'subscriptions', 'subscribe']
        if attrs.get('username') in invalid_usernames:
            raise ValidationError(
                {'username': 'Вы не можете использовать этот username.'}
            )
        return attrs


""" class SetPasswordSerializer(serializers.Serializer):
    Изменение пароля пользователя.

    current_password = serializers.CharField()
    new_password = serializers.CharField()

    def validate(self, obj):
        try:
            validate_password(obj['new_password'])
        except django_exceptions.ValidationError as e:
            raise serializers.ValidationError(
                {'new_password': list(e.messages)}
            )
        return super().validate(obj)

    def update(self, instance, validated_data):
        if not instance.check_password(validated_data['current_password']):
            raise serializers.ValidationError(
                {'current_password': 'Неправильный пароль.'}
            )
        if (validated_data['current_password']
           == validated_data['new_password']):
            raise serializers.ValidationError(
                {'new_password': 'Новый пароль должен отличаться от текущего.'}
            )
        instance.set_password(validated_data['new_password'])
        instance.save()
        return validated_data
 """


class RecipeSerializer(ModelSerializer):
    """Список рецептов без ингредиентов."""

    image = Base64ImageField(read_only=True)

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('name', 'image', 'cooking_time')


class SubscriptionsSerializer(UserReadSerializer):
    """Список авторов на которых подписан пользователь."""

    recipes = SerializerMethodField()
    recipes_count = SerializerMethodField()

    class Meta(UserReadSerializer.Meta):
        fields = ('email', 'id', 'avatar',
                  'username', 'first_name',
                  'last_name', 'is_subscribed',
                  'recipes', 'recipes_count')
        read_only_fields = ('email', 'avatar', 'first_name',
                            'last_name', 'username')

    def get_recipes_count(self, author):
        """Количество рецептов автора."""
        return author.recipes.count()

    def get_recipes(self, author):
        """Получение списка рецептов автора."""
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit', None)
        recipes = author.recipes.all()
        if limit is not None:
            try:
                recipes = recipes[:int(limit)]
            except ValueError:
                raise ValidationError(
                    detail='Неверный формат лимита рецептов!',
                    code=status.HTTP_400_BAD_REQUEST
                )
        serializer = RecipeSerializer(recipes, many=True, read_only=True)
        return serializer.data


class SubscribeSerializer(ModelSerializer):
    """Подписка на автора."""

    class Meta:
        model = Subscribe
        fields = (
            'user',
            'author'
        )

    def validate(self, attrs):
        user = attrs['user']
        author = attrs['author']
        if user == author:
            raise ValidationError(
                {'author': 'Нельзя подписаться на себя.'}
            )
        if user.subscriber.filter(author=author).exists():
            raise ValidationError(
                {'author': 'Уже подписан.'}
            )
        return attrs

    def to_representation(self, instance):
        return SubscriptionsSerializer(
            instance.author,
            context={'request': self.context.get('request')}
        ).data

# -----------------------------------------------------------------------------
#                            Приложение recipes
# -----------------------------------------------------------------------------


class IngredientSerializer(ModelSerializer):
    """Список ингредиентов."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class TagSerializer(ModelSerializer):
    """Список тегов."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class RecipeIngredientSerializer(ModelSerializer):
    """Список ингредиентов с количеством для рецепта."""

    id = ReadOnlyField()
    name = ReadOnlyField(source='ingredient.name')
    measurement_unit = ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name',
                  'measurement_unit', 'amount')
        validators = [UniqueTogetherValidator(
            queryset=IngredientRecipe.objects.all(),
            fields=['ingredient', 'recipe'])
        ]


class RecipeReadSerializer(ModelSerializer):
    """Сериализатор для чтения информации о рецепте."""

    author = UserReadSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = SerializerMethodField()
    is_favorited = SerializerMethodField(read_only=True)
    is_in_shopping_cart = SerializerMethodField(read_only=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags',
                  'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart',
                  'name', 'image',
                  'text', 'cooking_time')
        read_only_fields = ('author', 'tags',)

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
    """Ингредиент и количество для создания рецепта."""

#    id = PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    id = IntegerField(write_only=True)

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'amount')


class RecipeCreateSerializer(ModelSerializer):
    """Создание, изменение и удаление рецепта."""

    author = UserReadSerializer(read_only=True)
    id = ReadOnlyField()
    tags = PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True)
    ingredients = RecipeIngredientCreateSerializer(many=True)
    image = Base64ImageField(max_length=None)
    cooking_time = IntegerField()

    class Meta:
        model = Recipe
        fields = ('id', 'ingredients',
                  'tags', 'author',
                  'name', 'image',
                  'text', 'cooking_time')

    def validate_ingredients(self, value):
        if not value:
            raise ValidationError('Нужен хотя бы один ингредиент!')
        ingredients = set()
        for item in value:
            if item['id'] in ingredients:
                raise ValidationError('Ингредиенты не могут повторяться!')
            if int(item['amount']) <= 0:
                raise ValidationError(
                    'Количество ингредиента должно быть больше 0!'
                )
            ingredients.add(item['id'])
        return value

    def validate_cooking_time(self, value):
        if value < 1:
            raise ValidationError(
                'Время приготовления не меньше одной минуты')
        return value

    def validate_tags(self, value):
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

    def update(self, instance, validated_data):
        """Метод изменения рецепта."""
        tags = validated_data.pop('tags', [])
        ingredients = validated_data.pop('ingredients', [])
        if tags:
            instance.tags.set(tags)
        if ingredients:
            instance.ingredients.clear()
            self.create_ingredients_amounts(ingredients, instance)
        return super().update(instance, validated_data)

    @staticmethod
    def create_ingredients_amounts(ingredients, recipe):
        """Добавление ингредиентов с количеством."""
        for ingredient in ingredients:
            IngredientRecipe.objects.create(
                recipe=recipe,
                ingredient=ingredient.get('id'),
                amount=ingredient.get('amount'),
            )
        # IngredientRecipe.objects.bulk_create(
        #     IngredientRecipe(
        #         ingredient=Ingredient.objects.get(id=ingredient['id']),
        #         recipe=recipe,
        #         amount=ingredient['amount'],
        #     ) for ingredient in ingredients
        # )
        # return recipe

    def to_representation(self, recipe):
        request = self.context.get('request')
        context = {'request': request}
        return RecipeReadSerializer(recipe, context=context).data


class ShoppingCartSerializer(ModelSerializer):
    """Добавление в список покупок."""

    class Meta:
        model = ShoppingCart
        fields = (
            'user',
            'recipe'
        )

    def validate(self, attrs):
        user = attrs['user']
        recipe = attrs['recipe']
        if user.shopping_user.filter(recipe=recipe).exists():
            raise ValidationError(
                {'recipe': 'Уже есть в списке.'}
            )
        return attrs

    def to_representation(self, instance):
        return RecipeSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data


class FavoriteSerializer(ModelSerializer):
    """Добавление в избранное."""

    class Meta:
        model = Favorite
        fields = (
            'user',
            'recipe'
        )

    def validate(self, attrs):
        user = attrs['user']
        recipe = attrs['recipe']
        if user.favorite_recipe.filter(recipe=recipe).exists():
            raise ValidationError(
                {'recipe': 'Уже добавлен в избранное.'}
            )
        return attrs

    def to_representation(self, instance):
        return RecipeSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data
