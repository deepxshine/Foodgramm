from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

User = get_user_model()


class Ingredient(models.Model):
    name = models.CharField(max_length=100,
                            verbose_name='name of the ingredient')
    measurement_unit = models.CharField(max_length=15,
                                        verbose_name='unit of measurement')

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=52, verbose_name='name of the tag')
    slug = models.CharField(max_length=52, unique=True, verbose_name='slug')
    color = models.CharField(max_length=7, unique=True,
                             verbose_name='HEX color')

    def __str__(self):
        return self.name


class Recipe(models.Model):
    name = models.CharField(max_length=200, verbose_name='name of the recipe')
    text = models.TextField(verbose_name='description')
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='recipes',
                               verbose_name='Author')
    image = models.ImageField(verbose_name='image', upload_to='static/recipe/')
    ingredients = models.ManyToManyField(Ingredient,
                                         through='IngredientInRecipe',
                                         related_name='recipes',
                                         verbose_name='ingredients')
    tags = models.ManyToManyField(Tag, verbose_name='Tags',
                                  related_name='recipes')
    pub_date = models.DateTimeField(auto_now=True, verbose_name='Date')
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления',
        validators=(MinValueValidator(
            limit_value=1,
            message='Время приготовления не может быть меньше одной минуты'),
        )
    )

    class Meta:
        ordering = ['-pub_date']

    def __str__(self):
        return self.name


class IngredientInRecipe(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               related_name='ingredient_list',
                               verbose_name='recipes', )
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE,
                                   verbose_name='ingredient',
                                   related_name='ingredient_list'
                                   )
    amount = models.PositiveSmallIntegerField(
        verbose_name='amount',
        validators=[MinValueValidator(1,
                                      message='Вы указали меньше 0!'), ])

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='unique_ingredients_in_the_recipe'
            )
        ]


class FavoriteRecipe(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='favorites',
                             verbose_name='favorite recipe')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               related_name='favorite_recipe', )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'], name='unique_favorite_recipe'
            )
        ]


class ShoppingCart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='shopping_cart', )
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               related_name='shopping_cart_recipe', )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'], name='unique_item_in_shopping_card'
            )
        ]


class TagRecipe(models.Model):
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE,
                            related_name='tag_recipe', )
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               related_name='tag_recipe', )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['tag', 'recipe'],
                                    name='unique_tag_recipe')]


class Subscribe(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='subscribe')
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='subscriber')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['author', 'user'],
                                    name='unique_sub')]
