from django.contrib import admin
from .models import Game, Developer, Genre

@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ("title", "developer", "release_date")
    list_filter = ("genres", "developer")
    search_fields = ("title", "developer__name")

admin.site.register([Developer, Genre])
