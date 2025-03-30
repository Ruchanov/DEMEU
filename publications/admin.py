from django.contrib import admin
from .models import Publication, PublicationImage, PublicationVideo, View, PublicationDocument


class PublicationImageInline(admin.TabularInline):
    model = PublicationImage
    extra = 1  # Позволяет загружать дополнительные изображения


class PublicationVideoInline(admin.TabularInline):
    model = PublicationVideo
    extra = 1  # Позволяет загружать дополнительные видео


class PublicationDocumentInline(admin.TabularInline):
    model = PublicationDocument
    extra = 1  # Позволяет загружать дополнительные документы
    fields = ('document_type', 'file', 'uploaded_at')
    readonly_fields = ('uploaded_at',)


class PublicationAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'amount', 'status', 'verification_status', 'created_at')
    search_fields = ('title', 'author__email', 'category')
    list_filter = ('category', 'created_at', 'status', 'verification_status')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    inlines = [PublicationImageInline, PublicationVideoInline, PublicationDocumentInline]

    fieldsets = (
        ('Основная информация', {'fields': ('author', 'title', 'category', 'description')}),
        ('Финансовая информация', {'fields': ('bank_details', 'amount')}),
        ('Контактные данные', {'fields': ('contact_name', 'contact_email', 'contact_phone')}),
        ('Статусы', {'fields': ('status', 'verification_status')}),
        ('Даты', {'fields': ('created_at', 'updated_at')}),
    )


class DonationAdmin(admin.ModelAdmin):
    list_display = ['get_donor_name', 'donor_amount', 'publication', 'created_at']
    search_fields = ('donor__email', 'publication__title')
    list_filter = ('publication',)

    def get_donor_name(self, obj):
        if obj.donor:
            return f"{obj.donor.first_name} {obj.donor.last_name}".strip() or obj.donor.email
        return "Anonymous"

    get_donor_name.short_description = "Donor Name"


class ViewAdmin(admin.ModelAdmin):
    list_display = ('viewer', 'publication', 'viewed_at')
    search_fields = ('viewer__email', 'publication__title')
    list_filter = ('viewed_at',)


class PublicationDocumentAdmin(admin.ModelAdmin):
    list_display = (
        'publication', 'document_type', 'file', 'uploaded_at',
        'verified', 'verification_status',
    )
    readonly_fields = (
        'uploaded_at', 'verified', 'verification_status',
        'verification_details', 'extracted_data'
    )
    search_fields = ('publication__title', 'document_type')
    list_filter = ('document_type', 'uploaded_at', 'verification_status')

    def verification_summary(self, obj):
        if obj.verification_details:
            return str(obj.verification_details.get("message", ""))
        return ""

admin.site.register(Publication, PublicationAdmin)
admin.site.register(View, ViewAdmin)
admin.site.register(PublicationDocument, PublicationDocumentAdmin)
