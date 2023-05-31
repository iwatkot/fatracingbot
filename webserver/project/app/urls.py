from django.urls import path

# from django.contrib.auth import views as auth_views
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = "app"
urlpatterns = [
    path("", views.index, name="index"),
    path("login/", views.login, name="login"),
    path("post/", views.post, name="post"),
    path("live/", views.live, name="live"),
    path("race/<str:race_name>/", views.race, name="race"),
    path("races/", views.races, name="races"),
    path("logout/", views.logout, name="logout"),
    path("admin/", views.admin, name="admin"),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
