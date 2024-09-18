from django.contrib.auth.password_validation import validate_password
from django.core import exceptions as django_exceptions
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from recipes.models import (Favorite, Ingredient, Recipe, IngredientRecipe,
                            ShoppingCart, Tag)
from rest_framework import serializers
from rest_framework import status
from rest_framework.exceptions import ValidationError
from users.models import Subscribe, User
from django.db import transaction
from django.shortcuts import get_object_or_404

# from users import models as user_models


#class UserSerializers(UserSerializer):
#    class Meta:
#        model = User
#        fields = (
#            'id',
#            'email',
#            'username',
#            'first_name',
#            'last_name',
#        )
#        read_only_fields = ('id',)


class AvatarSerializer(UserSerializer):
    avatar = Base64ImageField(required=True, allow_null=False)

    class Meta:
        model = User
        fields = ('avatar',)

    def validate(self, data):
        avatar = data.get('avatar')
        if avatar is None:
            raise serializers.ValidationError()
        return data


class UserReadSerializer(UserSerializer):
    """[GET] Cписок пользователей."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name',
                  'avatar', 'is_subscribed')

    def get_is_subscribed(self, obj):
        user_id = self.context.get("request").user.id
        return Subscribe.objects.filter(
            author=obj.id, user=user_id
        ).exists()


class UserCreateSerializers(UserCreateSerializer):
    """[POST] Создание нового пользователя."""

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

    def validate(self, obj):
        invalid_usernames = ['me', 'set_password',
                             'subscriptions', 'subscribe']
        if self.initial_data.get('username') in invalid_usernames:
            raise serializers.ValidationError(
                {'username': 'Вы не можете использовать этот username.'}
            )
        return obj


class SetPasswordSerializer(serializers.Serializer):
    """[POST] Изменение пароля пользователя."""

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
    name = serializers.ReadOnlyField()
    cooking_time = serializers.ReadOnlyField()

    class Meta:
        model = Recipe
        fields = ('id', 'name',
                  'image', 'cooking_time')


class SubscriptionsSerializer(UserReadSerializer):
    """[GET] Список авторов на которых подписан пользователь."""

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
        serializer = RecipeSerializer(recipes, many=True, read_only=True)
        return serializer.data


""" class SubscribeAuthorSerializer(serializers.ModelSerializer):


    email = serializers.ReadOnlyField()
    username = serializers.ReadOnlyField()
    is_subscribed = serializers.SerializerMethodField()
    recipes = RecipeSerializer(many=True, read_only=True)
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'avatar',
                  'username', 'first_name',
                  'last_name', 'is_subscribed',
                  'recipes', 'recipes_count')

    def validate(self, obj):
        if (self.context['request'].user == obj):
            raise serializers.ValidationError({'errors': 'Ошибка подписки.'})
        return obj

    def get_is_subscribed(self, obj):
        return (
            self.context.get('request').user.is_authenticated
            and Subscribe.objects.filter(user=self.context['request'].user,
                                         author=obj).exists()
        )

    def get_recipes_count(self, obj):
        return obj.recipes.count()
 """
# -----------------------------------------------------------------------------
#                            Приложение recipes
# -----------------------------------------------------------------------------


class IngredientSerializer(serializers.ModelSerializer):
    """[GET] Список ингредиентов."""

    class Meta:
        model = Ingredient
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    """[GET] Список тегов."""

    class Meta:
        model = Tag
        fields = '__all__'


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


class RecipeReadSerializer(serializers.ModelSerializer):
    """[GET] Список рецептов."""

    author = UserReadSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = RecipeIngredientSerializer(
        many=True, read_only=True, source='recipes')
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

    def get_is_favorited(self, obj):
        return (
            self.context.get('request').user.is_authenticated
            and Favorite.objects.filter(user=self.context['request'].user,
                                        recipe=obj).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        return (
            self.context.get('request').user.is_authenticated
            and ShoppingCart.objects.filter(
                user=self.context['request'].user,
                recipe=obj).exists()
        )


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    """Ингредиент и количество для создания рецепта."""

    id = serializers.IntegerField(write_only=True)

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'amount')


class RecipeCreateSerializer(serializers.ModelSerializer):
    """[POST, PATCH, DELETE] Создание, изменение и удаление рецепта."""

    tags = serializers.PrimaryKeyRelatedField(many=True,
                                              queryset=Tag.objects.all())
    author = UserReadSerializer(read_only=True)
    id = serializers.ReadOnlyField()
    ingredients = RecipeIngredientCreateSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'ingredients',
                  'tags', 'image',
                  'name', 'text',
                  'cooking_time', 'author')
        extra_kwargs = {
            'ingredients': {'required': True, 'allow_blank': False},
            'tags': {'required': True, 'allow_blank': False},
            'name': {'required': True, 'allow_blank': False},
            'text': {'required': True, 'allow_blank': False},
            'image': {'required': True, 'allow_blank': False},
            'cooking_time': {'required': True},
        }

    def validate_ingredients(self, value):
        ingredients = value
        if not ingredients:
            raise ValidationError({
                'ingredients': 'Нужен хотя бы один ингредиент!'
            })
        ingredients_list = []
        for item in ingredients:
            ingredient = get_object_or_404(Ingredient, id=item['id'])
            if ingredient in ingredients_list:
                raise ValidationError(
                    'Ингредиенты не могут повторяться!'
                )
            if int(item['amount']) <= 0:
                raise ValidationError(
                    'Количество ингредиента должно быть больше 0!'
                )
            ingredients_list.append(ingredient)
        return value

    def validate_tags(self, value):
        tags = value
        if not tags:
            raise ValidationError('Нужно выбрать хотя бы один тег!')
        tags_list = []
        for tag in tags:
            if tag in tags_list:
                raise ValidationError('Теги должны быть уникальными!')
            tags_list.append(tag)
        return value

    """ def validate(self, obj):
        for field in ['name', 'text', 'cooking_time']:
            if not obj.get(field):
                raise serializers.ValidationError(
                    f'{field} - Обязательное поле.'
                )
        if not obj.get('tags'):
            raise serializers.ValidationError(
                'Нужно указать минимум 1 тег.'
            )
        tags = obj.get('tags')
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError('Теги должны быть уникальными')
        if not obj.get('ingredients'):
            raise serializers.ValidationError(
                'Нужно указать минимум 1 ингредиент.'
            )
        inrgedient_id_list = [item['id'] for item in obj.get('ingredients')]
        unique_ingredient_id_list = set(inrgedient_id_list)
        if len(inrgedient_id_list) != len(unique_ingredient_id_list):
            raise serializers.ValidationError(
                'Ингредиенты должны быть уникальны.'
            )
        return obj
 """
    @transaction.atomic
    def create_ingredients_amounts(self, ingredients, recipe):
        IngredientRecipe.objects.bulk_create(
            [IngredientRecipe(
                ingredient=Ingredient.objects.get(id=ingredient['id']),
                recipe=recipe,
                amount=ingredient['amount']
            ) for ingredient in ingredients]
        )

    @transaction.atomic
    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_ingredients_amounts(recipe=recipe,
                                        ingredients=ingredients)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        instance = super().update(instance, validated_data)
        instance.tags.clear()
        instance.tags.set(tags)
        instance.ingredients.clear()
        self.create_ingredients_amounts(recipe=instance,
                                        ingredients=ingredients)
        instance.save()
        return instance

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return RecipeReadSerializer(instance, context=context).data
