from django.http import HttpResponse
from djoser.views import UserViewSet
from rest_framework import status, viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import (IsAuthenticatedOrReadOnly,
                                        SAFE_METHODS,
                                        IsAuthenticated, AllowAny)
from django.db.models import Sum
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from recipes.models import (Tag, User, Recipe, Ingredient,
                            IngredientInRecipe,
                            Subscribe, FavoriteRecipe, ShoppingCard)
from .serializers import (TagSerializer, IngredientsSerializer,
                          RecipeSerializer, UsersSerializer,
                          SubscribeSerializer, EditRecipeSerializer,
                          AddFavoriteRecipeSerializer)
from .filters import RecipeFilter
from .permissions import IsAuthorOrReadOnly
from .pagination import MyPagination


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientsSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)
    pagination_class = (MyPagination,)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    filter_backends = (DjangoFilterBackend,)
    permission_classes = (AllowAny,)
    filterset_class = RecipeFilter
    pagination_class = MyPagination

    def get_serializer_class(self):
        if self.action in SAFE_METHODS:
            return RecipeSerializer
        else:
            return EditRecipeSerializer

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,),
        url_path='shopping_cart',
        url_name='shopping_cart',
    )
    def shopping_cart(self, request, pk):
        """Метод для управления списком покупок"""

        user = request.user
        recipe = Recipe.objects.filter(id=pk)

        if request.method == 'POST':
            if ShoppingCard.objects.filter(user=user, recipe=recipe).exists():
                return Response("Уже в корзине",
                                status=status.HTTP_400_BAD_REQUEST
                                )
            ShoppingCard.objects.create(user=user, recipe=recipe)
            serializer = AddFavoriteRecipeSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            obj = ShoppingCard.objects.filter(user=user, recipe__id=pk)
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
            recipe__shopping_recipe__user=request.user
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
        recipe = Recipe.objects.filter(id=pk)
        if __name__ == '__main__':
            if request.method == 'POST':
                if FavoriteRecipe.objects.filter(user=user,
                                                 recipe=recipe).exists():
                    return Response('Этот рецепт уже в избранном',
                                    status=status.HTTP_400_BAD_REQUEST)
                FavoriteRecipe.objects.create(user=user, recipe=recipe)
                serializer = RecipeSerializer(recipe)
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED)
            if request.method == 'DELETE':
                obj = FavoriteRecipe.objects.filter(user=user, recipe=recipe)
                if obj.exists():
                    obj.delete()
                    return Response(status=status.HTTP_204_NO_CONTENT)
                return Response('Этого рецепта нет в избранном',
                                status=status.HTTP_400_BAD_REQUEST)


class UsersViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = UsersSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = (LimitOffsetPagination,)

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,),
        url_path='subscriptions',
        url_name='subscriptions',
    )
    def get_subs(self, request):
        user = request.user
        queryset = User.objects.filter(follow__user=self.request.user)
        if not queryset:
            return Response('У вас нет подписок!',
                            status=status.HTTP_400_BAD_REQUEST)
        pages = self.paginate_queryset(queryset)
        serializer = SubscribeSerializer(pages, many=True,
                                         context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,),
        url_path='subscriptions',
        url_name='subscriptions',
    )
    def subscribe(self, request, id):
        user = request.user
        author = User.objects.filter(id=id)
        sub = Subscribe.objects.filter(user=user.id, author=author.id)

        if request.method == 'POST':
            if user == author:
                return Response('Нельзя быть подписанным на самого себя',
                                status=status.HTTP_400_BAD_REQUEST)
            if sub.exist():
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
