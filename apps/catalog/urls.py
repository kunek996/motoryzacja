from django.urls import path

from . import views

app_name = "catalog"

urlpatterns = [
    path("", views.home, name="home"),
    path("makes/", views.makes_overview, name="makes"),
    path("new/", views.create, name="create"),
    path("suggest-car/", views.suggest_car, name="suggest_car"),
    path("saved/", views.saved, name="saved"),
    path("mine/", views.mine, name="mine"),
    path("api/models/", views.models_for_make, name="api_models"),
    path("<int:pk>-<slug:slug>/", views.detail, name="detail"),
    path("<int:pk>/", views.detail, name="detail_short"),
    path("<int:pk>/edit/", views.edit, name="edit"),
    path("<int:pk>/delete/", views.delete, name="delete"),
    path("<int:pk>/vote/", views.toggle_vote, name="vote"),
    path("<int:pk>/bookmark/", views.toggle_bookmark, name="bookmark"),
    path("<int:pk>/comment/", views.add_comment, name="comment"),
    path("<int:pk>/report/", views.report, name="report"),
    path("comment/<int:pk>/delete/", views.delete_comment, name="comment_delete"),
    path("attachment/<int:pk>/", views.download_attachment, name="download"),
    path("attachment/<int:pk>/delete/", views.delete_attachment, name="attachment_delete"),
]
