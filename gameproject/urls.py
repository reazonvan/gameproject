from django.contrib import admin
from django.urls import path
from gameapp.views import game_list, game_detail

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', game_list, name='game_list'),
    path('game/<int:pk>/', game_detail, name='game_detail'),
]