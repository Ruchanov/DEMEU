from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import UserCertificate
from django.contrib.auth import get_user_model
from .utils import send_certificate_email
from .services import assign_certificate

User = get_user_model()

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def certificate_public_view(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        assign_certificate(user)
        certificate = UserCertificate.objects.get(user=user)

        data = {
            'user_id': user.id,
            'user_name': f"{user.first_name} {user.last_name}",
            'level': certificate.level,
            'certificate_url': request.build_absolute_uri(certificate.pdf.url) if certificate.pdf else None
        }
        return Response(data, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    except UserCertificate.DoesNotExist:
        return Response({'error': 'Certificate not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_certificate_view(request):
    user = request.user

    try:
        certificate = UserCertificate.objects.get(user=user)

        data = {
            'level': certificate.level,
            'certificate_url': request.build_absolute_uri(certificate.pdf.url) if certificate.pdf else None
        }

        return Response(data, status=status.HTTP_200_OK)
    except UserCertificate.DoesNotExist:
        return Response({"error": "Certificate not found"}, status=status.HTTP_404_NOT_FOUND)
