from django.contrib.auth import get_user_model
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters import rest_framework as filters
from djoser.views import UserViewSet
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from api.filters import IngredientFilter, RecipeFilter
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
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthorOrReadOnly]
    pagination_class = LimitPagination
    http_method_names = ['get', 'post', 'put', 'delete', 'patch']
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = RecipeFilter

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
        recipe = get_object_or_404(Recipe, id=pk)
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
        for name, unit, amount in RecipeIngredient.objects.filter(
                recipe__shopping_cart__user=self.request.user).values_list(
                    'ingredient__name', 'ingredient__measurement_unit',
                    'amount'):
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
                f"{item} ({shopping_list[item]['unit']}) — "
                f"{shopping_list[item]['amount']}\n")
        response = HttpResponse(purchase_list,
                                'Content-Type: application/txt')
        response['Content-Disposition'] = (
            'attachment; filename="purchase_list.txt"')
        return response

    @action(detail=True, methods=['get', 'delete'],
            permission_classes=[permissions.IsAuthenticated])
    def favorite(self, request, pk=None):
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)
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


class UserSubscriptionViewSet(UserViewSet):
    pagination_class = LimitPagination

    @action(detail=False, methods=['get'],
            permission_classes=[permissions.IsAuthenticated])
    def subscriptions(self, request):
        queryset = (get_user_model().objects
                    .filter(subscribing__subscriber=self.request.user))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = UserSubscriptionSerializer(
                page, many=True, context={'request': self.request})
            return self.get_paginated_response(serializer.data)
        return (Response(UserSubscriptionSerializer(
            queryset, many=True, context={'request': self.request}).data))

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
