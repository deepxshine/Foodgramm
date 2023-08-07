from django.contrib import admin
from recipes.models import Tag, Recipe, Ingredient, IngredientInRecipe


class IngredientsInRecipe(admin.TabularInline):
    model = IngredientInRecipe
    extra = 1

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    pass


@admin.register(Recipe)
class Recipe(admin.ModelAdmin):
    inlines = (IngredientsInRecipe,)

@admin.register(Ingredient)
class Ingredient(admin.ModelAdmin):
    pass
