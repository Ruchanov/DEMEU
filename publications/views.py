from django.db.models import Sum
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import Publication, View, Donation
from .serializers import PublicationSerializer, DonationSerializer


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticatedOrReadOnly])
def publication_list(request):
    if request.method == 'GET':
        publications = Publication.objects.all()
        serializer = PublicationSerializer(publications, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = PublicationSerializer(data=request.data)
        if serializer.is_valid():
            publication = serializer.save(author=request.user)
            response_data = serializer.data
            response_data["privacy_policy"] = "Ваши данные хранятся в соответствии с нашей политикой конфиденциальности."
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticatedOrReadOnly])
def publication_detail(request, pk):
    try:
        publication = Publication.objects.get(pk=pk)
    except Publication.DoesNotExist:
        return Response({"error": "Publication not found."}, status=status.HTTP_404_NOT_FOUND)

 # Если пользователь авторизован, добавляем его как просмотревшего публикацию
    if request.user.is_authenticated:
        View.objects.get_or_create(publication=publication, viewer=request.user)

    # Серилизатор будет вычислять donation_percentage, total_views и total_donated
    serializer = PublicationSerializer(publication)

    if request.method == 'GET':
        return Response(serializer.data)

    elif request.method == 'PUT':
        if publication.author != request.user:
            return Response({"error": "You do not have permission to edit this publication."},
                            status=status.HTTP_403_FORBIDDEN)

        serializer = PublicationSerializer(publication, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        if publication.author != request.user:
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

    donor_name = request.data.get('donor_name')
    donor_amount = request.data.get('donor_amount')

    if not donor_name or not donor_amount:
        return Response({"error": "Donor name and amount are required."}, status=status.HTTP_400_BAD_REQUEST)

    donation = Donation.objects.create(
        publication=publication,
        donor_name=donor_name,
        donor_amount=donor_amount
    )

    return Response(DonationSerializer(donation).data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def privacy_policy(request):
    return Response({
        "privacy_policy": "Мы уважаем вашу конфиденциальность. Все данные защищены и используются "
                          "только в рамках нашего сервиса."
    })


@api_view(['GET'])
def privacy_policy(request):
    return Response({
        "privacy_policy": "Мы уважаем вашу конфиденциальность. Все данные защищены и используются "
                          "только в рамках нашего сервиса."
    })