from django.contrib import admin
from .models import Tag, Playlist, Song

admin.site.register(Tag)
admin.site.register(Playlist)
admin.site.register(Song)
