from django.db import models

class Developer(models.Model):
    name = models.CharField(max_length=100)
    founded = models.DateField()
    country = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class Genre(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField()

    def __str__(self):
        return self.name

class Game(models.Model):
    title = models.CharField(max_length=200)
    developer = models.ForeignKey(Developer, on_delete=models.CASCADE)
    release_date = models.DateField()
    price = models.DecimalField(max_digits=6, decimal_places=2)
    genres = models.ManyToManyField(Genre)
    cover_image = models.ImageField(upload_to="covers/")
    rating = models.FloatField(default=0)
    description = models.TextField(blank=True, verbose_name="Описание")

    def __str__(self):
        return f"{self.title} ({self.release_date.year})"

    def get_absolute_url(self):
        return reverse('game_detail', kwargs={'pk': self.pk})