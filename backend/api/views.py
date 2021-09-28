from django.contrib.auth import get_user_model
from django.http.response import HttpResponse
from djoser.views import UserViewSet
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView, get_object_or_404
from rest_framework.response import Response

from api.paginations import LimitPagination
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (IngredientSerializer, RecipeCreationSerializer,
                             RecipeSerializer, RecipeShortInfoSerializer,
                             TagSerializer, UserSubscriptionSerializer)
from recipes.models import (FavoriteRecipe, Ingredient, Recipe,
                            RecipeIngredient, ShoppingCart, Tag)
from users.models import Subscription


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.AllowAny]


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = IngredientSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        name = self.request.query_params.get('name')
        queryset = Ingredient.objects.all()
        if name is not None:
            return queryset.filter(name__istartswith=name)
        return queryset


class RecipeViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthorOrReadOnly]
    pagination_class = LimitPagination
    http_method_names = ['get', 'post', 'put', 'delete', 'patch']

    def get_queryset(self):
        true_values = ('1', 'true')
        user = self.request.user
        queryset = Recipe.objects.all()
        author_id = self.request.query_params.get('author')
        tags = self.request.query_params.getlist('tags', '')
        if author_id is not None:
            queryset = queryset.filter(author_id=author_id)
        if tags:
            queryset = queryset.filter(tags__slug__in=tags)
        if user.is_authenticated:
            is_favorited = self.request.query_params.get('is_favorited')
            is_in_shopping_cart = self.request.query_params.get(
                'is_in_shopping_cart')
            if (is_favorited is not None and is_favorited.lower()
                    in true_values):
                queryset = queryset.filter(favorites__user=user)
            if (is_in_shopping_cart is not None and is_in_shopping_cart
                    in true_values):
                queryset = queryset.filter(shopping_cart__user=user)
        return queryset

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RecipeSerializer
        else:
            return RecipeCreationSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['get', 'delete'],
            permission_classes=[permissions.IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        user = request.user
        recipe = Recipe.objects.get(id=pk)
        shopping_cart_record_exists = ShoppingCart.objects.filter(
            recipe=recipe, user=user).exists()
        if request.method == 'GET':
            if shopping_cart_record_exists:
                return Response(
                    {'errors': 'Рецепт уже добавлен в список покупок!'},
                    status=status.HTTP_400_BAD_REQUEST)
            ShoppingCart.objects.create(recipe=recipe, user=user)
            return Response(RecipeShortInfoSerializer(
                instance=recipe, context={'request': request}).data,
                status=status.HTTP_201_CREATED)
        if not shopping_cart_record_exists:
            return Response(
                {'errors': 'Данного рецепта нет в списке покупок!'},
                status=status.HTTP_400_BAD_REQUEST)
        ShoppingCart.objects.filter(recipe=recipe, user=user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'],
            permission_classes=[permissions.IsAuthenticated])
    def download_shopping_cart(self, request):
        shopping_list = {}
        for shopping_cart_item in request.user.shopping_cart.all():
            recipe_ingredient_list = RecipeIngredient.objects.filter(
                recipe=shopping_cart_item.recipe
            )
            for recipe_ingredient in recipe_ingredient_list:
                name = recipe_ingredient.ingredient.name
                amount = recipe_ingredient.amount
                unit = recipe_ingredient.ingredient.measurement_unit
                if name not in shopping_list:
                    shopping_list[name] = {
                        'amount': amount,
                        'unit': unit
                    }
                else:
                    shopping_list[name]['amount'] += amount
        purchase_list = []
        for item in shopping_list:
            purchase_list.append(
                f'{item} ({shopping_list[item]["unit"]}) — '
                f'{shopping_list[item]["amount"]}\n')
        response = HttpResponse(purchase_list,
                                'Content-Type: application/txt')
        response['Content-Disposition'] = (
            'attachment; filename="purchase_list.txt"')
        return response

    @action(detail=True, methods=['get', 'delete'],
            permission_classes=[permissions.IsAuthenticated])
    def favorite(self, request, pk=None):
        user = request.user
        recipe = Recipe.objects.get(id=pk)
        favorite_record_exists = FavoriteRecipe.objects.filter(
            recipe=recipe, user=user).exists()
        if request.method == 'GET':
            if favorite_record_exists:
                return Response(
                    {'errors': 'Рецепт уже добавлен в избранное!'},
                    status=status.HTTP_400_BAD_REQUEST)
            FavoriteRecipe.objects.create(recipe=recipe, user=user)
            return Response(RecipeShortInfoSerializer(
                instance=recipe, context={'request': request}).data,
                status=status.HTTP_201_CREATED)
        if not favorite_record_exists:
            return Response(
                {'errors': 'Данного рецепта нет в избранном!'},
                status=status.HTTP_400_BAD_REQUEST)
        FavoriteRecipe.objects.filter(recipe=recipe, user=user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ListSubscriptions(ListAPIView):
    pagination_class = LimitPagination
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSubscriptionSerializer

    def get_queryset(self):
        return (get_user_model().objects
                .filter(subscribing__subscriber=self.request.user))


class UserSubscriptionViewSet(UserViewSet):
    pagination_class = LimitPagination

    @action(detail=True, methods=['get', 'delete'],
            permission_classes=[permissions.IsAuthenticated])
    def subscribe(self, request, id=None):
        user = request.user
        author = get_object_or_404(get_user_model(), id=id)
        subscription_exists = Subscription.objects.filter(
            subscriber=user, author=author)
        if request.method == 'GET':
            if author.id == user.id:
                return Response(
                    {'errors': 'Нельзя подписаться на самого себя!'},
                    status=status.HTTP_400_BAD_REQUEST)
            if subscription_exists:
                return Response(
                    {'errors': 'Такая подписка уже есть!'},
                    status=status.HTTP_400_BAD_REQUEST)
            Subscription.objects.create(subscriber=user, author=author)
            return Response(UserSubscriptionSerializer(
                instance=author, context={'request': request}).data,
                status=status.HTTP_201_CREATED)
        if not subscription_exists:
            return Response(
                {'errors': 'Такой подписки не существует!'},
                status=status.HTTP_400_BAD_REQUEST)
        Subscription.objects.filter(subscriber=user, author=author).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
