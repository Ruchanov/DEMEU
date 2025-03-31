from django.urls import path
from .views import (publication_list, publication_detail, recommended_publications, top_publications,
                    archived_publications, urgent_publications, active_publications, pending_publications)

urlpatterns = [
    path('', publication_list, name='publication-list'),
    path('<int:pk>/', publication_detail, name='publication-detail'),
    path('top-publications/', top_publications, name='top-publications'),
    path('recommended/', recommended_publications, name='recommended-publications'),
    path('archive/', archived_publications, name='publication-archive'),
    path('urgent/', urgent_publications, name='urgent-publications'),
    path('my-active/', active_publications, name='my-active-publications'),
    path('my-pending/', pending_publications, name='my-pending-publications'),
]