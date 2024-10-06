from django.contrib.auth.password_validation import validate_password
from django.core import exceptions as django_exceptions
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from recipes.models import (Favorite, Ingredient, Recipe, IngredientRecipe,
                            ShoppingCart, Tag)
from rest_framework import serializers
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueTogetherValidator
from django.db import transaction
from django.shortcuts import get_object_or_404

from users.models import Subscribe, User


class AvatarSerializer(UserSerializer):
    """Аватар."""

    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ('avatar',)

    def validate(self, data):
        if 'avatar' not in data:
            raise serializers.ValidationError(
                {'errors': 'Поле avatar обязательно.'})
        return data


class UserReadSerializer(UserSerializer):
    """Сериализатор для чтения информации о пользователе, включая подписку."""

    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name',
                  'avatar', 'is_subscribed')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return request.user.subscriber.filter(user=obj).exists()
        return False


class UserCreateSerializers(UserCreateSerializer):
    """Создание нового пользователя."""

    class Meta:
        model = User
        fields = ('id', 'email', 'username',
                  'first_name', 'last_name', 'password')

    def validate(self, attrs):
        invalid_usernames = ['me', 'set_password',
                             'subscriptions', 'subscribe']
        if attrs.get('username') in invalid_usernames:
            raise serializers.ValidationError(
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


class RecipeSerializer(serializers.ModelSerializer):
    """Список рецептов без ингредиентов."""

    image = Base64ImageField(read_only=True)
#    name = serializers.ReadOnlyField()
#    cooking_time = serializers.ReadOnlyField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('name', 'image', 'cooking_time')


class SubscriptionsSerializer(UserReadSerializer):
    """Список авторов на которых подписан пользователь."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.ReadOnlyField(source='recipes.count')

    class Meta:
        model = User
        fields = ('email', 'id', 'avatar',
                  'username', 'first_name',
                  'last_name', 'is_subscribed',
                  'recipes', 'recipes_count')
        read_only_fields = ('email', 'username')

    """ def validate(self, data):
        author = self.instance
        user = self.context.get('request').user
        if Subscribe.objects.filter(author=author, user=user).exists():
            raise serializers.ValidationError(
                detail='Вы уже подписаны на этого пользователя!',
                code=status.HTTP_400_BAD_REQUEST
            )
        if user == author:
            raise serializers.ValidationError(
                detail='Вы не можете подписаться на самого себя!',
                code=status.HTTP_400_BAD_REQUEST
            )
        return data """

    def get_recipes_count(self, obj):
        """Количество рецептов автора."""
        return obj.recipes.count()

    def get_recipes(self, obj):
        """Получение списка рецептов автора."""
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit', None)
        recipes = obj.recipes.all()
        if limit is not None:
            try:
                recipes = recipes[:int(limit)]
            except ValueError:
                raise serializers.ValidationError(
                    detail='Неверный формат лимита рецептов!',
                    code=status.HTTP_400_BAD_REQUEST
                )
        return RecipeSerializer(recipes, many=True, context=self.context).data


class SubscribeSerializer(serializers.ModelSerializer):

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
            raise serializers.ValidationError(
                {'author': 'Нельзя подписаться на себя.'}
            )

        if user.subscriber.filter(author=author).exists():
            raise serializers.ValidationError(
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


class IngredientSerializer(serializers.ModelSerializer):
    """Список ингредиентов."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class TagSerializer(serializers.ModelSerializer):
    """Список тегов."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Список ингредиентов с количеством для рецепта."""

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name',
                  'measurement_unit', 'amount')
        validators = [UniqueTogetherValidator(
            queryset=IngredientRecipe.objects.all(),
            fields=['ingredient', 'recipe'])
        ]


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения информации о рецепте."""

    author = UserReadSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = RecipeIngredientSerializer(
        many=True, read_only=True, source='recipe_ingredient')
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags',
                  'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart',
                  'name', 'image',
                  'text', 'cooking_time')
        read_only_fields = ('author', 'tags',)

    def get_is_favorited(self, obj):
        """Проверка, добавлен ли рецепт в избранное."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Favorite.objects.filter(user=request.user, recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        """Проверка, находится ли рецепт в списке покупок."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return ShoppingCart.objects.filter(user=request.user, recipe=obj).exists()
        return False
    # def get_is_favorited(self, obj):
    #     """Проверка добавлен ли рецепт в избранное."""
    #     user = self.context.get('request').user
    #     if user.is_anonymous:
    #         return False
    #     return Favorite.objects.filter(user=user, recipe=obj).exists()

    # def get_is_in_shopping_cart(self, obj):
    #     user = self.context.get('request').user
    #     if user.is_anonymous:
    #         return False
    #     return ShoppingCart.objects.filter(user=user, recipe=obj).exists()


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    """Ингредиент и количество для создания рецепта."""

