from django import forms
from .models import Song, Playlist, Tag
from django_select2.forms import Select2MultipleWidget
from django.urls import reverse_lazy


# Создание и редактирование плейлиста
class PlaylistForm(forms.ModelForm):
    new_tags = forms.CharField(
        required=False,
        label="Новые теги (через запятую)",
        help_text="Добавьте теги, которых нет в списке, например: #рок, #80е, #любимое"
    )

    class Meta:
        model = Playlist
        fields = ['title', 'cover_image', 'tags']
        # Поле для динамического поиска и добавления тегов (и удаления тоже)
        widgets = {
            'tags': Select2MultipleWidget(
                attrs={
                    # Правильный способ указать URL:
                    'data-ajax--url': reverse_lazy('search_tags'),
                    'data-placeholder': 'Начните вводить тег для поиска...',
                    # Эта опция разрешает AJAX-загрузку
                    'data-ajax--cache': 'true',
                    # Минимальная длина ввода для начала поиска
                    'data-minimum-input-length': '1',
                }
            )
        }


# Добавление трека
class SongForm(forms.ModelForm):
    class Meta:
        model = Song
        # Поле 'playlist' будем устанавливать автоматически
        fields = ['title', 'audio_file']


# Редактирование трека
class SongEditForm(forms.ModelForm):
    class Meta:
        model = Song
        fields = ['title', 'audio_file']
        widgets = {
            'audio_file': forms.ClearableFileInput, # Стандартный виджет для файлов
        }