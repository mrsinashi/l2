from django.urls import path
from . import views

urlpatterns = [
    path('load', views.load),
    path('counts', views.counts),
    path('hosp-services-by-type', views.hosp_services_by_type),
    path('make-service', views.make_service),
    path('directions-by-key', views.directions_by_key),
]
