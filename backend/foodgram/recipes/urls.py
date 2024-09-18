from django.urls import path

from . import views

urlpatterns = [
    path('<str:short_link>/', views.redirect_to_recipe, name='redirect'),
]
