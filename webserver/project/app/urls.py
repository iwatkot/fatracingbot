from django.urls import path

from . import views

app_name = "app"
urlpatterns = [
    path("", views.index, name="index"),
    path("login/", views.login, name="login"),
    path("post/", views.post, name="post"),
    path("live/", views.live, name="live"),
    path("logout/", views.logout, name="logout"),
    path("admin/", views.admin, name="admin"),
    path("tds/", views.tds, name="tds"),
    path("tzar/", views.tzar, name="tzar"),
]