#    id = serializers.IntegerField(write_only=True)
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'amount')


class RecipeCreateSerializer(serializers.ModelSerializer):
    """[POST, PATCH, DELETE] Создание, изменение и удаление рецепта."""

    author = UserReadSerializer(read_only=True)
    id = serializers.ReadOnlyField()
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(),
                                              many=True)
    ingredients = RecipeIngredientCreateSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'ingredients',
                  'tags', 'author',
                  'name', 'image',
                  'text', 'cooking_time')

    def validate_ingredients(self, value):
        if not value:
            raise ValidationError('Нужен хотя бы один ингредиент!')
        ingredient_list = set()
        for item in value:
            ingredient = get_object_or_404(Ingredient, id=item['id'])
            if ingredient in ingredient_list:
                raise ValidationError('Ингредиенты не могут повторяться!')
            if int(item['amount']) <= 0:
                raise ValidationError(
                    'Количество ингредиента должно быть больше 0!'
                )
            ingredient_list.add(item['id'])
        return value

    def validate_tags(self, value):
        if not value:
            raise ValidationError('Нужно выбрать хотя бы один тег!')
        if len(value) != len(set(value)):
            raise ValidationError('Теги должны быть уникальными!')
        return value

    # @transaction.atomic
    # def create(self, validated_data):
    #     tags = validated_data.pop('tags')
    #     ingredients = validated_data.pop('ingredients')
    #     print(f'ingredients: {ingredients}')
    #     request = self.context.get('request')
    #     recipe = Recipe.objects.create(author=request.user, **validated_data)
    #     recipe.tags.set(tags)
    #     self.create_ingredients_amounts(recipe=recipe, ingredients=ingredients)
    #     return recipe
    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        request = self.context.get('request')
        recipe = Recipe.objects.create(author=request.user, **validated_data)
        recipe.tags.set(tags)
        return self.create_ingredients_amounts(ingredients, recipe)

#     @transaction.atomic
#     def update(self, instance, validated_data):
#         tags = validated_data.pop('tags')
#         ingredients = validated_data.pop('ingredients')
# #        instance = super().update(instance, validated_data)
#         instance.tags.clear()
#         instance.tags.set(tags)
#         instance.ingredients.clear()
#         instance = super().update(instance, validated_data)
#         self.create_ingredients_amounts(ingredients=ingredients,
#                                         recipe=instance)
#         instance.save()
#         return instance
    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        instance.tags.clear()
        instance.tags.set(tags)
        instance.ingredients.clear()
        super().update(instance, validated_data)
        return self.create_ingredients_amounts(ingredients, instance)

#    @transaction.atomic
    @staticmethod
    def create_ingredients_amounts(ingredients, recipe):
        IngredientRecipe.objects.bulk_create(
            IngredientRecipe(
                ingredient=ingredient['id'],
                recipe=recipe,
                amount=ingredient['amount'],
            ) for ingredient in ingredients
        )
        return recipe

    def to_representation(self, instance):
        return RecipeReadSerializer(instance).data
    # def to_representation(self, instance):
    #     request = self.context.get('request')
    #     context = {'request': request}
    #     return RecipeReadSerializer(instance, context=context).data


class ShoppingCartSerializer(serializers.ModelSerializer):
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
            raise serializers.ValidationError(
                {'recipe': 'Уже есть в списке.'}
            )
        return attrs

    def to_representation(self, instance):
        return RecipeSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data


class FavoriteSerializer(serializers.ModelSerializer):
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
            raise serializers.ValidationError(
                {'recipe': 'Уже добавлен в избранное.'}
            )
        return attrs

    def to_representation(self, instance):
        return RecipeSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data
