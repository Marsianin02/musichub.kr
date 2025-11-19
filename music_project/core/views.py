from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.http import HttpResponseForbidden, JsonResponse
from django.db.models import Q
import json
from .models import Playlist, Song, Tag
from .forms import PlaylistForm, SongForm, SongEditForm


# Домашняя страница
def home(request):
    # Получаем все плейлисты
    playlists = Playlist.objects.all()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'core/partials/home_partial.html', {'playlists': playlists})
    return render(request, 'core/home.html', {'playlists': playlists})


# Страница плейлиста
def playlist_detail(request, pk):
    playlist = get_object_or_404(Playlist, pk=pk)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'core/partials/playlist_detail_partial.html', {'playlist': playlist})
    return render(request, 'core/playlist_detail.html', {'playlist': playlist})


# Поиск тегов для AJAX-запросов от виджета
def search_tags(request):
    term = request.GET.get('term', '').strip()
    tags = Tag.objects.all()

    if term:
        query = request.GET.get('q', '').strip()
        if query:
            tags = tags.filter(name__icontains=query)

    # Форматируем ответ для виджета
    results = [
        {'id': tag.id, 'text': tag.name}
        for tag in tags
    ]

    return JsonResponse({'results': results})


# Вывод результатов поиска
def search_view(request):
    # Получаем поисковый запрос 'q' из GET-параметра
    query = request.GET.get('q', '').strip()

    playlists_by_title = Playlist.objects.none()
    playlists_by_tag = Playlist.objects.none()
    songs_by_title = Song.objects.none()
    songs_by_tag = Song.objects.none()

    if query:
        playlists_by_title = Playlist.objects.filter(Q(title__icontains=query)).distinct()
        playlists_by_tag = Playlist.objects.filter(Q(tags__name__icontains=query)).distinct()
        songs_by_title = Song.objects.filter(Q(title__icontains=query)).distinct()
        songs_by_tag = Song.objects.filter(Q(playlist__tags__name__icontains=query)).distinct()

    context = {
        'query': query,
        'playlists_by_title': playlists_by_title,
        'playlists_by_tag': playlists_by_tag,
        'songs_by_title': songs_by_title,
        'songs_by_tag': songs_by_tag,
    }

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # Если это AJAX-запрос, отдаем только "кусочек" HTML
        return render(request, 'core/partials/search_results_partial.html', context)
    return render(request, 'core/search_results.html', context)


# Тут уже все что требует авторизации
# Создание плейлиста
@login_required
def create_playlist(request):
    if request.method == 'POST':
        form = PlaylistForm(request.POST, request.FILES)
        if form.is_valid():
            playlist = form.save(commit=False)
            playlist.creator = request.user
            playlist.save()

            # Сначала сохраняем теги, выбранные из существующего списка
            form.save_m2m()

            # Затем обрабатываем и добавляем новые теги
            new_tags_str = form.cleaned_data.get('new_tags', '').strip()
            if new_tags_str:
                tag_names = [name.strip() for name in new_tags_str.split(',')]
                for name in tag_names:
                    if name:
                        # get_or_create ищет без учета регистра, создает с правильным регистром
                        tag, created = Tag.objects.get_or_create(
                            name__iexact=name,
                            defaults={'name': name}
                        )
                        playlist.tags.add(tag)

            return redirect('playlist_detail', pk=playlist.pk)
    else:
        form = PlaylistForm()
    return render(request, 'core/playlist_form.html', {'form': form, 'title': 'Создать плейлист'})


# Редактирование плейлиста
@login_required
def edit_playlist(request, pk):
    playlist = get_object_or_404(Playlist, pk=pk)
    if playlist.creator != request.user and not request.user.is_superuser:
        return HttpResponseForbidden("Вы не можете редактировать чужой плейлист.")

    if request.method == 'POST':
        form = PlaylistForm(request.POST, request.FILES, instance=playlist)
        if form.is_valid():
            # Сохраняем основные поля. commit=False, чтобы M2M не сохранялись сразу.
            playlist_instance = form.save(commit=False)
            playlist_instance.save()

            # Сохраняем M2M связи для уже выбранных тегов (из 'tags')
            form.save_m2m()

            # Обрабатываем и добавляем НОВЫЕ теги (из 'new_tags')
            new_tags_str = form.cleaned_data.get('new_tags', '').strip()
            if new_tags_str:
                tag_names = [name.strip() for name in new_tags_str.split(',') if name.strip()]
                for name in tag_names:
                    tag, created = Tag.objects.get_or_create(
                        name__iexact=name,
                        defaults={'name': name}
                    )
                    playlist_instance.tags.add(tag)

            return redirect('playlist_detail', pk=playlist_instance.pk)
    else:
        form = PlaylistForm(instance=playlist)

    return render(request, 'core/playlist_form.html', {
        'form': form,
        'title': 'Редактировать плейлист'
    })


# Удаление плейлиста
@login_required
def delete_playlist(request, pk):
    playlist = get_object_or_404(Playlist, pk=pk)
    if playlist.creator != request.user and not request.user.is_superuser:
        return HttpResponseForbidden("Вы не можете удалить чужой плейлист.")

    if request.method == 'POST':
        playlist.delete()
        return redirect('home')
    return render(request, 'core/playlist_confirm_delete.html', {'playlist': playlist})


# Добавление песни в плейлист
@login_required
def add_song_to_playlist(request, pk):
    playlist = get_object_or_404(Playlist, pk=pk)
    if playlist.creator != request.user and not request.user.is_superuser:
        return HttpResponseForbidden("Вы не можете добавлять песни в чужой плейлист.")

    if request.method == 'POST':
        form = SongForm(request.POST, request.FILES)
        if form.is_valid():
            song = form.save(commit=False)
            song.playlist = playlist
            song.uploaded_by = request.user
            song.save()
            return redirect('playlist_detail', pk=playlist.pk)
    else:
        form = SongForm()
    return render(request, 'core/song_form.html', {'form': form, 'playlist': playlist})


# Редактирование песни
@login_required
def edit_song(request, pk):
    song = get_object_or_404(Song, pk=pk)
    playlist = song.playlist
    # Проверка прав
    if playlist.creator != request.user and not request.user.is_superuser:
        return HttpResponseForbidden("Вы не можете редактировать этот трек.")

    if request.method == 'POST':
        # Передаем request.FILES в форму, чтобы она могла обработать загрузку файла.
        form = SongEditForm(request.POST, request.FILES, instance=song)
        if form.is_valid():
            form.save()  # Сохраняем изменения (и новый файл, если он есть)
            return redirect('playlist_detail', pk=playlist.pk)
    else:
        form = SongEditForm(instance=song)

    return render(request, 'core/song_edit_form.html', {'form': form, 'song': song})


# Удаление трека
@login_required
def delete_song(request, pk):
    song = get_object_or_404(Song, pk=pk)
    playlist = song.playlist  # Сохраняем pk плейлиста для редиректа

    # Проверка прав (такая же, как при редактировании)
    if playlist.creator != request.user and not request.user.is_superuser:
        return HttpResponseForbidden("Вы не можете удалить этот трек.")

    if request.method == 'POST':
        song.delete()
        # Возвращаемся на страницу плейлиста, откуда удалили трек
        return redirect('playlist_detail', pk=playlist.pk)

        # Если метод GET, показываем страницу подтверждения
    return render(request, 'core/song_confirm_delete.html', {'song': song})


# Ну тут уже все связанное с авторизацией
def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'core/signup.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'core/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('home')
