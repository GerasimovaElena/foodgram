from djoser.views import UserViewSet
from rest_framework.decorators import action
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status

from .serializers import CustomUserSerializer, UserAvatarSerializer, TagSerializer
from recipes.models import Tag


class CustomUserViewSet(UserViewSet):
    serializer_class = CustomUserSerializer

    def get_permissions(self):
        if self.action == 'me':
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    @action(
        methods=['put', 'delete'],
        url_path='me/avatar',
        detail=False,
        serializer_class=UserAvatarSerializer,
        permission_classes=[IsAuthenticated]
    )
    def avatar(self, request):
        """Обрабатывает PUT и DELETE запросы для аватара пользователя."""
        user = request.user

        if request.method == 'PUT':
            serializer = self.get_serializer(
                user, data=request.data
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                {'avatar': serializer.data.get('avatar')},
                status=status.HTTP_200_OK
            )

        user.avatar.delete(save=True)
        return Response(
            status=status.HTTP_204_NO_CONTENT
        )


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Вьюсет для просмотра списка тегов и получения информации о конкретном теге.
    """

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]
    pagination_class = None

