from django.urls import path
from . import views

urlpatterns = [
    path("sync/", views.SyncChat.as_view()),
    path("next/", views.SearchNext.as_view())
]