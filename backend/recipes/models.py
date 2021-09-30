from colorfield.fields import ColorField
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

User = get_user_model()


class Tag(models.Model):
    name = models.CharField(max_length=200, verbose_name='Название')
    color = ColorField(default='#000000', verbose_name='Цвет')
    slug = models.SlugField(max_length=200, verbose_name='Slug')

    class Meta:
        ordering = ['name']
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        constraints = [
            models.UniqueConstraint(fields=['slug'],
                                    name='unique_tag_slug'),
            models.UniqueConstraint(fields=['name'], name='unique_tag_name')
        ]

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(max_length=300, verbose_name='Название')
    measurement_unit = models.CharField(
        max_length=10, verbose_name='Единица измерения')

    class Meta:
        ordering = ['name']
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient_name_measurement_unit')
        ]

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='recipes',
        null=True, verbose_name='Автор')
    name = models.CharField(max_length=300, verbose_name='Название')
    image = models.ImageField(
        upload_to='recipes/images', verbose_name='Изображение')
    text = models.TextField(verbose_name='Описание')
    ingredients = models.ManyToManyField(
        Ingredient, through='RecipeIngredient', verbose_name='Ингредиенты')
    tags = models.ManyToManyField(Tag, verbose_name='Теги')
    cooking_time = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1, 'Значение должно быть больше 1!')],
        verbose_name='Время приготовления')
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name

    def favorites_count(self):
        return self.favorites.count()

    favorites_count.short_description = 'Количество добавлений в избранное'


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, verbose_name='Рецепт')
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE, verbose_name='Ингредиент')
    amount = models.PositiveIntegerField(
        validators=[MinValueValidator(1, 'Значение должно быть больше 1!')],
        verbose_name='Количество')

    class Meta:
        verbose_name = 'Ингредиент рецепта'
        verbose_name_plural = 'Ингредиенты рецептов'
        constraints = [
            models.UniqueConstraint(fields=['recipe', 'ingredient'],
                                    name='unique_recipeingredient')
        ]

    def __str__(self):
        return (f'{self.recipe.name}: {self.ingredient.name}'
                f' ({self.amount})')


class FavoriteRecipe(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='favorites',
        verbose_name='Пользователь')
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='favorites',
        verbose_name='Рецепт')
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = [
            models.UniqueConstraint(fields=['user', 'recipe'],
                                    name='unique_favoriterecipe')
        ]

    def __str__(self):
        return f'{self.user.username}: {self.recipe.name}'


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='shopping_cart',
        verbose_name='Пользователь')
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE,
        related_name='shopping_cart', verbose_name='Рецепт')
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'
        constraints = [
            models.UniqueConstraint(fields=['user', 'recipe'],
                                    name='unique_shoppingcart')
        ]

    def __str__(self):
        return f'{self.user.username}: {self.recipe.name}'
