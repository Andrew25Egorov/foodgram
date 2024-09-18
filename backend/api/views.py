from datetime import datetime

from api.pagination import CustomPaginator
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
# from foodgram.settings import FILE_NAME

from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, SAFE_METHODS, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from users.models import Subscribe, User
from recipes.models import (Favorite, Ingredient, Recipe, IngredientRecipe,
                            ShoppingCart, Tag)
from .filters import IngredientFilter, RecipeFilter
from .permissions import IsAdminOrReadOnly, IsAuthorOrReadOnly
from .serializers import (AvatarSerializer,
                          IngredientSerializer, RecipeCreateSerializer,
                          RecipeReadSerializer, RecipeSerializer,
                          SetPasswordSerializer,
                          SubscriptionsSerializer, TagSerializer,
                          UserReadSerializer)

from shortener import shortener
# from apps.shortener import shortener

# from users import models as user_models

# from .serializers import UserSerializers


# class UserViewSet(BaseUserViewSet):
#    queryset = user_models.User.objects.all()
#    serializer_class = UserSerializers


class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    pagination_class = CustomPaginator
    serializer_class = UserReadSerializer

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, id=None):
        """Подписка на автора."""
        author = get_object_or_404(User, pk=id)
        user = self.request.user

        if self.request.method == 'POST':
            if user == author:
                return Response(
                    {'errors': 'Нельзя подписаться или отписаться от себя!'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if Subscribe.objects.filter(user=user, author=author).exists():
                return Response(
                    {'errors': 'Подписка уже оформлена!'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            serializer = SubscriptionsSerializer(author, data=request.data,
                                                 context={'request': request})
            serializer.is_valid(raise_exception=True)
            Subscribe.objects.create(user=user, author=author)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if self.request.method == 'DELETE':
            get_object_or_404(Subscribe, user=user,
                              author=author).delete()
            return Response({'detail': 'Успешная отписка'},
                            status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=("get",),
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        """Список авторов, на которых подписан пользователь."""
        user = self.request.user
        queryset = User.objects.filter(subscribing__user=user)
        limit = self.paginate_queryset(queryset)
        serializer = SubscriptionsSerializer(limit, many=True,
                                             context={'request': request})
        return self.get_paginated_response(serializer.data)

    """ @action(detail=False, methods=['get'],
            pagination_class=None,
            permission_classes=(IsAuthenticated,))
    def me(self, request):
        serializer = UserReadSerializer(request.user)
        return Response(serializer.data,
                        status=status.HTTP_200_OK)
 """
    @action(detail=False, methods=['post'],
            permission_classes=(IsAuthenticated,))
    def set_password(self, request):
        serializer = SetPasswordSerializer(request.user, data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
        return Response({'detail': 'Пароль успешно изменен!'},
                        status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['put'],
            url_path='me/avatar',
            permission_classes=[IsAuthenticated],
            )
    def avatar(self, request, *args, **kwargs):
        """Добавление-обновление аватара пользователя."""
        serializer = AvatarSerializer(request.user, data=request.data)

        if not request.data.get('avatar'):
            return Response(
                {'detail': 'Поле avatar обязательно.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @avatar.mapping.delete
    def delete_avatar(self, request, *args, **kwargs):
        """Удаление аватара пользователя."""
        user = request.user
        if user.avatar:
            user.avatar.delete()
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'detail': 'Аватар отсутствует.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    """ def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return UserReadSerializer
        return UserCreateSerializers

    @action(detail=False, methods=['get'],
            pagination_class=None,
            permission_classes=(IsAuthenticated,))
    def me(self, request):
        serializer = UserReadSerializer(request.user)
        return Response(serializer.data,
                        status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'],
            permission_classes=(IsAuthenticated,))
    def set_password(self, request):
        serializer = SetPasswordSerializer(request.user, data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
        return Response({'detail': 'Пароль успешно изменен!'},
                        status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['put'], url_path='me/avatar',
            permission_classes=[IsAuthenticated])
    def avatar(self, request, *args, **kwargs):
    
        serializer = AvatarSerializer(request.user, data=request.data)

        if not request.data.get('avatar'):
            return Response(
                {'detail': 'Поле avatar обязательно.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @avatar.mapping.delete
    def delete_avatar(self, request, *args, **kwargs):

        user = request.user
        if user.avatar:
            user.avatar.delete()
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'detail': 'Аватар отсутствует.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=False, methods=['get'],
            permission_classes=(IsAuthenticated,),
            pagination_class=CustomPaginator)
    def subscriptions(self, request):
    
        queryset = User.objects.filter(subscribing__user=request.user)
        page = self.paginate_queryset(queryset)
        serializer = SubscriptionsSerializer(page, many=True,
                                             context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=(IsAuthenticated,))
    def subscribe(self, request, **kwargs):

        author = get_object_or_404(User, id=kwargs['pk'])

        if request.method == 'POST':
            serializer = SubscriptionsSerializer(
                author, data=request.data, context={"request": request})
            serializer.is_valid(raise_exception=True)
            Subscribe.objects.create(user=request.user, author=author)
            return Response(serializer.data,
                            status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            get_object_or_404(Subscribe, user=request.user,
                              author=author).delete()
            return Response({'detail': 'Успешная отписка'},
                            status=status.HTTP_204_NO_CONTENT) """

# -----------------------------------------------------------------------------
#                            Приложение recipes
# -----------------------------------------------------------------------------


class IngredientViewSet(ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    search_fields = ('^name', )


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsAdminOrReadOnly,)


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrReadOnly | IsAdminOrReadOnly,)
    pagination_class = CustomPaginator
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_short_link(self, user, pk):
        return shortener.create(user, pk)

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeReadSerializer
        return RecipeCreateSerializer

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk):
        """Добавление и удаление рецептов из избранного."""
        if request.method == 'POST':
            return self.add_to(Favorite, request.user, pk)
        else:
            return self.delete_from(Favorite, request.user, pk)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk):
        if request.method == 'POST':
            return self.add_to(ShoppingCart, request.user, pk)
        else:
            return self.delete_from(ShoppingCart, request.user, pk)

    def add_to(self, model, user, pk):
        """Добавление рецепта."""
        if model.objects.filter(user=user, recipe__id=pk).exists():
            return Response({'errors': 'Рецепт уже добавлен!'},
                            status=status.HTTP_400_BAD_REQUEST)
        recipe = get_object_or_404(Recipe, id=pk)
        model.objects.create(user=user, recipe=recipe)
        serializer = RecipeSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_from(self, model, user, pk):
        obj = model.objects.filter(user=user, recipe__id=pk)
        if obj.exists():
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'errors': 'Рецепт уже удален!'},
                        status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        user = request.user
        if not user.shopping_cart.exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)

        ingredients = IngredientRecipe.objects.filter(
            recipe__shopping_cart__user=request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(amount=Sum('amount'))

        today = datetime.today()
        shopping_list = (
            f'Список покупок для: {user.get_full_name()}\n\n'
            f'Дата: {today:%Y-%m-%d}\n\n'
        )
        shopping_list += '\n'.join([
            f'- {ingredient["ingredient__name"]} '
            f'({ingredient["ingredient__measurement_unit"]})'
            f' - {ingredient["amount"]}'
            for ingredient in ingredients
        ])
        shopping_list += f'\n\nFoodgram ({today:%Y})'

        filename = f'{user.username}_shopping_list.txt'
        response = HttpResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename={filename}'

        return response
