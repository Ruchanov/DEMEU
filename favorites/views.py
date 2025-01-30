from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import FavoritePublication, FavoriteUser
from .serializers import FavoritePublicationSerializer, FavoriteUserSerializer
from publications.models import Publication
from accounts.models import User


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def favorite_publication_list_create(request):
    if request.method == 'GET':
        favorites = FavoritePublication.objects.filter(user=request.user)
        serializer = FavoritePublicationSerializer(favorites, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        publication_id = request.data.get('publication')
        if publication_id:
            try:
                publication = Publication.objects.get(id=publication_id)
                favorite = FavoritePublication.objects.create(user=request.user, publication=publication)
                serializer = FavoritePublicationSerializer(favorite)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except Publication.DoesNotExist:
                return Response({"error": "Publication not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response({"error": "Publication ID is required."}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def favorite_publication_delete(request, pk):
    try:
        favorite = FavoritePublication.objects.get(id=pk, user=request.user)
    except FavoritePublication.DoesNotExist:
        return Response({"error": "Favorite publication not found."}, status=status.HTTP_404_NOT_FOUND)

    favorite.delete()
    return Response({"message": "Publication removed from favorites."}, status=status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def favorite_user_list_create(request):
    if request.method == 'GET':
        favorites = FavoriteUser.objects.filter(user=request.user)
        serializer = FavoriteUserSerializer(favorites, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        favorite_user_id = request.data.get('favorite_user')
        if favorite_user_id:
            try:
                favorite_user = User.objects.get(id=favorite_user_id)
                if favorite_user != request.user:
                    favorite = FavoriteUser.objects.create(user=request.user, favorite_user=favorite_user)
                    serializer = FavoriteUserSerializer(favorite)
                    return Response(serializer.data, status=status.HTTP_201_CREATED)
                return Response({"error": "You cannot add yourself to favorites."}, status=status.HTTP_400_BAD_REQUEST)
            except User.DoesNotExist:
                return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response({"error": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def favorite_user_delete(request, pk):
    try:
        favorite = FavoriteUser.objects.get(id=pk, user=request.user)
    except FavoriteUser.DoesNotExist:
        return Response({"error": "Favorite user not found."}, status=status.HTTP_404_NOT_FOUND)

    favorite.delete()
    return Response({"message": "User removed from favorites."}, status=status.HTTP_204_NO_CONTENT)