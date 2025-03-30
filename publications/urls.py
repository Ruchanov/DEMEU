from django.urls import path
from .views import publication_list, publication_detail, list_documents, upload_document, \
    delete_document, recommended_publications, update_document, top_publications, archived_publications, \
    urgent_publications, active_publications, pending_publications

urlpatterns = [
    path('', publication_list, name='publication-list'),
    path('<int:pk>/', publication_detail, name='publication-detail'),
    path('<int:publication_id>/documents/', list_documents, name='document-list'),
    path('<int:publication_id>/documents/upload/', upload_document, name='document-upload'),
    path('documents/<int:document_id>/update/', update_document, name='document-update'),
    path('documents/<int:document_id>/delete/', delete_document, name='document-delete'),
    path('top-publications/', top_publications, name='top-publications'),
    path('recommended/', recommended_publications, name='recommended-publications'),
    path('archive/', archived_publications, name='publication-archive'),
    path('urgent/', urgent_publications, name='urgent-publications'),
    path('my-active/', active_publications, name='my-active-publications'),
    path('my-pending/', pending_publications, name='my-pending-publications'),
]