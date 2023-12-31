import django_filters.rest_framework as filters
from rest_framework.filters import SearchFilter

from recipes.models import Recipe


class RecipeFilter(filters.FilterSet):
    tags = filters.AllValuesMultipleFilter(field_name='tags__slug')
    is_favorited = filters.filters.BooleanFilter(
        method='get_is_recipe_in_favorite')
    is_in_shopping_cart = filters.filters.BooleanFilter(
        method='get_is_recipe_in_shoppingcart_filter')

    class Meta:
        model = Recipe
        fields = ['is_favorited', 'is_in_shopping_cart', 'author', 'tags']

    def get_is_recipe_in_favorite(self, queryset, name, value):
        if value:
            user = self.request.user
            return queryset.filter(
                favorite_recipe__user=user)
        return queryset

    def get_is_recipe_in_shoppingcart_filter(self, queryset, name, value):
        if value:
            user = self.request.user
            return queryset.filter(shopping_cart_recipe__user_id=user.id)
        return queryset


class IngredientFilter(SearchFilter):
    search_param = 'name'
