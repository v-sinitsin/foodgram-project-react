import django_filters

from recipes.models import Ingredient, Recipe, Tag


class IngredientFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(
        field_name='name', method='filter_ingredients')

    class Meta:
        model = Ingredient
        fields = ['name']

    def filter_ingredients(self, queryset, name, value):
        return (queryset.filter(name__istartswith=value).extra({'order': 1}).
                union(queryset.filter(name__icontains=value).
                      exclude(name__istartswith=value).
                      extra({'order': 2})).order_by('order', 'name'))


class RecipeFilter(django_filters.FilterSet):
    tags = django_filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all()
    )
    is_favorited = django_filters.BooleanFilter(method='get_favorites')
    is_in_shopping_cart = django_filters.BooleanFilter(
        method='get_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = ('is_favorited', 'is_in_shopping_cart', 'author', 'tags')

    def get_favorites(self, queryset, name, value):
        if value:
            return queryset.filter(favorites__user=self.request.user)
        return queryset

    def get_in_shopping_cart(self, queryset, name, value):
        if value:
            return queryset.filter(shopping_cart__user=self.request.user)
        return queryset
