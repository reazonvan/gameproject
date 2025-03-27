from django.shortcuts import render, get_object_or_404
from .models import Game, Developer, Genre


def game_list(request):
    games = Game.objects.all().select_related('developer').prefetch_related('genres')
    developers = Developer.objects.all()
    genres = Genre.objects.all()

    return render(request, 'game_list.html', {
        'games': games,
        'developers': developers,
        'genres': genres
    })


def game_detail(request, pk):
    game = get_object_or_404(Game.objects.select_related('developer').prefetch_related('genres'), pk=pk)
    return render(request, 'game_detail.html', {'game': game})