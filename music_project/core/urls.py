from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    # Авторизация
    path('signup/', views.signup, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    # Плейлисты
    path('playlist/create/', views.create_playlist, name='create_playlist'),
    path('playlist/<int:pk>/', views.playlist_detail, name='playlist_detail'),
    path('playlist/<int:pk>/edit/', views.edit_playlist, name='edit_playlist'),
    path('playlist/<int:pk>/delete/', views.delete_playlist, name='delete_playlist'),
    # Песни
    path('playlist/<int:pk>/add_song/', views.add_song_to_playlist, name='add_song_to_playlist'),
    path('tags/search/', views.search_tags, name='search_tags'),
    path('song/<int:pk>/edit/', views.edit_song, name='edit_song'),
    path('song/<int:pk>/delete/', views.delete_song, name='delete_song'),
    path('search/', views.search_view, name='search'),
]