from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from web.models import *
from algorithm.time_window import time_arrange_small
from algorithm.dicts import *
from algorithm.constants import *
from algorithm.alns_v3 import alns


# Create your views here.


def index(request):
    return render(request, 'web/index.html')


def flights(request):
    flights_list = Flight.objects.all()
    print(flights_list)
    context = {'flights_list': flights_list}
    return render(request, 'web/flights.html', context)


def flight_detail(request, flight_id):
    flight = get_object_or_404(Flight, pk=flight_id)
    print(flight.__dict__)
    context = {'flight_dict': flight.__dict__}
    return render(request, 'web/flight_detail.html', context)


def services_generation(request):
    if request.method == 'POST':
        print('Service generation')
        # Flight.objects.filter(is_served=True).update(is_served=False)
        flights_unserved = Flight.objects.filter(~Q(is_served=True))

        print('flights_unserved:', flights_unserved)
        for flight in flights_unserved:
            services_list = time_arrange_small(flight.on_block_time, flight.off_block_time)
            for service_type, time_window in services_list.items():
                print(service_type)
                print(time_window)
                parking_node = RoadNodes.objects.get(node_function=flight.parking_id)
                service = Service(flight=flight, service_type=service_type, earliest_start_time=time_window[0],
                                  latest_start_time=time_window[1],
                                  minimum_duration=service_minimum_duration_dict[service_type],
                                  maximum_duration=service_maximum_duration_dict[service_type],
                                  earliest_end_time=time_window[0] + service_minimum_duration_dict[service_type],
                                  latest_end_time=time_window[1] + service_maximum_duration_dict[service_type],
                                  service_vehicle_type=service_vehicle_dict[service_type],
                                  service_vehicle_num=service_vehicle_num, service_start_node=parking_node,
                                  service_delay_time=0,
                                  service_end_node=parking_node)
                print(service)
                service.save()
        # return redirect('web:service_generation')
        flights_unserved.update(is_served=True)
    return render(request, 'web/flights.html')


def services(request):
    services_list = Service.objects.all()
    print(services_list)
    context = {'services_list': services_list}
    return render(request, 'web/services.html', context)


def service_detail(request, service_id):
    service = get_object_or_404(Service, pk=service_id)
    print(service.__dict__)
    context = {'service_dict': service.__dict__}
    return render(request, 'web/service_detail.html', context)


def vehicle_scheduling(request):
    if request.method == 'POST':
        print('Vehicle scheduling')
        service_type = 'QJ'
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
        for service in services_unscheduled:
            service_id = service.id
            x_coord = service.service_start_node.node_position_x
            y_coord = service.service_start_node.node_position_y
            demand = 1
            start_time = service.earliest_start_time
            end_time = service.latest_start_time
            service_time = int((service.minimum_duration + service.maximum_duration) / 2)
            demands.append({'service_id': service_id, 'x_coord': x_coord, 'y_coord': y_coord, 'demand': demand,
                            'start_time': start_time,
                            'end_time': end_time, 'service_time': service_time})

        cost_of_time, cost_of_distance, opt_type, obj, route_list, timetable_list = alns(
            demands=demands, depots=depots, rand_d_max=0.4, rand_d_min=0.1,
            worst_d_min=5, worst_d_max=20, regret_n=5, r1=30, r2=20, r3=10, rho=0.5,
            phi=0.9, epochs=1, pu=5, v_cap=vehicle_capacity, v_speed=400, opt_type=1)

        vehicle_scheduled_num = len(timetable_list)
        vehicle_scheduled = vehicle_available[0:vehicle_scheduled_num]
        print('vehicle_scheduled_need:', vehicle_scheduled_num)
        print('vehicle_scheduled:', vehicle_scheduled)
        print('vehicle_scheduled_num:', len(vehicle_scheduled))

        for i in range(vehicle_scheduled_num):
            timetable = timetable_list[i]
            route = route_list[i]
            vehicle = vehicle_scheduled[i]
            deport = RoadNodes.objects.get(node_id=route[0])

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
                vehicle_path.save()

        services_unscheduled.update(is_scheduled=True)
    return render(request, 'web/services.html')


def vehicles(request):
    vehicles_list = Vehicle.objects.all()
    print(vehicles_list)
    context = {'vehicles_list': vehicles_list}
    return render(request, 'web/vehicles.html', context)


def vehicle_detail(request, vehicle_id):
    vehicle = get_object_or_404(Vehicle, pk=vehicle_id)
    print(vehicle.__dict__)
    context = {'vehicle_dict': vehicle.__dict__}
    return render(request, 'web/vehicles_detail.html', context)


def vehicle_path(request, vehicle_id):
    vehicle = get_object_or_404(Vehicle, pk=vehicle_id)
    vehicle_path_list = VehiclePath.objects.filter(vehicle=vehicle)
    context = {'vehicle_path_list': [node.__dict__ for node in vehicle_path_list]}
    return render(request, 'web/vehicle_path.html', context)
