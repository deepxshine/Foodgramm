from django.core.exceptions import ValidationError
import django_filters as filters

from recipes.models import User, Ingredient, Recipe


class RecipeFilter(filters.FilterSet):
    tags = filters.AllValuesMultipleFilter(field_name='tags__slug')
    is_favorited = filters.filters.NumberFilter(
        method='get_is_favorited')
    is_in_shopping_cart = filters.filters.NumberFilter(
        method='get_is_recipe_in_shoppingcart_filter')

    class Meta:
        model = Recipe
        fields = ['is_favorited', 'is_in_shopping_cart', 'author', 'tags']

    def get_is_favorited(self, queryset, name, value):
        if value == 1:
            user = self.request.user
            return queryset.filter(favorite_recipe__user_id=user.id)
        return queryset

    def get_is_recipe_in_shoppingcart_filter(self, queryset, name, value):
        if value == 1:
            user = self.request.user
            return queryset.filter(cart_recipe__user_id=user.id)
        return queryset
