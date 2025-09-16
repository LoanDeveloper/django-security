from django.urls import path

from .views import (
    RGPDEraseView,
    RGPDExportView,
    confirm_email_view,
    dashboard_view,
    home_view,
    login_view,
    logout_view,
    register_view,
)

urlpatterns = [
    path("", home_view, name="home"),
    path("register/", register_view, name="register"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("dashboard/", dashboard_view, name="dashboard"),
    path("confirm-email/<uidb64>/<token>/", confirm_email_view, name="confirm_email"),
]
