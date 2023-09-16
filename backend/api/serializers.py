from django.db.models import F
from djoser.serializers import UserCreateSerializer
from drf_base64.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from recipes.models import (FavoriteRecipe, Ingredient, IngredientInRecipe,
                            Recipe, ShoppingCart, Subscribe, Tag, TagRecipe,
                            User)


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
    # password = serializers.CharField(style={"input_type": "password"},
    #                                  write_only=True)

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed')

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Subscribe.objects.filter(user=user, author=obj.id).exists()


class IngredientRecipeSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    author = UsersSerializer(default=serializers.CurrentUserDefault(),
                             required=False)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    ingredients = serializers.SerializerMethodField()

    class Meta:

        model = Recipe
        fields = ('id', 'name', 'text', 'author', 'image', 'ingredients',
                  'tags', 'pub_date', 'cooking_time', 'is_favorited',
                  'is_in_shopping_cart',)

    def get_ingredients(self, obj):
        return obj.ingredients.values(
            'id',
            'name',
            'measurement_unit',
            amount=F('ingredient_list__amount')
        )

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
    author = UsersSerializer(required=False, )

    class Meta:
        model = Recipe
        fields = ('id',
                  'name', 'text', 'author', 'image', 'ingredients',
                  'tags',
                  'pub_date', 'cooking_time')

    def validate(self, data):
        ingredients = data['ingredient_list']

        ingredients_list = []
        for ingr in ingredients:
            if ingr.get('id'):
                ingredient = Ingredient.objects.filter(id=ingr['id'])
                if ingredient in ingredients_list:
                    raise serializers.ValidationError(
                        'Данный ингредиент уже используется')
                ingredients_list.append(ingredient)
        return data

    @staticmethod
    def create_ingredient(ingredients, recipe):
        for ingredient in ingredients:
            IngredientInRecipe.objects.create(
                recipe=recipe,
                ingredient_id=ingredient.get('id'),
                amount=ingredient.get('amount'))

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredient_list')
        tags = validated_data.pop('tags')

        user = self.context.get('request').user
        recipe = Recipe.objects.create(**validated_data, author=user)
        recipe.tags.set(tags)
        for element in ingredients:
            id = element['id']
            ingredient = Ingredient.objects.get(pk=id)
            amount = element['amount']
            IngredientInRecipe.objects.create(
                ingredient=ingredient, recipe=recipe, amount=amount)
        return recipe

    def update(self, instance, validated_data):
        IngredientInRecipe.objects.filter(recipe=instance).delete()
        TagRecipe.objects.filter(recipe=instance).delete()
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredient_list')
        instance.tags.set(tags)
        for element in ingredients:
            id = element['id']
            ingredient = Ingredient.objects.get(pk=id)
            amount = element['amount']
            IngredientInRecipe.objects.create(
                ingredient=ingredient, recipe=instance, amount=amount
            )
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
        read_only_fields = ('is_subscribed',)

    def get_subs_recipes(self, obj):
        request = self.context.get('request')
        recipes = obj.recipes.all()
        recipes_limit = request.query_params.get('recipes_limit')
        if recipes_limit:
            recipes = recipes[:int(recipes_limit)]
        return RecipeSerializer(recipes, many=True,
                                context={'request': request}).data

    @staticmethod
    def get_recipes_count(obj):
        return obj.recipes.count()

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Subscribe.objects.filter(user=user, author=obj.id).exists()


class ShoppingCartAndFavoriteRecipeSerializer(ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class CustomUserCreateSerializer(UsersSerializer):
    password = serializers.CharField(style={"input_type": "password"},
                                     write_only=True)

    class Meta(UsersSerializer.Meta):
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name', 'password')
