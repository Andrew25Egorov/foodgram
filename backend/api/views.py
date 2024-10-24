from datetime import datetime

from api.pagination import CustomPaginator
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet

from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly,
                                        SAFE_METHODS)
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
#                          SetPasswordSerializer,
                          SubscribeSerializer,
                          SubscriptionsSerializer,
                          TagSerializer,
                          UserReadSerializer)

from shortener import shortener


class CustomUserViewSet(UserViewSet):
    """Вьюсет пользователя."""
    queryset = User.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = CustomPaginator
    serializer_class = UserReadSerializer

    def get_permissions(self):
        if self.action == 'me':
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    # @action(detail=False, methods=['get'],
    #         pagination_class=None,
    #         permission_classes=(IsAuthenticated,))
    # def me(self, request):
    #     serializer = UserReadSerializer(request.user)
    #     return Response(serializer.data,
    #                     status=status.HTTP_200_OK)

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

    @action(detail=False, methods=['PUT'],
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
            {'detail': 'Аватар отсутствует.'},
            status=status.HTTP_400_BAD_REQUEST
        )

# -----------------------------------------------------------------------------
#                            Приложение recipes
# -----------------------------------------------------------------------------


class IngredientViewSet(ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
#    filter_backends = (IngredientFilter,)
    filterset_class = IngredientFilter
    search_fields = ('^name', )
    pagination_class = None


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
#    permission_classes = (IsAdminOrReadOnly,)
    pagination_class = None


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrReadOnly,)
    pagination_class = CustomPaginator
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
#    serializer_class = RecipeReadSerializer

    def get_serializer_class(self):
        """ Выбор сериализатора. """
        if self.request.method in SAFE_METHODS:
            return RecipeReadSerializer
        return RecipeCreateSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['get'],
            url_path='get-link', permission_classes=[AllowAny])
    def short_link(self, request, pk):
        """ Получение короткой ссылки на рецепт. """
        recipe = get_object_or_404(Recipe, pk=pk)
        short_link = self.get_short_link(request.user, recipe.id)
        return Response({'short-link': short_link}, status=status.HTTP_200_OK)

    def get_short_link(self, user, pk):
        """ Создание короткой ссылки для рецепта. """
        return shortener.create(user, pk)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk):
        """Добавление и удаление рецептов из избранного."""
        return self._handle_favorite_or_cart(Favorite, request, pk)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
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
        obj = model.objects.filter(user=user, recipe__id=pk)
        if obj.exists():
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'errors': 'Рецепт уже удален!'},
                        status=status.HTTP_404_NOT_FOUND)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        """Скачивание списка покупок."""
        user = request.user
        if not ShoppingCart.objects.filter(user=user).exists():
            return Response(status=status.HTTP_204_NO_CONTENT)
        # if not user.shopping_user.exists():
        #     return Response(status=status.HTTP_400_BAD_REQUEST)

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
