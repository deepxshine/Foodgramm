from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from djoser.serializers import UserCreateSerializer
from recipes.models import (Tag, Ingredient, Recipe, User, IngredientInRecipe,
                            Subscribe, ShoppingCart, FavoriteRecipe, )
from drf_base64.fields import Base64ImageField


# class Base64ImageField(serializers.ImageField):
#
#     def to_internal_value(self, data):
#         if isinstance(data, str) and data.startswith('data:image'):
#             format, imgstr = data.split(';base64,')
#             ext = format.split('/')[-1]
#             data = ContentFile(base64.b64decode(imgstr), name='photo.' + ext)
#
#         return super().to_internal_value(data)


class TagSerializer(ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug', 'color',)


class IngredientsSerializer(ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('name', 'measurement_unit', 'id')


class UsersSerializer(UserCreateSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        # fields = ('id', 'first_name', 'last_name', 'username', 'email',)
        fields = ('__all__')

    def get_is_subscribed(self, obj):
        """Метод проверки подписки"""

        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Subscribe.objects.filter(user=user, author=obj.id).exists()


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    author = UsersSerializer(default=serializers.CurrentUserDefault(),
                             required=False)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:

        model = Recipe
        fields = ('id',
                  'name', 'text', 'author', 'image', 'ingredients',
                  'tags',
                  'pub_date', 'cooking_time', 'is_favorited',
                  'is_in_shopping_cart',)

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return FavoriteRecipe.objects.filter(
            user=request.user, recipe=obj
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(
            user=request.user, recipe=obj
        ).exists()


class EditIngredientsSerializer(ModelSerializer):
    id = serializers.IntegerField()

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'amount')


class EditRecipeSerializer(ModelSerializer):
    image = Base64ImageField()
    ingredients = EditIngredientsSerializer(
        source='ingredient_list', many=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all()
    )

    # author = UsersSerializer(default=serializers.CurrentUserDefault(),)

    class Meta:
        model = Recipe
        fields = ('id',
                  'name', 'text', 'author', 'image', 'ingredients',
                  'tags',
                  'pub_date', 'cooking_time')

    def validate(self, data):
        print(data)
        ingredients = data['ingredient_list']

        ingredients_list = []
        for i in ingredients:
            ingredient = get_object_or_404(Ingredient, id=i['id'])
            if ingredient in ingredients_list:
                raise serializers.ValidationError(
                    'Данный ингредиент уже используется')
            ingredients_list.append(ingredient)
        return data

    @staticmethod
    def create_ingredient(ingredients, recipe):
        for ingredient in ingredients:
            IngredientInRecipe.objects.create(recipe=recipe,
                                              ingredient=ingredient.get(
                                                  'id'),
                                              amount=ingredient.get('amount'))

    def create(self, validated_data):
        print(1)
        ingredients = validated_data.pop('ingredient_list')
        tags = validated_data.pop('tags')
        print(1)
        user = self.context.get('request').user.id
        print(user)
        recipe = Recipe.objects.create(**validated_data, author=user)
        recipe.tags.set(tags)
        self.create_ingredient(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        if 'ingredient_list' in validated_data:
            ingredients = validated_data.pop('ingredient_list')
            instance.ingredients.clear()
            self.create_ingredient(ingredients, instance)
        return super().update(instance, validated_data)


class SubscribeSerializer(ModelSerializer):
    recipes = serializers.SerializerMethodField(
        read_only=True,
        method_name='get_subs_recipes')
    recipes_count = serializers.SerializerMethodField(
        read_only=True
    )
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count',)

    def get_subs_recipes(self, obj):
        request = self.context.get('request')
        recipes = obj.recipes.all()
        recipes_limit = request.query_params.get('recipes_limit')
        if recipes_limit:
            recipes = recipes[:int(recipes_limit)]
        return RecipeSerializer(recipes, many=True).data

    @staticmethod
    def get_recipes_count(obj):
        return obj.recipes.count()

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Subscribe.objects.filter(user=user, author=obj.id).exists()


# class FavoriteRecipeSerializer(ModelSerializer):
#     # image = Base64ImageField()
#
#     class Meta:
#         model = Recipe
#         fields = ('id', 'name', 'image', 'cooking_time')


class ShoppingCartAndFavoriteRecipeSerializer(ModelSerializer):
    # image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
