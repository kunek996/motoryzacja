from django.urls import path

from . import views

app_name = "billing"

urlpatterns = [
    path("", views.pricing, name="pricing"),
    path("checkout/", views.checkout, name="checkout"),
    path("success/", views.success, name="success"),
    path("portal/", views.portal, name="portal"),
    path("manage/", views.manage, name="manage"),
    path("dev/activate/", views.dev_activate, name="dev_activate"),
    path("dev/cancel/", views.dev_cancel, name="dev_cancel"),
]
