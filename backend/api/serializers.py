from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from djoser.serializers import UserCreateSerializer
from recipes.models import Tag, Ingredient, Recipe, User, IngredientInRecipe, \
    Subscribe, ShoppingCart, FavoriteRecipe
from drf_base64.fields import Base64ImageField


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
    """Сериализатор для рецептов."""

    tags = TagSerializer(many=True)
    author = UsersSerializer()

    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        """Мета-параметры сериализатора"""

        model = IngredientInRecipe
        fields = ('id', 'tags', 'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart', 'name',
                  'image', 'text', 'cooking_time'
                  )

    def get_is_favorited(self, obj):
        """Метод проверки на добавление в избранное."""

        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return FavoriteRecipe.objects.filter(
            user=request.user, recipe=obj
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        """Метод проверки на присутствие в корзине."""

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
        # fields = ('id', 'amount')
        fields = ('__all__')


class EditRecipeSerializer(ModelSerializer):
    image = Base64ImageField()
    ingredients = EditIngredientsSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all()
    )

    class Meta:
        model = Recipe
        fields = (
            'name', 'description', 'author', 'image', 'ingredients', 'tags',
            'pub_date', 'cooking_time')

    def validate(self, data):
        ingredients = data['ingredients']
        ingredients_list = []
        for i in ingredients_list:
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
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_ingredient(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        if 'ingredients' in validated_data:
            ingredients = validated_data.pop('ingredients')
            instance.ingredients.clear()
            self.create_ingredient(ingredients, instance)
        return super().update(instance, validated_data)


class SubscribeSerializer(ModelSerializer):
    pass


class FavoriteRecipe(ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
