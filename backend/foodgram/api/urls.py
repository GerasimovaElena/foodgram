from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CustomUserViewSet, TagViewSet, IngredientViewSet, RecipeViewSet, DownloadCartView

router = DefaultRouter()
router.register(r'users', CustomUserViewSet, basename='user')
router.register(r'tags', TagViewSet, basename='tag')
router.register(r'ingredients', IngredientViewSet, basename='ingredient')
router.register(r'recipes', RecipeViewSet, basename='recipe')

urlpatterns = [
    path('recipes/<int:pk>/get-link/', RecipeViewSet.as_view({'get': 'get_short_link'})),
    path('recipes/download_shopping_cart/', DownloadCartView.as_view()),
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
    path('', include('djoser.urls')),
]
