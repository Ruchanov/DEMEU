from django.contrib import admin
from .models import Publication, PublicationImage, PublicationVideo, Donation, View, PublicationDocument


class PublicationImageInline(admin.TabularInline):
    model = PublicationImage
    extra = 1  # Позволяет загружать дополнительные изображения


class PublicationVideoInline(admin.TabularInline):
    model = PublicationVideo
    extra = 1  # Позволяет загружать дополнительные видео


class PublicationAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'amount', 'created_at')
    search_fields = ('title', 'author__email', 'category')
    list_filter = ('category', 'created_at')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    inlines = [PublicationImageInline, PublicationVideoInline]

    fieldsets = (
        ('Основная информация', {'fields': ('author', 'title', 'category', 'description')}),
        ('Финансовая информация', {'fields': ('bank_details', 'amount')}),
        ('Контактные данные', {'fields': ('contact_name', 'contact_email', 'contact_phone')}),
        ('Даты', {'fields': ('created_at', 'updated_at')}),
    )


class DonationAdmin(admin.ModelAdmin):
    list_display = ('donor_name', 'donor_amount', 'publication')
    search_fields = ('donor_name', 'donor_email', 'publication__title')
    list_filter = ('publication',)


class ViewAdmin(admin.ModelAdmin):
    list_display = ('viewer', 'publication', 'viewed_at')
    search_fields = ('viewer__email', 'publication__title')
    list_filter = ('viewed_at',)


class PublicationDocumentAdmin(admin.ModelAdmin):
    list_display = ('publication', 'document_type', 'file', 'uploaded_at')
    search_fields = ('publication__title', 'document_type')
    list_filter = ('document_type', 'uploaded_at')


admin.site.register(Publication, PublicationAdmin)
admin.site.register(Donation, DonationAdmin)
admin.site.register(View, ViewAdmin)
admin.site.register(PublicationDocument, PublicationDocumentAdmin)
