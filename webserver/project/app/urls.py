from django.urls import path
from . import views

app_name = "app"
urlpatterns = [
    path("", views.index, name="index"),
    path("telegram_login/", views.telegram_login, name="telegram_login"),
    path("post_map/", views.post_map, name="post_map"),
    path("live/", views.live, name="live"),
    path("race/<str:race_name>/", views.race, name="race"),
    path("races/", views.races, name="races"),
]
