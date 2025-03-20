from django.urls import path
from .views import donation_create, top_donors

urlpatterns = [
    path('<int:publication_id>/donate/', donation_create, name='donation-create'),
    path('<int:publication_id>/top-donors/', top_donors, name='top-donors'),
]
