from django.db import models
from django.contrib.auth.models import User


# Модель для тегов
class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Тег")

    def __str__(self):
        return f"#{self.name}"


# Модель для плейлистов
class Playlist(models.Model):
    title = models.CharField(max_length=200, verbose_name="Название плейлиста")
    # При удалении пользователя плейлисты остаются (null=True).
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="playlists")
    cover_image = models.ImageField(upload_to='playlist_covers/', verbose_name="Обложка")
    # Связь "многие-ко-многим" с тегами
    tags = models.ManyToManyField(Tag, blank=True, verbose_name="Теги")

    def __str__(self):
        return f"'{self.title}' от {self.creator.username if self.creator else 'N/A'}"


# Модель для песен
class Song(models.Model):
    title = models.CharField(max_length=200, verbose_name="Название песни")
    # ForeignKey указывает на Playlist
    playlist = models.ForeignKey(Playlist, related_name='songs', on_delete=models.CASCADE, verbose_name="Плейлист")
    audio_file = models.FileField(upload_to='songs/')
    # А также на того кто загрузил
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.title