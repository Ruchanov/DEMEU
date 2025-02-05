from django.db.models import Sum, Count
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Publication, View, Donation
from .serializers import PublicationSerializer, DonationSerializer


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticatedOrReadOnly])
def publication_list(request):
    if request.method == 'GET':
        publications = Publication.objects.annotate(
            total_donated=Sum('donations__donor_amount'),
            total_views=Count('views'),
        )
        for pub in publications:
            pub.donation_percentage = (pub.total_donated or 0) / (pub.amount or 1) * 100

        serializer = PublicationSerializer(publications, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = PublicationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(author=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticatedOrReadOnly])
def publication_detail(request, pk):
    try:
        publication = Publication.objects.annotate(
            total_donated=Sum('donations__donor_amount'),
            total_views=Count('views'),
        ).get(pk=pk)
    except Publication.DoesNotExist:
        return Response({"error": "Publication not found."}, status=status.HTTP_404_NOT_FOUND)

    publication.donation_percentage = (publication.total_donated or 0) / (publication.amount or 1) * 100

    if request.method == 'GET':
        if request.user.is_authenticated and not View.objects.filter(publication=publication, viewer=request.user).exists():
            View.objects.create(publication=publication, viewer=request.user)

        serializer = PublicationSerializer(publication)
        return Response(serializer.data)

    elif request.method == 'PUT':
        if request.user != publication.author:
            return Response({"error": "You do not have permission to edit this publication."},
                            status=status.HTTP_403_FORBIDDEN)

        serializer = PublicationSerializer(publication, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        if request.user != publication.author:
            return Response({"error": "You do not have permission to delete this publication."},
                            status=status.HTTP_403_FORBIDDEN)

        publication.delete()
        return Response({"message": "Publication deleted successfully."}, status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def donation_create(request, publication_id):
    try:
        publication = Publication.objects.get(id=publication_id)
    except Publication.DoesNotExist:
        return Response({"error": "Publication not found."}, status=status.HTTP_404_NOT_FOUND)

    serializer = DonationSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(publication=publication)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def top_donors(request, publication_id):
    try:
        publication = Publication.objects.get(id=publication_id)
    except Publication.DoesNotExist:
        return Response({"error": "Publication not found."}, status=status.HTTP_404_NOT_FOUND)

    top_donors = publication.donations.order_by('-donor_amount')[:5]
    serializer = DonationSerializer(top_donors, many=True)
    return Response(serializer.data)
