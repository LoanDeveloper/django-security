from django.urls import path
from .views import RGPDExportView, RGPDEraseView

urlpatterns = [
    path("rgpd/export/", RGPDExportView.as_view(), name="rgpd-export"),
    path("rgpd/erase/", RGPDEraseView.as_view(), name="rgpd-erase"),
]
