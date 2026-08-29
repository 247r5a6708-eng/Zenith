from django.urls import path
from tracker.views import landing, privacy_view, terms_view

urlpatterns = [
    path("",         landing,       name="landing"),
    path("privacy/", privacy_view,  name="privacy"),
    path("terms/",   terms_view,    name="terms"),
]
