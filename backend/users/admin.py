from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser, Subscription


class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Extra Fields', {'fields': ('avatar',)}),
    )
    search_fields = ('username', 'email')


class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'subscribed_to')
    search_fields = (
        'user__username',
        'user__email',
        'subscribed_to__username',
        'subscribed_to__email'
    )


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Subscription, SubscriptionAdmin)
