from io import BytesIO

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .filters import NameSearchFilter, RecipeFilter
from .permissions import IsAuthorOrReadOnly
from .serializers import (CustomUserSerializer, IngredientSerializer,
                          RecipeCreateSerializer, RecipeListSerializer,
                          RecipeMiniSerializer, SubscribeSerializer,
                          SubscriptionSerializer, TagSerializer,
                          UserAvatarSerializer)

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
            'manage_favorites',
            'manage_cart'
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

    def _manage_list(self, model_class, request, pk):

        recipe = self.get_object()

        if request.method == 'POST':
            instance, created = model_class.objects.get_or_create(
                user=request.user,
                recipe=recipe
            )
            if created:
                serializer = RecipeMiniSerializer(recipe)
                return Response(
                    serializer.data,
                    status=status.HTTP_201_CREATED
                )
            return Response(
                {"detail": "Рецепт уже в списке"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            item = model_class.objects.get(user=request.user, recipe=recipe)
            item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except model_class.DoesNotExist:
            return Response(
                {"detail": "Рецепт не в списке"},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post', 'delete'], url_path='favorite')
    def manage_favorites(self, request, pk=None):
        return self._manage_list(Favorite, request, pk)

    @action(detail=True, methods=['post', 'delete'], url_path='shopping_cart')
    def manage_cart(self, request, pk=None):
        return self._manage_list(ShoppingCart, request, pk)


class DownloadCartView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        shopping_cart_items = ShoppingCart.objects.filter(user=request.user)

        if not shopping_cart_items.exists():
            return Response(
                {"message": "Ваш список покупок пуст"},
                status=status.HTTP_200_OK
            )

        summary = {}
        for item in shopping_cart_items:
            recipe = item.recipe
            ingredients = recipe.ingredients.all()
            for ingredient in ingredients:
                recipe_ingredients = (
                    RecipeIngredient.objects
                    .filter(recipe=recipe, ingredient=ingredient)
                )
                for recipe_ingredient in recipe_ingredients:
                    amount = recipe_ingredient.amount
                    if ingredient.name in summary:
                        summary[ingredient.name]['amount'] += amount
                    else:
                        summary[ingredient.name] = {
                            'amount': amount,
                            'measurement_unit': ingredient.measurement_unit
                        }

        output = BytesIO()
        p = canvas.Canvas(output, pagesize=letter)
        width, height = letter
        p.setFont("Helvetica-Bold", 16)
        p.drawString(100, height - 50, "Список покупок:")
        p.setFont("Helvetica", 12)
        y_position = height - 100
        for name, data in summary.items():
            text = f"{name} ({data['measurement_unit']}) — {data['amount']}"
            p.drawString(100, y_position, f"• {text}")
            y_position -= 20
        p.showPage()
        p.save()
        output.seek(0)

        response = Response(
            output.getvalue(),
            content_type='application/pdf'
        )
        response['Content-Disposition'] = 'attachment; filename="my_cart.pdf"'
        return response
