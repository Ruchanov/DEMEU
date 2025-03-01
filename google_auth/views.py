import os
import requests
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import GoogleAuthSerializer
from accounts.models import User
from profiles.models import Profile
from django.core.files.base import ContentFile

class GoogleLoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = GoogleAuthSerializer(data=request.data)
        if serializer.is_valid():
            id_token_str = serializer.validated_data["id_token"]

            try:
                google_data = id_token.verify_oauth2_token(
                    id_token_str, google_requests.Request()
                )

                email = google_data.get("email")
                first_name = google_data.get("given_name", "")
                last_name = google_data.get("family_name", "")
                google_id = google_data.get("sub")
                google_avatar = google_data.get("picture", None)

                if not email:
                    return Response({"error": "Google account must have an email."}, status=400)

                user, created = User.objects.get_or_create(
                    email=email,
                    defaults={
                        "first_name": first_name,
                        "last_name": last_name,
                        "google_id": google_id,
                        "is_verified": True,
                        "is_active": True,
                    },
                )
                if not user.google_id:
                    user.google_id = google_id
                    user.save()

                profile, profile_created = Profile.objects.get_or_create(user=user)

                if not profile.avatar and google_avatar:
                    avatar_response = requests.get(google_avatar)
                    if avatar_response.status_code == 200:
                        profile.avatar.save(
                            f"{user.pk}_google.jpg",
                            ContentFile(avatar_response.content),
                            save=True
                        )

                refresh = RefreshToken.for_user(user)

                return Response(
                    {
                        "message": "Login successful",
                        "access_token": str(refresh.access_token),
                        "refresh_token": str(refresh),
                    },
                    status=200,
                )

            except ValueError as e:
                return Response({"error": f"Invalid token: {str(e)}"}, status=400)
            except Exception as e:
                return Response({"error": str(e)}, status=400)

        return Response(serializer.errors, status=400)
