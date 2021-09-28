from django.contrib import admin

from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag


class IngredientRecipeInline(admin.TabularInline):
    model = RecipeIngredient


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'favorites_count')
    list_filter = ('author', 'name', 'tags__name')
    inlines = [IngredientRecipeInline]


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')


admin.site.register(Tag)
