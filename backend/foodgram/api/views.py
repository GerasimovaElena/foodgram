import csv
from io import StringIO

from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from djoser.views import UserViewSet
from django.shortcuts import get_object_or_404

from recipes.models import Tag, Ingredient, Recipe, ShoppingCart, Favorite
from users.models import Subscription

from .filters import NameSearchFilter, RecipeFilter
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    CustomUserSerializer, UserAvatarSerializer, TagSerializer,
    IngredientSerializer, RecipeCreateSerializer, RecipeListSerializer,
    RecipeMiniSerializer, SubscriptionSerializer, SubscribeSerializer
)

User = get_user_model()


class CustomUserViewSet(UserViewSet):
    serializer_class = CustomUserSerializer

    def get_permissions(self):
        if self.action in [
            'me',
            'subscriptions',
            'subscribe',
            'avatar'
        ]:
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    @action(
        methods=['put', 'delete'],
        url_path='me/avatar',
        detail=False,
        serializer_class=UserAvatarSerializer
    )
    def avatar(self, request):
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
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['get'],
        url_path='subscriptions',
        detail=False,
        serializer_class=SubscriptionSerializer
    )
    def subscriptions(self, request):
        subscriptions = User.objects.filter(
            subscriptions__user=self.request.user
        ).order_by('id')

        page = self.paginate_queryset(subscriptions)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(subscriptions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=['post', 'delete'],
        detail=True,
        serializer_class=SubscribeSerializer
    )
    def subscribe(self, request, id):
        subscribed_to = get_object_or_404(User, pk=id)
        serializer = self.get_serializer(data={
            'subscribed_to': subscribed_to.id}
        )
        serializer.is_valid(raise_exception=True)

        if request.method == 'POST':
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        serializer.delete(validated_data=serializer.validated_data)
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    pagination_class = None
    filter_backends = (NameSearchFilter,)
    search_fields = ('^name',)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_permissions(self):
        if self.action in [
            'create',
            'add_to_cart',
            'remove_from_cart',
            'add_to_favorites',
            'remove_from_favorites'
        ]:
            return (IsAuthenticated(),)
        if self.action in ['update', 'partial_update', 'destroy']:
            return (IsAuthorOrReadOnly(),)
        return (AllowAny(),)

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return RecipeListSerializer
        return RecipeCreateSerializer

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_short_link(self, request, pk=None):
        try:
            recipe = self.get_object()
            base_url = request.build_absolute_uri('/s/')
            return Response(
                {'short-link': f'{base_url}{recipe.short_link}'},
                status=status.HTTP_200_OK
            )
        except Recipe.DoesNotExist:
            return Response(
                {'error': 'Рецепт не найден'},
                status=status.HTTP_404_NOT_FOUND
            )

    def _add_to_list(self, model_class, request, pk):
        recipe = self.get_object()
        instance, created = model_class.objects.get_or_create(
            user=request.user,
            recipe=recipe
        )
        if created:
            serializer = RecipeMiniSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(
            {"detail": "Рецепт уже в списке"},
            status=status.HTTP_400_BAD_REQUEST
        )

    def _remove_from_list(self, model_class, request, pk):
        recipe = self.get_object()
        try:
            item = model_class.objects.get(user=request.user, recipe=recipe)
            item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except model_class.DoesNotExist:
            return Response(
                {"detail": "Рецепт не в списке"},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'], url_path='favorite')
    def add_to_favorites(self, request, pk=None):
        return self._add_to_list(Favorite, request, pk)

    @action(detail=True, methods=['delete'], url_path='favorite')
    def remove_from_favorites(self, request, pk=None):
        return self._remove_from_list(Favorite, request, pk)

    @action(detail=True, methods=['post'], url_path='shopping_cart')
    def add_to_cart(self, request, pk=None):
        return self._add_to_list(ShoppingCart, request, pk)

    @action(detail=True, methods=['delete'], url_path='shopping_cart')
    def remove_from_cart(self, request, pk=None):
        return self._remove_from_list(ShoppingCart, request, pk)


class DownloadCartView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        shopping_cart_items = ShoppingCart.objects.filter(user=request.user)

        if not shopping_cart_items.exists():
            return Response(
                {"message": "Ваш список покупок пуст"},
                status=status.HTTP_200_OK
            )

        ingredients_summary = {}
        for item in shopping_cart_items:
            recipe = item.recipe
            ingredients = recipe.ingredients.all()
            for ingredient in ingredients:
                amount = (
                    ingredient.recipeingredient_set
                    .get(ingredient=ingredient)
                    .amount
                )
                if ingredient.name in ingredients_summary:
                    ingredients_summary[ingredient.name]['amount'] += amount
                else:
                    ingredients_summary[ingredient.name] = {
                        'amount': amount,
                        'measurement_unit': ingredient.measurement_unit
                    }

        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Ингредиент', 'Количество', 'Единица измерения'])
        for name, data in ingredients_summary.items():
            writer.writerow([name, data['amount'], data['measurement_unit']])
        output.seek(0)
        response = Response(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="my_cart.csv"'
        return response
