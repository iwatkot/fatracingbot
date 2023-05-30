from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = "app"
urlpatterns = [
    path("", views.index, name="index"),
    path("telegram_login/", views.telegram_login, name="telegram_login"),
    path("post_map/", views.post_map, name="post_map"),
    path("live/", views.live, name="live"),
    path("race/<str:race_name>/", views.race, name="race"),
    path("races/", views.races, name="races"),
    path("logout/", auth_views.LogoutView.as_view(next_page="/"), name="logout"),
    path("admin/", views.admin, name="admin"),
]
