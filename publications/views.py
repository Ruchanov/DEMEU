import re
from django.db.models import Sum, Count, Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Publication, View, Donation
from .serializers import PublicationSerializer, DonationSerializer


def normalize_text(text):
    return re.sub(r'[^\w\s]', '', text.lower())


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticatedOrReadOnly])
def publication_list(request):
    if request.method == 'GET':
        publications = Publication.objects.annotate(
            total_donated=Sum('donations__donor_amount'),
            total_views=Count('views'),
        )
        search = request.GET.get('search', '').strip().lower()
        if search:
            search_words = search.split()  # Разбиваем строку на слова
            # print(f"Поисковый запрос: {search_words}")  # Логируем введенные слова

            if len(search_words) <= 2:
                # 🔍 Если 1-2 слова → ищем любое из слов (логика OR)
                query = Q()
                for word in search_words:
                    word_normalized = normalize_text(word)  # Удаляем знаки
                    query |= (
                            Q(description__icontains=word_normalized) |
                            Q(title__icontains=word_normalized) |
                            Q(author__email__icontains=word_normalized)
                    )
                publications = publications.filter(query)
            else:
                # 🔍 Если 3+ слова → ищем полное совпадение текста (логика AND)
                normalized_search = normalize_text(search)
                publications = publications.filter(
                    Q(description__icontains=normalized_search) |
                    Q(title__icontains=normalized_search) |
                    Q(author__email__icontains=normalized_search)
                )

        #Фильтрация
        category = request.GET.get('category')
        if category:
            publications = publications.filter(category=category)

        created_at_gte = request.GET.get('created_at__gte')
        created_at_lte = request.GET.get('created_at__lte')
        if created_at_gte and created_at_lte:
            publications = publications.filter(created_at__gte=created_at_gte, created_at__lte=created_at_lte)

        amount_gte = request.GET.get('amount__gte')
        amount_lte = request.GET.get('amount__lte')
        if amount_gte and amount_lte:
            publications = publications.filter(amount__gte=amount_gte, amount__lte=amount_lte)

        total_donated_gte = request.GET.get('total_donated__gte')
        total_donated_lte = request.GET.get('total_donated__lte')
        if total_donated_gte and total_donated_lte:
            publications = publications.filter(total_donated__gte=total_donated_gte,
                                               total_donated__lte=total_donated_lte)

        #Сортировка
        ordering = request.GET.get('ordering', '-created_at')  # По умолчанию сортируем по дате
        if ordering in ['created_at', '-created_at', 'total_views', '-total_views', 'total_donated', '-total_donated']:
            publications = publications.order_by(ordering)

        # print(f" SQL-запрос: {str(publications.query)}")  # Логируем SQL-запрос

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
