from django.urls import path
from . import views

app_name = "my_notes_app"
urlpatterns = [
    path("", views.index, name="index"),
]
