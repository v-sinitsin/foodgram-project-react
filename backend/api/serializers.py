from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.models import (FavoriteRecipe, Ingredient, Recipe,
                            RecipeIngredient, ShoppingCart, Tag)
from users.models import Subscription


class UserRegisterSerializer(UserCreateSerializer):
    class Meta(UserCreateSerializer.Meta):
        fields = ('id', 'email', 'username', 'last_name',
                  'first_name', 'password')
        read_only_fields = ['id']


class UserInfoSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = (
            'id',
            'email',
            'username',
            'last_name',
            'first_name',
            'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request', None)
        if request is None or request.user.is_anonymous:
            return False
        return Subscription.objects.filter(
            subscriber=request.user, author=obj).exists()


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ['id', 'name', 'measurement_unit', 'amount']


class RecipeSerializer(serializers.ModelSerializer):
    author = UserInfoSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        exclude = ['created_at']

    def get_ingredients(self, obj):
        return RecipeIngredientSerializer(
            RecipeIngredient.objects.filter(recipe=obj), many=True).data

    def get_is_favorited(self, obj):
        request = self.context.get('request', None)
        if request is None or request.user.is_anonymous:
            return False
        return FavoriteRecipe.objects.filter(
            user=request.user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request', None)
        if request is None or request.user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(
            user=request.user, recipe=obj).exists()


class IngredientRecipeCreationSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

    class Meta:
        model = RecipeIngredient
        fields = ['id', 'amount']


class RecipeCreationSerializer(serializers.ModelSerializer):
    ingredients = IngredientRecipeCreationSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True)
    image = Base64ImageField()
    author = UserInfoSerializer(read_only=True)

    class Meta:
        model = Recipe
        fields = ['id', 'tags', 'author', 'ingredients',
                  'name', 'image', 'text', 'cooking_time']

    def create(self, validated_data):
        tags_data = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        for tag in tags_data:
            recipe.tags.add(Tag.objects.get(id=tag.id))
        for ingredient in ingredients_data:
            RecipeIngredient.objects.create(
                recipe=recipe, amount=ingredient['amount'],
                ingredient=ingredient['id'])
        return recipe

    def to_representation(self, instance):
        return RecipeSerializer(instance).data

    def update(self, instance, validated_data):
        instance.tags.clear()
        instance.ingredients.clear()
        tags_data = validated_data['tags']
        ingredients_data = validated_data['ingredients']
        for tag in tags_data:
            instance.tags.add(Tag.objects.get(id=tag.id))
        for ingredient in ingredients_data:
            RecipeIngredient.objects.create(
                recipe=instance, amount=ingredient['amount'],
                ingredient=ingredient['id'])
        instance.name = validated_data['name']
        instance.text = validated_data['text']
        instance.image = validated_data['image']
        instance.cooking_time = validated_data['cooking_time']
        instance.save()
        return instance


class RecipeShortInfoSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ['id', 'name', 'image', 'cooking_time']


class UserSubscriptionSerializer(UserInfoSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(UserInfoSerializer.Meta):
        fields = (
            'id',
            'email',
            'username',
            'last_name',
            'first_name',
            'is_subscribed',
            'recipes',
            'recipes_count'
        )

    def get_recipes_count(self, obj):
        return obj.recipes.filter(author=obj).count()

    def get_recipes(self, obj):
        recipes = Recipe.objects.filter(author=obj).order_by(
            'created_at')
        recipes_limit = self.context['request'].query_params.get(
            'recipes_limit', None)
        if recipes_limit is not None:
            recipes = recipes[:int(recipes_limit)]
        return RecipeShortInfoSerializer(recipes, many=True).data
