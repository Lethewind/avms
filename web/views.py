from django.shortcuts import render, get_object_or_404
import json

from django.db.models import Q
from django.forms.models import model_to_dict
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404

from algorithm.alns_v3 import alns
from algorithm.constants import *
from algorithm.dicts import *
from algorithm.time_window import time_arrange_small
from web.models import *
from web.serializers import *


# Create your views here.


def index(request):
    return render(request, 'web/index.html')


def flights(request):
    flights_list = Flight.objects.all()
    context = [model_to_dict(item) for item in flights_list]
    # return render(request, 'web/flights.html', context)
    return JsonResponse(context, safe=False)


def flight_detail(request, flight_id):
    flight = get_object_or_404(Flight, pk=flight_id)
    context = model_to_dict(flight)
    # return render(request, 'web/flight_detail.html', context)
    return JsonResponse(context, safe=False)


def services_generation(request):
    if request.method == 'POST':
        now_service = Service.objects.filter(service_vehicle_num=1)
        for per_s in now_service:
            per_s.delete()
        print('Service generation')
        # Flight.objects.filter(is_served=True).update(is_served=False)
        flights_unserved = Flight.objects.filter(~Q(is_served=False))

        # print('flights_unserved:', flights_unserved)
        service_list = []
        no = 1
        for flight in flights_unserved:
            services_list = time_arrange_small(flight.on_block_time, flight.off_block_time)
            for service_type, time_window in services_list.items():
                print(service_type)
                print(time_window)

                try:
                    parking_node = RoadNodes.objects.get(node_function=flight.parking_id)
                except Exception as e:
                    print(flight.flight_id)
                    pass
                service = Service(id=no,
                                  flight=flight, service_type=service_type, earliest_start_time=time_window[0],
                                  latest_start_time=time_window[1],
                                  minimum_duration=service_minimum_duration_dict[service_type],
                                  maximum_duration=service_maximum_duration_dict[service_type],
                                  earliest_end_time=time_window[0] + service_minimum_duration_dict[service_type],
                                  latest_end_time=time_window[1] + service_maximum_duration_dict[service_type],
                                  service_vehicle_type=service_vehicle_dict[service_type],
                                  service_vehicle_num=service_vehicle_num, service_start_node=parking_node,
                                  service_delay_time=0,
                                  service_end_node=parking_node)
                no += 1
                service_list.append(model_to_dict(service))
                service.save()
        # return redirect('web:service_generation')
        print(len(service_list))
        flights_unserved.update(is_served=True)
        # return render(request, 'web/flights.html')
        return JsonResponse(service_list, safe=False)


def services(request):
    services_list = Service.objects.all()
    context = [model_to_dict(item) for item in services_list]
    # return render(request, 'web/services.html', context)
    return JsonResponse(context, safe=False)


def service_detail(request, service_id):
    service = get_object_or_404(Service, pk=service_id)
    context = model_to_dict(service)
    # return render(request, 'web/service_detail.html', context)
    return JsonResponse(context, safe=False)


