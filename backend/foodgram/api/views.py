from djoser.views import UserViewSet
from django.contrib.auth import get_user_model
from rest_framework.decorators import action
from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status

from .serializers import CustomUserSerializer, UserAvatarSerializer, TagSerializer, IngredientSerializer
from recipes.models import Tag, Ingredient

User = get_user_model()

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
  
    # @action(
    #     methods=['get'],
    #     detail=False,
    #     permission_classes=[IsAuthenticated],
    #     url_path='subscriptions'
    # )
    # def subscriptions(self, request):
    #     user = request.user
    #     subscriptions = User.objects.filter(subscribers__user=user)
    #     page = self.paginate_queryset(subscriptions)
    #     if page is not None:
    #         serializer = SubscriptionSerializer(page, many=True, context={'request': request})
    #         return self.get_paginated_response(serializer.data)
        
    #     serializer = SubscriptionSerializer(subscriptions, many=True, context={'request': request})
    #     return Response(serializer.data, status=status.HTTP_200_OK)

    # @action(
    #     methods=['post', 'delete'],
    #     detail=True,
    #     permission_classes=[IsAuthenticated],
    #     url_path='subscribe'
    # )
    # def subscribe(self, request, pk=None):
    #     """Подписка и отписка на пользователя."""
    #     user_to_subscribe = get_object_or_404(User, pk=pk)
        
    #     if request.method == 'POST':
    #         if request.user == user_to_subscribe:
    #             return Response(
    #                 {"errors": "Нельзя подписаться на самого себя."},
    #                 status=status.HTTP_400_BAD_REQUEST
    #             )
    #         if Subscription.objects.filter(user=request.user, subscribed_to=user_to_subscribe).exists():
    #             return Response(
    #                 {"errors": "Вы уже подписаны на этого пользователя."},
    #                 status=status.HTTP_400_BAD_REQUEST
    #             )
    #         Subscription.objects.create(user=request.user, subscribed_to=user_to_subscribe)
    #         serializer = SubscriptionSerializer(user_to_subscribe, context={'request': request})
    #         return Response(serializer.data, status=status.HTTP_201_CREATED)
        
    #     elif request.method == 'DELETE':
    #         subscription = Subscription.objects.filter(user=request.user, subscribed_to=user_to_subscribe)
    #         if not subscription.exists():
    #             return Response(
    #                 {"errors": "Вы не были подписаны на этого пользователя."},
    #                 status=status.HTTP_400_BAD_REQUEST
    #             )
    #         subscription.delete()
    #         return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Вьюсет для просмотра списка тегов и получения информации о конкретном теге.
    """

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    pagination_class = None
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, )
    filterset_fields = ('name',)
    search_fields = ('^name',)
