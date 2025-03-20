from django.urls import path
from .views import donation_create, top_donors, donation_history, cancel_donation, donation_stats

urlpatterns = [
    path('<int:publication_id>/donate/', donation_create, name='donation-create'),
    path('<int:publication_id>/top-donors/', top_donors, name='top-donors'),
    path('my-donations/', donation_history, name='donation-history'),
    path('cancel-donation/<int:donation_id>/', cancel_donation, name='cancel-donation'),
    path('donation-stats/', donation_stats, name='donation-stats'),
]
