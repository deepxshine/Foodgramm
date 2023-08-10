from django.urls import include, path
from rest_framework import routers

from .views import (IngredientsViewSet, TagViewSet, RecipeViewSet, UsersViewSet)

router = routers.DefaultRouter()
# router.register(
#     r'recipes/(?P<recipe_id>\d+)/favorite',
#     FavoriteRecipeViewSet,
#     basename='favorite'
# )
# router.register(
#     r'recipes/(?P<recipe_id>\d+)/shopping_cart',
#     ShoppingCartViewSet,
#     basename='favorite'
# )
# router.register(
#     r'users/(?P<recipe_id>\d+)/subscribe',
#     SubscribeViewSet,
#     basename='subscribe'
# )
router.register('ingredients', IngredientsViewSet)
router.register('users', UsersViewSet)
router.register('tags', TagViewSet)

router.register('recipes', RecipeViewSet)

urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls))
]
