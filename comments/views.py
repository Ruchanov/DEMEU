from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import Comment
from .serializers import CommentSerializer


@api_view(['GET', 'POST', 'PUT', 'DELETE'])
@permission_classes([permissions.IsAuthenticatedOrReadOnly])
def comment_list_create(request, publication_id):
    if request.method == 'GET':
        comments = Comment.objects.filter(publication_id=publication_id).order_by('-created_at')
        serializer = CommentSerializer(comments, many=True, context={'request': request})
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = CommentSerializer(data=request.data, context={'request': request, 'publication_id': publication_id})

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.save(author=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    elif request.method == 'PUT':  # ✅ Обновление комментария в рамках публикации
        comment_id = request.data.get('comment_id')
        new_content = request.data.get('content')

        if not comment_id or not new_content:
            return Response({"error": "Comment ID and new content are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            comment = Comment.objects.get(id=comment_id, publication_id=publication_id)
        except Comment.DoesNotExist:
            return Response({"error": "Comment not found under this publication."}, status=status.HTTP_404_NOT_FOUND)

        if comment.author != request.user:
            return Response({"error": "You do not have permission to update this comment."},
                            status=status.HTTP_403_FORBIDDEN)

        comment.content = new_content
        comment.save()

        serializer = CommentSerializer(comment, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'DELETE':
        comment_id = request.data.get('comment_id')

        if not comment_id:
            return Response({"error": "Comment ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            comment = Comment.objects.get(id=comment_id, publication_id=publication_id)
        except Comment.DoesNotExist:
            return Response({"error": "Comment not found under this publication."}, status=status.HTTP_404_NOT_FOUND)

        if comment.author != request.user:
            return Response({"error": "You do not have permission to delete this comment."},
                            status=status.HTTP_403_FORBIDDEN)

        comment.delete()
        return Response({"message": "Comment deleted successfully."}, status=status.HTTP_204_NO_CONTENT)

#
# @api_view(['GET', 'PUT', 'DELETE'])
# @permission_classes([permissions.IsAuthenticated])
# def comment_detail(request, pk):
#     try:
#         comment = Comment.objects.get(pk=pk)
#     except Comment.DoesNotExist:
#         return Response({"error": "Comment not found."}, status=status.HTTP_404_NOT_FOUND)
#
#     #Проверка прав доступа
#     if request.method in ['PUT', 'DELETE'] and comment.author != request.user:
#         return Response({"error": "You do not have permission to modify or delete this comment."},
#                             status=status.HTTP_403_FORBIDDEN)
#
#     if request.method == 'GET':
#         serializer = CommentSerializer(comment)
#         return Response(serializer.data, status=status.HTTP_200_OK)
#
#     elif request.method == 'PUT':
#         if comment.author != request.user:
#             return Response({"error": "You do not have permission to edit this comment."},
#                             status=status.HTTP_403_FORBIDDEN)
#
#         serializer = CommentSerializer(comment, data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_200_OK)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
#     elif request.method == 'DELETE':
#         if comment.author != request.user:
#             return Response({"error": "You do not have permission to delete this comment."},
#                             status=status.HTTP_403_FORBIDDEN)
#
#         comment.delete()
#         return Response({"message": "Comment deleted successfully."}, status=status.HTTP_204_NO_CONTENT)