def vehicle_scheduling(request):
    if request.method == 'POST':
        print('Vehicle scheduling')
        service_type = 'QY'
        VehiclePath.objects.all().delete()
        Service.objects.filter(is_scheduled=True).update(is_scheduled=False)  # 重置一下，测试用
        services_unscheduled = Service.objects.filter(
            ~Q(is_scheduled=True) & Q(service_type=service_type))  # 未安排车辆&清洁服务
        vehicle_available = Vehicle.objects.filter(
            Q(vehicle_status=1) & Q(vehicle_type=service_vehicle_dict[service_type]))
        vehicle_capacity = len(vehicle_available)

        depots = []
        deports_list = RoadNodes.objects.filter(node_function=-1)  # 车库
        for deport in deports_list:
            deport_id = deport.node_id
            x_coord = deport.node_position_x
            y_coord = deport.node_position_y
            # capacity = vehicle_capacity
            capacity = 100
            start_time = 0
            end_time = 1440
            depots.append({'deport_id': deport_id, 'x_coord': x_coord, 'y_coord': y_coord, 'capacity': capacity,
                           'start_time': start_time,
                           'end_time': end_time})
            start_time = 0
            end_time = 1440
            depots.append({'deport_id': deport_id, 'x_coord': x_coord, 'y_coord': y_coord, 'capacity': capacity,
                           'start_time': start_time,
                           'end_time': end_time})

        demands = []
        demand_dict = []
        for service in services_unscheduled:
            service_node = service.id

            x_coord = service.service_start_node.node_position_x
            y_coord = service.service_start_node.node_position_y
            demand = 1
            start_time = service.earliest_start_time
            end_time = service.latest_start_time
            service_time = int((service.minimum_duration + service.maximum_duration) / 2)
            demands.append({'service_id': service_node, 'x_coord': x_coord, 'y_coord': y_coord, 'demand': demand,
                            'start_time': start_time,
                            'end_time': end_time, 'service_time': service_time})
            demand_dict.append(service.service_start_node)

        cost_of_time, cost_of_distance, opt_type, obj, route_list, timetable_list = alns(
            demands=demands, depots=depots, rand_d_max=0.4, rand_d_min=0.1,
            worst_d_min=5, worst_d_max=20, regret_n=5, r1=30, r2=20, r3=10, rho=0.5,
            phi=0.9, epochs=3, pu=3, v_cap=vehicle_capacity, v_speed=400, opt_type=1, demand_list_N=demand_dict)

        vehicle_scheduled_num = len(timetable_list)
        vehicle_scheduled = vehicle_available[0:vehicle_scheduled_num]
        print('vehicle_scheduled_need:', vehicle_scheduled_num)
        print('vehicle_scheduled:', vehicle_scheduled)
        print('route_list', route_list)
        print('vehicle_scheduled_num:', len(vehicle_scheduled))

        Vehiclepath_dict = {}  # 键值对为车辆-路径

        for i in range(vehicle_scheduled_num):
            timetable = timetable_list[i]
            route = route_list[i]
            vehicle = vehicle_scheduled[i]
            deport = RoadNodes.objects.get(node_id=route[0])
            Vehiclepath_dict[vehicle.vehicle_id] = []

            for j in range(len(route)):
                node_arrival_time, node_departure_time = timetable[j]
                if j == len(route) - 1 or j == 0:
                    vehicle_path = VehiclePath(vehicle=vehicle, node=deport, node_arrival_time=node_arrival_time,
                                               node_departure_time=node_departure_time)
                else:
                    service = Service.objects.get(id=route[j])
                    node = service.service_start_node
                    vehicle_path = VehiclePath(vehicle=vehicle, service=service, node=node,
                                               node_arrival_time=node_arrival_time,
                                               node_departure_time=node_departure_time)
                Vehiclepath_dict[vehicle.vehicle_id].append(model_to_dict(vehicle_path))
                vehicle_path.save()

        services_unscheduled.update(is_scheduled=True)
        return JsonResponse(Vehiclepath_dict)
        # return render(request, 'web/services.html')


def vehicles(request):
    vehicles_list = Vehicle.objects.all()
    # context = [model_to_dict(item) for item in vehicles_list]
    for item in vehicles_list:
        item.__dict__.pop('_state')
    context = [item.__dict__ for item in vehicles_list]

    print(context)
    # return render(request, 'web/vehicles.html', context)
    return JsonResponse(context, safe=False)


def vehicle_detail(request, vehicle_id):
    vehicle = get_object_or_404(Vehicle, pk=vehicle_id)
    # print(vehicle)
    vehicle.__dict__.pop('_state')
    context = vehicle.__dict__
    # context = VehicleSerializer(vehicle)
    # context = json.dumps(vehicle, default=lambda o: o.__dict__, indent=4)
    print(context)
    # return render(request, 'web/vehicles_detail.html', context)
    return JsonResponse(context, safe=False)


def vehicle_path(request, vehicle_id):
    if request.method == 'POST':
        vehicle = get_object_or_404(Vehicle, pk=vehicle_id)
        vehicle_path = VehiclePath.objects.filter(vehicle=vehicle)
        onepath_inf = []
        onepath_window = []
        for per_path in vehicle_path:
            onepath_inf.append(per_path.node_id)
            onepath_window.append([per_path.node_arrival_time, per_path.node_departure_time])
        road_dict = {}
        road_all = RoadSections.objects.all()
        for per_road in road_all:
            road_dict.setdefault(per_road.section_end_node_id, {})
            road_dict[per_road.section_end_node_id].setdefault(per_road.section_start_node_id, per_road)
            road_dict.setdefault(per_road.section_start_node_id, {})
            road_dict[per_road.section_start_node_id].setdefault(per_road.section_end_node_id, per_road)
        all_path, all_window = cal_all_windows(graph_dict, onepath_inf, onepath_window, road_dict)
        print(all_path)
        print(all_window)
        for per_path in vehicle_path:
            per_path.delete()

        vehicle_detail_dist = {}
        vehicle_detail_dist[vehicle.vehicle_id] = []

        for i in range(len(all_path)):
            node = RoadNodes.objects.get(node_id=all_path[i])
            node_arrival_time = all_window[i][0]
            node_departure_time = all_window[i][1]
            vehicle_true_path = VehiclePath(
                vehicle=vehicle, node=node, node_arrival_time=node_arrival_time,
                node_departure_time=node_departure_time
            )
            vehicle_detail_dist[vehicle.vehicle_id].append(model_to_dict(vehicle_true_path))
            vehicle_true_path.save()
            # vehicle_detail_list.append({'path_id': all_path[i], 'arrival_time': all_window[i][0], 'departure_time': all_window[i][1]})
        return JsonResponse(vehicle_detail_dist)


