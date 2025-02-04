from django.contrib import admin
from .models import FavoritePublication, FavoriteUser


class FavoritePublicationAdmin(admin.ModelAdmin):
    list_display = ('user', 'publication', 'created_at')
    search_fields = ('user__email', 'publication__title')
    list_filter = ('created_at',)
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)


class FavoriteUserAdmin(admin.ModelAdmin):
    list_display = ('user', 'favorite_user', 'created_at')
    search_fields = ('user__email', 'favorite_user__email')
    list_filter = ('created_at',)
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)


admin.site.register(FavoritePublication, FavoritePublicationAdmin)
admin.site.register(FavoriteUser, FavoriteUserAdmin)
