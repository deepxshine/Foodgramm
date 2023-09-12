from django.contrib import admin

from recipes.models import (FavoriteRecipe, Ingredient, IngredientInRecipe,
                            Recipe, ShoppingCart, Subscribe, Tag, TagRecipe)


class IngredientsInRecipe(admin.TabularInline):
    model = IngredientInRecipe
    extra = 1


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'color', 'slug')


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'pk', 'name', 'author', 'get_tags', 'get_favorites')
    list_filter = ('author', 'name', 'tags')
    search_fields = ('name',)
    inlines = IngredientsInRecipe,

    def get_favorites(self, obj):
        return obj.favorites.count()

    def get_tags(self, obj):
        return '\n'.join(obj.tags.values_list('name', flat=True))


@admin.register(Ingredient)
class Ingredient(admin.ModelAdmin):
    search_fields = ('name',)


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    pass


@admin.register(Subscribe)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'author')
    search_fields = ('user', 'author')
    list_filter = ('user', 'author')


@admin.register(FavoriteRecipe)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'recipe')


@admin.register(TagRecipe)
class TagRecipeAdmin(admin.ModelAdmin):
    list_display = ('pk', 'tag', 'recipe')
