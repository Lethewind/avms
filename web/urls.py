from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    # flights
    path('flights/', views.flights, name='flights'),
    path('flights/create/', views.flights_create, name='flights_create'),
    path('flights/update/', views.flights_update, name='flights_update'),
    path('flights/delete/', views.flights_delete, name='flights_delete'),
    path('flights/<str:flight_id>/', views.flight_detail, name='flight'),
    path('flights/<str:flight_id>/delete/', views.flight_delete, name='flight'),
    path('flights/<str:flight_id>/update/', views.flight_update, name='flight_path'),

    # vehicles
    path('vehicles/', views.vehicles, name='vehicles'),
    path('vehicles/create/', views.vehicles_create, name='vehicles_create'),
    path('vehicles/update/', views.vehicles_update, name='vehicles_update'),
    path('vehicles/delete/', views.vehicles_delete, name='vehicles_delete'),
    path('vehicle_scheduling', views.vehicle_scheduling, name='vehicle_scheduling'),
    path('scene_status/', views.scene_status, name='scene_status'),
    path('time_data_cal/', views.time_data_cal, name='time_data_cal'),
    path('vehicles/<str:vehicle_id>/', views.vehicle_detail, name='vehicle'),
    path('vehicles/<str:vehicle_id>/delete/', views.vehicle_delete, name='vehicle'),
    path('vehicles/<str:vehicle_id>/update/', views.vehicle_update, name='vehicle_path'),
    path('vehicles/<str:vehicle_id>/path/', views.vehicle_path_detail, name='vehicle_path'),

    # services
    path('services/', views.services, name='services'),
    path('services/create/', views.services_create, name='services_create'),
    path('services/update/', views.services_update, name='services_update'),
    path('services/delete/', views.services_delete, name='services_delete'),
    path('services/<str:service_id>/', views.service_detail, name='service'),
    path('services/<str:service_id>/delete/', views.service_delete, name='service'),
    path('services/<str:service_id>/update/', views.service_update, name='service_path'),
    path('services_generation', views.services_generation, name='services_generation'),

    # instructions
    path('instructions/', views.instructions, name='instructions'),
    path('instructions/create/', views.instruction_create, name='instruction_create'),
    path('instructions/<str:instruction_id>/', views.instruction_detail, name='instruction'),
    path('instructions/<str:instruction_id>/delete/', views.instruction_delete, name='instruction'),
    path('instructions/<str:instruction_id>/update/', views.instruction_update, name='instruction_path'),

    # instructions-do
    # path('instructions/task_cancel/', views.instruction_task_cancel, name='instruction_task_cancel'),
    # path('instructions/flight_arrival_time_change/', views.instruction_flight_arrival_time_change,
    #      name='instruction_flight_arrival_time_change'),
    # path('instructions/flight_parking_id_change/', views.flight_parking_id_change,
    #      name='flight_parking_id_change'),
    # path('instructions/vehicle_wait/', views.instruction_vehicle_wait, name='instruction_vehicle_wait'),
    # path('instructions/vehicle_path_change/', views.instruction_vehicle_path_change,
    #      name='instruction_vehicle_path_change'),
    # path('instructions/roadsection_change/', views.instruction_roadSection_change,
    #      name='instruction_roadSection_change'),
]
