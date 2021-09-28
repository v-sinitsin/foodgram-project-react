from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from recipes.models import FavoriteRecipe, ShoppingCart
from users.models import Subscription, User


class FavoriteInline(admin.TabularInline):
    model = FavoriteRecipe


class ShoppingCartInline(admin.TabularInline):
    model = ShoppingCart


class SubscriptionInline(admin.TabularInline):
    model = Subscription
    fk_name = 'subscriber'


@admin.register(User)
class UserAdmin(UserAdmin):
    list_filter = ('email', 'username')
    inlines = [FavoriteInline, ShoppingCartInline, SubscriptionInline]
