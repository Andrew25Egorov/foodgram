from django_filters import ModelMultipleChoiceFilter
from django_filters.rest_framework import FilterSet, filters

from recipes.models import Ingredient, Recipe, Tag


class IngredientFilter(FilterSet):
    """Фильтр по названию для ингредиентов."""
    name = filters.CharFilter(lookup_expr='startswith')

    class Meta:
        """Класс Meta."""

        model = Ingredient
        fields = ['name']


class RecipeFilter(FilterSet):
    """Фильтр для отображения рецептов."""
    tags = ModelMultipleChoiceFilter(field_name='tags__slug',
                                     to_field_name='slug',
                                     queryset=Tag.objects.all())
    is_favorited = filters.BooleanFilter(
        method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart')

    class Meta:
        """Класс Meta."""

        model = Recipe
        fields = ('author', 'tags', 'is_favorited',
                  'is_in_shopping_cart')

    def filter_is_favorited(self, queryset, name, value):
        """Метод для избранного."""
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(favorite_recipe__user=user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        """Метод для списка покупок."""
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(shopping_recipe__user=user)
        return queryset
