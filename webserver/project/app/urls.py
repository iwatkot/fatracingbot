from django.urls import path

from . import views

app_name = "app"
urlpatterns = [
    path("", views.index, name="index"),
    path("login/", views.login, name="login"),
    path("post/", views.post, name="post"),
    path("live/", views.live, name="live"),
    path("logout/", views.logout, name="logout"),
    path("admin/events", views.admin_events, name="admin_events"),
    path(
        "admin/event/download/<str:race_id>/",
        views.admin_event_download,
        name="admin_event_download",
    ),
    path("admin/new_event", views.admin_new_event, name="admin_new_event"),
    path("tds/", views.tds, name="tds"),
    path("tzar/", views.tzar, name="tzar"),
]
