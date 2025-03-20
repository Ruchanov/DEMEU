from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from .models import Donation
from .serializers import DonationSerializer
from publications.models import Publication

def get_publication_or_404(publication_id):
    try:
        return Publication.objects.get(id=publication_id)
    except Publication.DoesNotExist:
        return None

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def donation_create(request, publication_id):
    publication = get_publication_or_404(publication_id)
    if not publication:
        return Response({"error": "Publication not found."}, status=status.HTTP_404_NOT_FOUND)

    data = request.data.copy()
    data['donor'] = request.user.id

    serializer = DonationSerializer(data=data, context={'request': request})
    if serializer.is_valid():
        serializer.save(publication=publication, donor=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([AllowAny])
def top_donors(request, publication_id):
    publication = get_publication_or_404(publication_id)
    if not publication:
        return Response({"error": "Publication not found."}, status=status.HTTP_404_NOT_FOUND)

    top_donors = publication.donations.order_by('-donor_amount', '-created_at')[:5]
    serializer = DonationSerializer(top_donors, many=True, context={'request': request})
    return Response(serializer.data)