from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import (SAFE_METHODS, AllowAny,
                                        IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from .filters import RecipeFilter
from .pagination import MyPagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (EditRecipeSerializer, IngredientsSerializer,
                          RecipeSerializer,
                          ShoppingCartAndFavoriteRecipeSerializer,
                          SubscribeSerializer, TagSerializer, UsersSerializer)
from recipes.models import (FavoriteRecipe, Ingredient, IngredientInRecipe,
                            Recipe, ShoppingCart, Subscribe, Tag, User)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientsSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)
    pagination_class = MyPagination


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    filter_backends = (DjangoFilterBackend,)
    permission_classes = (IsAuthorOrReadOnly,)
    filterset_class = RecipeFilter
    pagination_class = MyPagination

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeSerializer
        return EditRecipeSerializer

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,),
        url_path='shopping_cart',
        url_name='shopping_cart',
    )
    def shopping_cart(self, request, pk):
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)

        if request.method == 'POST':
            if ShoppingCart.objects.filter(user=user, recipe_id=pk).exists():
                return Response("Уже в корзине",
                                status=status.HTTP_400_BAD_REQUEST
                                )
            ShoppingCart.objects.create(user=user, recipe_id=pk)
            serializer = ShoppingCartAndFavoriteRecipeSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            obj = ShoppingCart.objects.filter(user=user, recipe__id=pk)
            if obj.exists():
                obj.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response('Рецепта нет в корзине',
                            status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def get_txt(ingredients):
        if not ingredients:
            return 'Список покупок пуст'
        shops = 'Список покупок:\n'
        for ingredient in ingredients:
            shops += (
                f"{ingredient['ingredient__name']}  - "
                f"{ingredient['sum']} "
                f"({ingredient['ingredient__measurement_unit']})\n"
            )
        return shops

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,),
        url_path='download_shopping_cart',
        url_name='download_shopping_cart',
    )
    def download_shopping_cart(self, request):

        ingredients = IngredientInRecipe.objects.filter(
            recipe__shopping_cart__user=request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(sum=Sum('amount'))
        shopping_list = self.get_txt(ingredients)
        return HttpResponse(shopping_list, content_type='text/plain')

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,),
        url_path='favorite',
        url_name='favorite',
    )
    def favorite_recipe(self, request, pk):
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            if FavoriteRecipe.objects.filter(user=user,
                                             recipe_id=pk).exists():
                return Response('Этот рецепт уже в избранном',
                                status=status.HTTP_400_BAD_REQUEST)
            FavoriteRecipe.objects.create(user=user, recipe_id=pk)
            serializer = ShoppingCartAndFavoriteRecipeSerializer(recipe)
            return Response(serializer.data,
                            status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            obj = FavoriteRecipe.objects.filter(user=user, recipe_id=pk)
            if obj.exists():
                obj.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response('Этого рецепта нет в избранном',
                            status=status.HTTP_400_BAD_REQUEST)


class UsersViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = UsersSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = LimitOffsetPagination

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,),
        url_path='subscriptions',
        url_name='subscriptions',
    )
    def get_subs(self, request):
        user = request.user
        subscribers = User.objects.filter(author__user=user)
        if not subscribers:
            return Response('У вас нет подписок!',
                            status=status.HTTP_400_BAD_REQUEST)
        pages = self.paginate_queryset(subscribers)
        serializer = SubscribeSerializer(pages, many=True,
                                         context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,),
        url_path='subscribe',
        url_name='subscribe',
    )
    def subscribe(self, request, id):
        user = request.user
        author = get_object_or_404(User, id=id)
        sub = Subscribe.objects.filter(user=user.id, author=author)

        if request.method == 'POST':
            if user == author:
                return Response('Нельзя быть подписанным на самого себя',
                                status=status.HTTP_400_BAD_REQUEST)
            if sub.exists():
                return Response('Вы уже подписаны',
                                status=status.HTTP_400_BAD_REQUEST)
            subscribe = Subscribe.objects.create(
                user=user,
                author=author
            )
            subscribe.save()
            return Response('Вы подписались на этого автора',
                            status=status.HTTP_201_CREATED)
        if sub.exists():
            sub.delete()
            return Response(f'Вы отписались от {author}',
                            status=status.HTTP_204_NO_CONTENT)
        return Response(f'Вы не подписаны на {author}',
                        status=status.HTTP_400_BAD_REQUEST)
