from django.contrib import admin
from .models import Comment


class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'publication', 'content', 'created_at', 'updated_at')
    search_fields = ('author__email', 'publication__title', 'content')
    list_filter = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')

admin.site.register(Comment, CommentAdmin)
