# from abc import ABC
#
# from rest_framework import serializers
# from web.models import *
#
#
# class RoadNodesSerializer(serializers.Serializer, many=True):
#     class Meta:
#         model = RoadNodes
#         fields = ['node_id', 'node_type', 'node_position_x', 'node_position_y', 'node_function', 'node_capacity',
#                   'node_availability']
#
#
# class VehiclePathSerializer(serializers.Serializer, many=True):
#     class Meta:
#         model = VehiclePath
#         fields = ['vehicle', 'service', 'node', 'node_arrival_time', 'node_departure_time']
#
#
# class VehicleSerializer(serializers.Serializer, many=True):
#     # vehicle_path = VehiclePathSerializer(serializers.ModelSerializer, many=True)
#
#     class Meta:
#         model = Vehicle
#         fields = ['vehicle_id', 'vehicle_type', 'vehicle_energy', 'vehicle_full_energy_mileage',
#                   'vehicle_current_position_x', 'vehicle_current_position_y', 'vehicle_status']
