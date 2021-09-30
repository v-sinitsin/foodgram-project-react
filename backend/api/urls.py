from django.urls import include, path
from rest_framework.routers import SimpleRouter

from api.views import (IngredientViewSet, RecipeViewSet, TagViewSet,
                       UserSubscriptionViewSet)

router = SimpleRouter()
router.register(r'tags', TagViewSet, basename='tag')
router.register(r'ingredients', IngredientViewSet, basename='ingredient')
router.register(r'recipes', RecipeViewSet, basename='recipe')
router.register(r'users', UserSubscriptionViewSet)

urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls)),
]
