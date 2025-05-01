from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Sum
from .models import Donation
from .serializers import DonationSerializer
from publications.models import Publication
from .utils import send_donation_email
from .tasks import send_donation_email_task
import stripe

def get_publication_or_404(publication_id):
    #Возвращает публикацию или None, если не найдено.
    try:
        return Publication.objects.get(id=publication_id)
    except Publication.DoesNotExist:
        return None


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def donation_create(request, publication_id):
    # Создание пожертвования и отправка чека на email."""
    publication = get_publication_or_404(publication_id)
    if not publication:
        return Response({"error": "Publication not found."}, status=status.HTTP_404_NOT_FOUND)

    data = request.data.copy()
    data['donor'] = request.user.id

    serializer = DonationSerializer(data=data, context={'request': request})
    if serializer.is_valid():
        donation = serializer.save(publication=publication, donor=request.user)

        # # Отправляем чек на email
        # send_donation_email(request.user, donation)

        send_donation_email_task.delay(donation.id)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([AllowAny])
def top_donors(request, publication_id):
    #Получение списка топ-5 доноров для публикации.
    publication = get_publication_or_404(publication_id)
    if not publication:
        return Response({"error": "Publication not found."}, status=status.HTTP_404_NOT_FOUND)

    top_donors = publication.donations.order_by('-donor_amount', '-created_at')[:5]
    serializer = DonationSerializer(top_donors, many=True, context={'request': request})
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def donation_history(request):
    #Получение истории пожертвований пользователя.
    donations = Donation.objects.filter(donor=request.user).order_by('-created_at')
    serializer = DonationSerializer(donations, many=True)
    return Response(serializer.data)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def cancel_donation(request, donation_id):
    #Позволяет пользователю отменить свое пожертвование.
    try:
        donation = Donation.objects.get(id=donation_id, donor=request.user)
    except Donation.DoesNotExist:
        return Response({"error": "Donation not found or access denied."}, status=status.HTTP_404_NOT_FOUND)

    donation.delete()
    return Response({"message": "Donation cancelled successfully."}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def donation_stats(request):
    #Возвращает общую сумму пожертвований и их количество.
    total_donated = Donation.objects.aggregate(total=Sum('donor_amount'))['total'] or 0
    donation_count = Donation.objects.count()

    return Response({
        "total_donated": total_donated,
        "total_donations": donation_count
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_payment_intent(request):
    try:
        donor_amount = float(request.data.get('donor_amount'))
        support_percentage = int(request.data.get('support_percentage', 0))

        support_amount = (donor_amount * support_percentage) / 100
        total_amount = donor_amount + support_amount

        intent = stripe.PaymentIntent.create(
            amount=int(total_amount * 100),  # Stripe требует сумму в тиынах (копейках)
            currency='kzt',
            metadata={
                'user_id': request.user.id,
                'donor_amount': donor_amount,
                'support_percentage': support_percentage,
                'publication_id': request.data.get('publication_id')
            }
        )

        return Response({'client_secret': intent.client_secret})

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)