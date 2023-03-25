from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('flights/', views.flights, name='flights'),
    path('flights/<str:flight_id>/', views.flight_detail, name='flight'),
    path('vehicles/', views.vehicles, name='vehicles'),
    path('vehicles/<str:vehicle_id>/', views.vehicle_detail, name='vehicle'),
    path('services/', views.services, name='services'),
    path('services/<str:service_id>/', views.service_detail, name='service'),
    path('services_generation', views.services_generation, name='services_generation'),
    path('vehicle_scheduling', views.vehicle_scheduling, name='vehicle_scheduling'),
    path('vehicles/<str:vehicle_id>/path/', views.vehicle_path, name='vehicle_path'),
]
