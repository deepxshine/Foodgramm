from django.urls import include, path
from rest_framework import routers

from .views import IngredientsViewSet, TagViewSet, RecipeViewSet, UsersViewSet

router = routers.DefaultRouter()
router.register('ingredients', IngredientsViewSet)
router.register('users', UsersViewSet)
router.register('tags', TagViewSet)
router.register('ingredients', IngredientsViewSet)
router.register('recipes', RecipeViewSet)

urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls))
]
