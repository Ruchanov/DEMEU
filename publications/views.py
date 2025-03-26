import os
import re

from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.utils import timezone
from decimal import Decimal
from django.db.models import Sum, Count, Q, F, FloatField, Avg
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Publication, View, PublicationDocument
from donations.models import Donation
from .serializers import PublicationSerializer, DonationSerializer, PublicationDocumentSerializer
from .tasks import validate_document_ocr


def normalize_text(text):
    return re.sub(r'[^\w\s]', '', text.lower())


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticatedOrReadOnly])
def publication_list(request):
    if request.method == 'GET':
        publications = Publication.objects.annotate(
            total_donated=Sum('donations__donor_amount'),
            total_views=Count('views'),
            total_comments=Count('comments'),
        )
        search = request.GET.get('search', '').strip().lower()
        if search:
            search_words = search.split()  # Разбиваем строку на слова
            # print(f"Поисковый запрос: {search_words}")  # Логируем введенные слова

            if len(search_words) <= 2:
                #Если 1-2 слова → ищем любое из слов (логика OR)
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
                #Если 3+ слова → ищем полное совпадение текста (логика AND)
                normalized_search = normalize_text(search)
                publications = publications.filter(
                    Q(description__icontains=normalized_search) |
                    Q(title__icontains=normalized_search) |
                    Q(author__email__icontains=normalized_search)
                )

        #Фильтрация
        categories = request.GET.get('category')
        if categories:
            category_list = [c.strip() for c in categories.split(',')]  # Разбиваем строку на список
            publications = publications.filter(category__in=category_list)


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
        # serializer = PublicationSerializer(data=request.data)
        serializer = PublicationSerializer(data=request.data, context={'request': request})
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
            total_comments=Count('comments')
        ).get(pk=pk)
    except Publication.DoesNotExist:
        return Response({"error": "Publication not found."}, status=status.HTTP_404_NOT_FOUND)

    publication.donation_percentage = (publication.total_donated or 0) / (publication.amount or 1) * 100

    if request.method == 'GET':
        if request.user.is_authenticated and not View.objects.filter(publication=publication, viewer=request.user).exists():
            View.objects.create(publication=publication, viewer=request.user)

        # serializer = PublicationSerializer(publication)
        serializer = PublicationSerializer(publication, context={'request': request})
        return Response(serializer.data)

    elif request.method == 'PUT':
        if request.user != publication.author:
            return Response({"error": "You do not have permission to edit this publication."},
                            status=status.HTTP_403_FORBIDDEN)

        # serializer = PublicationSerializer(publication, data=request.data, partial=True)
        serializer = PublicationSerializer(publication, data=request.data, partial=True, context={'request': request})
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
def upload_document(request, publication_id):
    try:
        publication = Publication.objects.get(id=publication_id)
    except Publication.DoesNotExist:
        return Response({"error": "Publication not found."}, status=404)

    serializer = PublicationDocumentSerializer(data=request.data)
    if serializer.is_valid():
        document = serializer.save(publication=publication)

        # Отправка задачи в Celery:
        validate_document_ocr.delay(document.id)

        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_documents(request, publication_id):
    documents = PublicationDocument.objects.filter(publication_id=publication_id)
    serializer = PublicationDocumentSerializer(documents, many=True)
    return Response(serializer.data)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_document(request, document_id):
    try:
        document = PublicationDocument.objects.get(id=document_id)
    except PublicationDocument.DoesNotExist:
        return Response({"error": "Document not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.user != document.publication.author:
        return Response({"error": "You don't have permission to delete this document."}, status=status.HTTP_403_FORBIDDEN)

    document.delete()
    return Response({"message": "Document deleted successfully."}, status=status.HTTP_204_NO_CONTENT)


@receiver(pre_delete, sender=PublicationDocument)
def delete_document_file(sender, instance, **kwargs):
    if instance.file:
        if os.path.exists(instance.file.path):
            os.remove(instance.file.path)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_document(request, document_id):
    try:
        document = PublicationDocument.objects.get(id=document_id)
    except PublicationDocument.DoesNotExist:
        return Response({"error": "Document not found."}, status=status.HTTP_404_NOT_FOUND)

    print(f"Автор публикации: {document.publication.author}")
    print(f"Пользователь, который делает запрос: {request.user}")

    if request.user != document.publication.author:
        return Response({"error": "You don't have permission to update this document."},
                        status=status.HTTP_403_FORBIDDEN)

    serializer = PublicationDocumentSerializer(document, data=request.data, partial=True)
    if serializer.is_valid():
        document.file.delete()  # Удаляем старый файл перед заменой
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def donation_create(request, publication_id):
#     try:
#         publication = Publication.objects.get(id=publication_id)
#     except Publication.DoesNotExist:
#         return Response({"error": "Publication not found."}, status=status.HTTP_404_NOT_FOUND)
#
#     data = request.data.copy()
#     data['donor'] = request.user.id
#
#     serializer = DonationSerializer(data=data, context={'request': request})
#     if serializer.is_valid():
#         serializer.save(publication=publication, donor=request.user)
#         return Response(serializer.data, status=status.HTTP_201_CREATED)
#
#     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
#
# @api_view(['GET'])
# def top_donors(request, publication_id):
#     try:
#         publication = Publication.objects.get(id=publication_id)
#     except Publication.DoesNotExist:
#         return Response({"error": "Publication not found."}, status=status.HTTP_404_NOT_FOUND)
#
#     top_donors = publication.donations.order_by('-donor_amount', '-created_at')[:5]
#     serializer = DonationSerializer(top_donors, many=True, context={'request': request})
#     return Response(serializer.data)



@api_view(['GET'])
def top_publications(request):
    two_months_ago = timezone.now() - timezone.timedelta(days=60)

    publications = Publication.objects.filter(created_at__gte=two_months_ago)

    publications = publications.annotate(
        total_donated=Sum('donations__donor_amount', default=0),
        total_views=Count('views', distinct=True),
        total_comments=Count('comments', distinct=True),
    )

    # Динамически рассчитываем средние суммы пожертвований по категориям
    category_averages = Publication.objects.values('category').annotate(
        avg_donation=Avg('donations__donor_amount')
    )

    category_averages_dict = {item['category']: float(item['avg_donation'] or 50000) for item in category_averages}

    for publication in publications:
        total_donated = float(getattr(publication, 'total_donated', Decimal(0)))
        total_views = float(getattr(publication, 'total_views', 0))
        total_comments = float(getattr(publication, 'total_comments', 0))

        # Количество дней с момента создания публикации
        days_old = (timezone.now() - publication.created_at).days + 1  # +1 чтобы не делить на 0

        # Коэффициент свежести (старые публикации затухают)
        freshness_factor = max(0.5, 1 - 0.01 * days_old)

        # Скорость пожертвований (важно, как быстро собираются деньги)
        donation_rate = total_donated / days_old

        # Коэффициент категории (балансируем популярные и непопулярные категории)
        category_factor = 1 + (category_averages_dict.get(publication.category, 50000) / 50000) * 0.2

        # Коэффициент вовлеченности пользователей (уникальные пользователи в комментариях)
        active_users = (
            publication.comments.values('author').distinct().count()
            if hasattr(Publication, 'comments')
            else 0
        )
        engagement_boost = 1 + (active_users / 50)

        # Финальный расчет рейтинга
        publication.score = (
                (total_donated * 0.5 + total_views * 0.3 + total_comments * 0.2 + donation_rate * 0.5)
                * freshness_factor * category_factor * engagement_boost
        )

    publications = [p for p in publications if p.total_donated > 0 or p.total_views > 0 or p.total_comments > 0]

    top_publications = sorted(publications, key=lambda p: p.score, reverse=True)[:10]

    serializer = PublicationSerializer(top_publications, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def recommended_publications(request):
    user = request.user

    # Получаем категории, которые пользователь чаще всего просматривал
    viewed_categories = list(
        View.objects.filter(viewer=user)
        .values('publication__category')
        .annotate(count=Count('id'))
        .order_by('-count')
        .values_list('publication__category', flat=True)
    )

    donated_categories = list(
        Donation.objects.filter(donor=user)
        .values('publication__category')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    donated_categories = [item['publication__category'] for item in donated_categories]

    # Объединяем списки категорий и удаляем дубликаты
    preferred_categories = list(set(viewed_categories + donated_categories))

    # Получаем публикации из предпочтительных категорий
    recommended_posts = Publication.objects.filter(category__in=preferred_categories).exclude(author=user)

    # Если у пользователя нет истории, просто берем самые популярные посты
    if not recommended_posts.exists():
        recommended_posts = (
            Publication.objects.annotate(
                total_donations=Sum('donations__donor_amount'),
                total_views=Count('views')
            )
            .order_by('-total_donations', '-total_views')[:5]
        )

    serializer = PublicationSerializer(recommended_posts, many=True)
    return Response(serializer.data)