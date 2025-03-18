from django.urls import path
from .views import publication_list, publication_detail, donation_create, top_donors, list_documents, upload_document, \
    delete_document, recommended_publications, update_document, top_publications

urlpatterns = [
    path('', publication_list, name='publication-list'),
    path('<int:pk>/', publication_detail, name='publication-detail'),
    path('<int:publication_id>/documents/', list_documents, name='document-list'),
    path('<int:publication_id>/documents/upload/', upload_document, name='document-upload'),
    path('documents/<int:document_id>/update/', update_document, name='document-update'),
    path('documents/<int:document_id>/delete/', delete_document, name='document-delete'),
    path('<int:publication_id>/donate/', donation_create, name='donation-create'),
    path('<int:publication_id>/top-donors/', top_donors, name='top-donors'),
    path('top-publications/', top_publications, name='top-publications'),
    path('recommended/', recommended_publications, name='recommended-publications'),

]