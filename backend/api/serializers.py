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
                {'avatar': 'Поле avatar обязательно.'})
        return data


class UserReadSerializer(UserSerializer):
    """Cписок пользователей."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name',
                  'avatar', 'is_subscribed')

    def get_is_subscribed(self, obj):
        user_id = self.context.get('request').user.id
        return Subscribe.objects.filter(
            author=obj.id, user=user_id
        ).exists()


class UserCreateSerializers(UserCreateSerializer):
    """Создание нового пользователя."""

    class Meta:
        model = User
        fields = ('id', 'email', 'id', 'username',
                  'first_name', 'last_name', 'password'
                  )
        """ extra_kwargs = {
            'first_name': {'required': True, 'allow_blank': False},
            'last_name': {'required': True, 'allow_blank': False},
            'username': {'required': True, 'allow_blank': False},
            'email': {'required': True, 'allow_blank': False},
        } """

    def validate(self, attrs):
        invalid_usernames = ['me', 'set_password',
                             'subscriptions', 'subscribe']
        if attrs.get('username') in invalid_usernames:
            raise serializers.ValidationError(
                {'username': 'Вы не можете использовать этот username.'}
            )
        return attrs


class SetPasswordSerializer(serializers.Serializer):
    """Изменение пароля пользователя."""

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
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'avatar',
                  'username', 'first_name',
                  'last_name', 'is_subscribed',
                  'recipes', 'recipes_count')
        read_only_fields = ('email', 'username')

    def validate(self, data):
        author = self.instance
        user = self.context.get('request').user
        if Subscribe.objects.filter(author=author, user=user).exists():
            raise ValidationError(
                detail='Вы уже подписаны на этого пользователя!',
                code=status.HTTP_400_BAD_REQUEST
            )
        if user == author:
            raise ValidationError(
                detail='Вы не можете подписаться на самого себя!',
                code=status.HTTP_400_BAD_REQUEST
            )
        return data

    def get_recipes_count(self, obj):
        """Количество рецептов автора."""
        return obj.recipes.count()

    def get_recipes(self, obj):
        """Получение списка рецептов автора."""
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        recipes = obj.recipes.all()
        if limit:
            recipes = recipes[:int(limit)]
        serializer = RecipeSerializer(recipes, many=True)
        return serializer.data


# -----------------------------------------------------------------------------
#                            Приложение recipes
# -----------------------------------------------------------------------------


class IngredientSerializer(serializers.ModelSerializer):
    """Список ингредиентов."""

    class Meta:
        model = Ingredient
        fields = '__all__'


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
    """Список рецептов."""

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
        request = self.context.get('request')
        return bool(
            request
            and request.user.is_authenticated
            and request.user.favorite_recipes.filter(recipe=obj).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        return bool(
            request
            and request.user.is_authenticated
            and request.user.shopping_carts.filter(recipe=obj).exists()
        )


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
                  'tags', 'image',
                  'name', 'text',
                  'cooking_time', 'author')
        """ extra_kwargs = {
            'ingredients': {'required': True},
            'tags': {'required': True},
            'name': {'required': True},
            'text': {'required': True},
            'image': {'required': True},
            'cooking_time': {'required': True},
        } """

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

    @transaction.atomic
    def create_ingredients_amounts(self, ingredients, recipe):
        IngredientRecipe.objects.bulk_create(
            IngredientRecipe(
                ingredient=get_object_or_404(Ingredient, id=ingredient['id']),
                recipe=recipe,
                amount=ingredient['amount'],
            ) for ingredient in ingredients
        )
        return recipe

    @transaction.atomic
    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        request = self.context.get('request')
        recipe = Recipe.objects.create(author=request.user, **validated_data)
        recipe.tags.set(tags)
        return self.create_ingredients_amounts(ingredients, recipe)

    @transaction.atomic
    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        instance.tags.clear()
        instance.tags.set(tags)
        instance.ingredients.clear()
        super().update(instance, validated_data)
        return self.create_ingredients_amounts(ingredients, instance)

    def to_representation(self, instance):
        return RecipeReadSerializer(instance).data
