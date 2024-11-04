"""Модуль вьюсетов."""
from datetime import datetime

from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly,
                                        SAFE_METHODS)
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from shortlink.models import ShortLink

from recipes.models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                            ShoppingCart, Tag)
from users.models import Subscribe, User
from .filters import IngredientFilter, RecipeFilter
from .pagination import CustomPaginator
from .permissions import IsAdminOrReadOnly, IsAuthorOrReadOnly
from .serializers import (AvatarSerializer, IngredientSerializer,
                          RecipeCreateSerializer, RecipeReadSerializer,
                          RecipeSerializer, SubscribeSerializer,
                          SubscriptionsSerializer, TagSerializer,
                          UserReadSerializer)


class CustomUserViewSet(UserViewSet):
    """Вьюсет пользователя."""
    queryset = User.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = CustomPaginator
    serializer_class = UserReadSerializer

    def get_permissions(self):
        """Получение разрешений."""
        if self.action == 'me':
            self.permission_classes = (IsAuthenticated,)
        return super().get_permissions()

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, id):
        """Подписка на автора."""
        author = get_object_or_404(User, id=id)
        user = self.request.user
        subscribing = Subscribe.objects.filter(user=user, author=author)

        if self.request.method == 'POST':
            if user == author:
                return Response(
                    {'errors': 'Нельзя подписаться или отписаться от себя!'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if subscribing.exists():
                return Response(
                    {'errors': 'Вы уже подписаны на этого автора!'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            queryset = Subscribe.objects.create(user=user, author=author)
            serializer = SubscribeSerializer(
                queryset, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            if not subscribing.exists():
                return Response(
                    {'errors': 'Вы уже отписаны от этого автора!'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            subscribing.delete()
            return Response({'detail': 'Вы успешно отписались!'},
                            status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(
        detail=False,
        methods=('get',),
        permission_classes=[IsAuthenticated],
        pagination_class=CustomPaginator
    )
    def subscriptions(self, request):
        """Список авторов, на которых подписан пользователь."""
        queryset = User.objects.filter(subscribing__user=self.request.user)
        limit = self.paginate_queryset(queryset)
        serializer = SubscriptionsSerializer(limit, many=True,
                                             context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(
        detail=False,
        methods=['PUT'],
        url_path='me/avatar',
        permission_classes=[IsAuthenticated],
    )
    def avatar(self, request, *args, **kwargs):
        """Добавление и обновление аватара пользователя."""
        serializer = AvatarSerializer(request.user, data=request.data)

        if 'avatar' not in request.data:
            return Response(
                {'errors': 'Поле avatar обязательное.'},
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
            {'errors': 'Аватар отсутствует.'},
            status=status.HTTP_400_BAD_REQUEST
        )


class IngredientViewSet(ReadOnlyModelViewSet):
    """Вьюсет ингредиентов."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    filterset_class = IngredientFilter
    search_fields = ('^name', )
    pagination_class = None


class TagViewSet(ReadOnlyModelViewSet):
    """Вьюсет тегов."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class RecipeViewSet(ModelViewSet):
    """Вьюсет рецептов."""
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrReadOnly,)
    pagination_class = CustomPaginator
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        """Выбор сериализатора."""
        if self.request.method in SAFE_METHODS:
            return RecipeReadSerializer
        return RecipeCreateSerializer

    def perform_create(self, serializer):
        """Сохранение нового рецепта с автором."""
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        """Изменение рецепта."""
        serializer.save(partial=True)

    @action(
        detail=True,
        methods=['get'],
        url_path='get-link',
        permission_classes=(AllowAny,)
    )
    def short_link(self, request, pk=None):
        """Получение короткой ссылки на рецепт."""
        recipe = self.get_object()
        short_link = self.get_short_link(recipe)
        return Response({'short-link': short_link}, status=status.HTTP_200_OK)

    def get_short_link(self, recipe):
        """Создание короткой ссылки для рецепта."""
        short_link = ShortLink.objects.create(
            full_url=f'/recipes/{recipe.id}/'
        )
        return short_link.short_url

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, pk):
        """Добавление и удаление рецептов из избранного."""
        return self._handle_favorite_or_cart(Favorite, request, pk)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, pk):
        """Добавление и удаление рецептов из покупок."""
        return self._handle_favorite_or_cart(ShoppingCart, request, pk)

    def _handle_favorite_or_cart(self, model, request, pk):
        """Обработка добавления и удаления из избранного или покупок."""
        if request.method == 'POST':
            return self.add_to(model, request.user, pk)
        return self.delete_from(model, request.user, pk)

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
        """Удаление рецепта."""
        recipe = get_object_or_404(Recipe, id=pk)
        obj = model.objects.filter(user=user, recipe=recipe)
        if obj.exists():
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'errors': 'Этот рецепт не был добавлен!'},
                        status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        """Скачивание списка покупок."""
        user = request.user
        if not ShoppingCart.objects.filter(user=user).exists():
            return Response(status=status.HTTP_204_NO_CONTENT)

        ingredients = IngredientRecipe.objects.filter(
            recipe__shopping_recipe__user=user
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
        shopping_list += f'\n\nсформировано сервисом "Foodgram" ({today:%Y})'
        filename = f'{user.username}_shopping_list.txt'
        response = HttpResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename={filename}'

        return response
