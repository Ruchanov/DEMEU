from django.urls import path
from .views import publication_list, publication_detail, donation_create, top_donors

urlpatterns = [
    path('', publication_list, name='publication-list'),
    path('<int:pk>/', publication_detail, name='publication-detail'),
    path('<int:publication_id>/donate/', donation_create, name='donation-create'),
    path('<int:publication_id>/top-donors/', top_donors, name='top-donors'),
]