def flights_create(request):
    if request.method == 'POST':
        new_flight_json = json.loads(request.body)
        new_flight = Flight(**new_flight_json)
        new_flight.save()
        return JsonResponse(model_to_dict(new_flight), safe=False)


def flights_delete(request):
    flight_id_list = json.loads(request.body)['flight_id_list']
    print(flight_id_list)
    context = []
    for flight_id in flight_id_list:
        try:
            flight = Flight.objects.get(flight_id=flight_id)
            flight.delete()
            is_succeed = 1
        except Flight.DoesNotExist:
            is_succeed = 0

        context.append({'flight_id': flight_id, 'is_succeed': is_succeed})
    print(context)
    return JsonResponse(context, safe=False)


def flight_update(request, flight_id):
    new_flight_json = json.loads(request.body)
    is_succeed = Flight.objects.filter(flight_id=flight_id).update(**new_flight_json)
    return JsonResponse({'flight_id': flight_id, 'is_succeed': is_succeed}, safe=False)


def flight_delete(request, flight_id):
    try:
        is_succeed = Flight.objects.get(flight_id=flight_id).delete()
        return JsonResponse({'flight_id': flight_id, 'is_succeed': 1}, safe=False)
    except Flight.DoesNotExist:
        return JsonResponse({'flight_id': flight_id, 'is_succeed': 0}, safe=False)


def flights_update(request):
    return None


def vehicles_create(request):
    if request.method == 'POST':
        new_vehicle_json = json.loads(request.body)
        new_vehicle = Vehicle(**new_vehicle_json)
        new_vehicle.save()
        return JsonResponse(model_to_dict(new_vehicle), safe=False)


def vehicles_delete(request):
    vehicle_id_list = json.loads(request.body)['vehicle_id_list']
    context = []
    for vehicle_id in vehicle_id_list:
        try:
            vehicle = Vehicle.objects.get(vehicle_id=vehicle_id)
            vehicle.delete()
            is_succeed = 1
        except Flight.DoesNotExist:
            is_succeed = 0

        context.append({'vehicle_id': vehicle_id, 'is_succeed': is_succeed})
    print(context)
    return JsonResponse(context, safe=False)


def vehicle_delete(request):
    vehicle_id = json.loads(request.body)['vehicle_id']
    try:
        is_succeed = Vehicle.objects.get(vehicle_id=vehicle_id).delete()
        return JsonResponse({'vehicle_id': vehicle_id, 'is_succeed': 1}, safe=False)
    except Vehicle.DoesNotExist:
        return JsonResponse({'vehicle_id': vehicle_id, 'is_succeed': 0}, safe=False)


def vehicle_update(request, vehicle_id):
    new_vehicle_json = json.loads(request.body)
    is_succeed = Vehicle.objects.filter(vehicle_id=vehicle_id).update(**new_vehicle_json)
    return JsonResponse({'vehicle_id': vehicle_id, 'is_succeed': is_succeed}, safe=False)


def vehicles_update(request):
    return None


def services_create(request):
    if request.method == 'POST':
        new_service_json = json.loads(request.body)
        new_service = Service(**new_service_json)
        new_service.save()
        return JsonResponse(model_to_dict(new_service), safe=False)


def services_delete(request):
    service_id_list = json.loads(request.body)['service_id_list']
    context = []
    for service_id in service_id_list:
        try:
            service = Service.objects.get(service_id=service_id)
            service.delete()
            is_succeed = 1
        except Flight.DoesNotExist:
            is_succeed = 0

        context.append({'service_id': service_id, 'is_succeed': is_succeed})
    print(context)
    return JsonResponse(context, safe=False)


def services_update(request):
    return None


def service_delete(request, service_id):
    service_id = json.loads(request.body)['id']
    try:
        is_succeed = Service.objects.get(id=service_id).delete()
        return JsonResponse({'id': service_id, 'is_succeed': 1}, safe=False)
    except Service.DoesNotExist:
        return JsonResponse({'id': service_id, 'is_succeed': 0}, safe=False)


def service_update(request, service_id):
    new_service_json = json.loads(request.body)
    is_succeed = Service.objects.filter(id=service_id).update(**new_service_json)
    return JsonResponse({'id': service_id, 'is_succeed': is_succeed}, safe=False)
