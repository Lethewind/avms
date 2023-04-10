from django.shortcuts import render, get_object_or_404
import json

from django.db.models import Q
from django.forms.models import model_to_dict
from django.http import JsonResponse, Http404
from django.shortcuts import render, get_object_or_404

from algorithm.alns_v3 import alns
from algorithm.constants import *
from algorithm.dicts import *
from algorithm.min_dis import dijkstra
from algorithm.route_inf_cal import cal_all_windows
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
                                  service_end_node=parking_node, is_finished=False)
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

        vehicle_scheduled_need = len(timetable_list)

        if vehicle_scheduled_need > vehicle_capacity:
            return JsonResponse({'scheduling_status': 0})

        vehicle_scheduled = vehicle_available[0:vehicle_scheduled_need]
        print('vehicle_capacity:', vehicle_capacity)
        print('vehicle_scheduled_need:', vehicle_scheduled_need)
        print('vehicle_scheduled:', vehicle_scheduled)
        print('route_list', route_list)

        Vehiclepath_dict = {}  # 键值对为车辆-路径

        for i in range(vehicle_scheduled_need):
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

            vehicle_path = VehiclePath.objects.filter(vehicle=vehicle)
            true_path_list = get_vehicle_true_path(vehicle, vehicle_path)

            for true_path in true_path_list:
                if VehiclePath.objects.filter(
                        Q(vehicle_id=true_path['vehicle_id']) & Q(node_id=true_path['node_id']) & ~Q(
                            service_id__isnull=True)).exists():
                    pass
                VehiclePath(**true_path).save()

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


def get_vehicle_true_path(vehicle, vehicle_path):
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

    true_path_list = []
    for i in range(len(all_path)):
        node = RoadNodes.objects.get(node_id=all_path[i])
        node_arrival_time = all_window[i][0]
        node_departure_time = all_window[i][1]
        vehicle_true_path = VehiclePath(
            vehicle=vehicle, node=node, node_arrival_time=node_arrival_time,
            node_departure_time=node_departure_time
        )
        # vehicle_true_path.save()
        vehicle_true_path.__dict__.pop('_state')
        true_path_list.append(vehicle_true_path.__dict__)
    return true_path_list


def vehicle_path_detail(request, vehicle_id):
    if request.method == 'POST':
        vehicle = get_object_or_404(Vehicle, pk=vehicle_id)
        vehicle_path_list = VehiclePath.objects.filter(vehicle=vehicle)
        for node in vehicle_path_list:
            node.__dict__.pop('_state')
        context = [item.__dict__ for item in vehicle_path_list]
        print(context)
        return JsonResponse(context, safe=False)


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
    try:
        is_succeed = Service.objects.get(id=service_id).delete()
        return JsonResponse({'id': service_id, 'is_succeed': 1}, safe=False)
    except Service.DoesNotExist:
        return JsonResponse({'id': service_id, 'is_succeed': 0}, safe=False)


def service_update(request, service_id):
    new_service_json = json.loads(request.body)
    is_succeed = Service.objects.filter(id=service_id).update(**new_service_json)
    return JsonResponse({'id': service_id, 'is_succeed': is_succeed}, safe=False)


def instructions(request):
    instructions_list = Instruction.objects.all()
    context = []
    for instruction in instructions_list:
        instruction.__dict__.pop('_state')
        context.append(instruction.__dict__)
    print(context)
    return JsonResponse(context, safe=False)


def instruction_detail(request, instruction_id):
    instruction = get_object_or_404(Instruction, pk=instruction_id)
    instruction.__dict__.pop('_state')
    return JsonResponse(model_to_dict(instruction), safe=False)


def instruction_create(request):
    if request.method == 'POST':
        new_instruction_json = json.loads(request.body)
        new_instruction = Instruction(**new_instruction_json)
        new_instruction.save()
        return do_instruction(new_instruction.id)
        # return JsonResponse(model_to_dict(new_instruction), safe=False)


def do_instruction(instruction_id):
    instruction = get_object_or_404(Instruction, pk=instruction_id)
    instruction_type = instruction_type_dict[instruction.instruction_type]
    todo_function_name = 'instruction_' + instruction_type
    return eval(todo_function_name)(instruction_id=instruction.id)


def instruction_delete(request, instruction_id):
    try:
        is_succeed = Instruction.objects.get(id=instruction_id).delete()
        return JsonResponse({'id': instruction_id, 'is_succeed': 1}, safe=False)
    except Instruction.DoesNotExist:
        return JsonResponse({'id': instruction_id, 'is_succeed': 0}, safe=False)


def instruction_update(request, instruction_id):
    new_instruction_json = json.loads(request.body)
    is_succeed = Instruction.objects.filter(instruction_id=instruction_id).update(**new_instruction_json)
    return JsonResponse({'instruction_id': instruction_id, 'is_succeed': is_succeed}, safe=False)


def instruction_task_cancel(instruction_id):
    print("Task Cancel!")
    instruction = get_object_or_404(Instruction, pk=instruction_id)
    flight_id = json.loads(instruction.instruction_content)['flight_id']
    flight = get_object_or_404(Flight, flight_id=flight_id)
    flight.delete()
    return None


def instruction_flight_arrival_time_change(instruction_id):
    print("Arrival Time Change!")
    try:
        instruction = get_object_or_404(Instruction, pk=instruction_id)
        flight_id = json.loads(instruction.instruction_content)['flight_id']
        new_arrival_time = json.loads(instruction.instruction_content)['new_arrival_time']
        flight = get_object_or_404(Flight, flight_id=flight_id)
        flight.arrival_time = new_arrival_time
        flight.save()

        return JsonResponse({'message': 'Arrival Time Change Success!'}, safe=False)
    except Http404:
        return JsonResponse({'message': 'Instruction not found!'}, safe=False)


def instruction_flight_parking_id_change(instruction_id):
    print("Parking ID Change!")
    try:
        instruction = get_object_or_404(Instruction, pk=instruction_id)
        flight_id = json.loads(instruction.instruction_content)['flight_id']
        new_parking_id = json.loads(instruction.instruction_content)['new_parking_id']
        flight = get_object_or_404(Flight, flight_id=flight_id)
        flight.parking_id = new_parking_id
        flight.save()

        return JsonResponse({'message': 'Parking ID Change Success!'}, safe=False)
    except Http404:
        return JsonResponse({'message': 'Instruction not found!'}, safe=False)


def get_vehicle_position(vehicle_id, current_time):
    try:
        vehicle = get_object_or_404(Vehicle, vehicle_id=vehicle_id)
        from_node = VehiclePath.objects.filter(Q(vehicle_id=vehicle_id) & Q(node_arrival_time__lte=current_time)).last()
        to_node = VehiclePath.objects.filter(Q(vehicle_id=vehicle_id) & Q(node_arrival_time__gte=current_time)).first()

        if from_node is None or to_node is None:
            return None, None, None, None
        vehicle_position_x = (current_time - from_node.node_departure_time) / (
                to_node.node_arrival_time - from_node.node_departure_time) * (
                                     to_node.node.node_position_x - from_node.node.node_position_x) + from_node.node.node_position_x
        vehicle_position_y = (current_time - from_node.node_departure_time) / (
                to_node.node_arrival_time - from_node.node_departure_time) * (
                                     to_node.node.node_position_y - from_node.node.node_position_y) + from_node.node.node_position_y
        return from_node.node_id, to_node.node_id, vehicle_position_x, vehicle_position_y
    except Http404:
        return None, None, None, None


def instruction_vehicle_wait(instruction_id):
    print("Vehicle Wait!")
    try:
        vehicle_speed = 400
        instruction = get_object_or_404(Instruction, pk=instruction_id)
        vehicle_id = instruction.instruction_content['vehicle_id']
        wait_time = instruction.instruction_content['wait_time']
        current_time = instruction.instruction_content['current_time']
        vehicle = get_object_or_404(Vehicle, vehicle_id=vehicle_id)
        next_service = VehiclePath.objects.filter(
            Q(vehicle_id=vehicle_id) & ~Q(service_id=None) & Q(node_arrival_time__gt=current_time)).order_by(
            'node_arrival_time').first()

        solution = []
        new_vehicle_list = Vehicle.objects.filter(Q(vehicle_status=1))
        for new_vehicle in new_vehicle_list:
            # new vehicle对应的所有未完成的服务
            unfinished_service_node = VehiclePath.objects.filter(
                Q(vehicle_id=new_vehicle.vehicle_id) & ~Q(service_id=None) & Q(node_arrival_time__gt=current_time))

            for i in range(len(unfinished_service_node) - 1):
                # 插入点的前一个和后一个service
                _service = unfinished_service_node[i]
                service_ = unfinished_service_node[i + 1]
                # 如果该服务的结束时间晚于next_service的开始时间，则break
                if _service.node_departure_time > get_object_or_404(Service,
                                                                    id=next_service.service_id).latest_start_time:
                    break

                service = Service.objects.get(id=_service.service_id)

                # 因插入操作而产生的距离（前点到next_service+next_service到后点）
                from_distance = dijkstra(graph_dict, _service.node_id, next_service.node_id, 2)
                to_distance = dijkstra(graph_dict, service_.node_id, next_service.node_id, 2)
                distance = from_distance + to_distance

                new_arrival_time = int(_service.node_departure_time + from_distance / vehicle_speed)
                new_departure_time = new_arrival_time + next_service.node_arrival_time - next_service.node_departure_time

                # 路上时间和服务持续时间
                delay_time = distance / vehicle_speed + next_service.node_arrival_time - next_service.node_departure_time
                delay_time = max(delay_time, 0)
                if new_vehicle.vehicle_id == vehicle.vehicle_id:
                    delay_time += wait_time

                time_loss = 0
                for temp_service in unfinished_service_node[i + 1:]:
                    changed_arrival_time = temp_service.node_arrival_time + delay_time
                    latest_start_time = get_object_or_404(Service, id=temp_service.service_id).latest_start_time
                    # 如果改变规划后服务开始时间晚于最晚开始时间，则计算time_loss
                    if changed_arrival_time > latest_start_time:
                        time_loss += changed_arrival_time - latest_start_time
                solution.append(
                    {'vehicle_id': new_vehicle.vehicle_id, 'next_srvice_id': next_service.service_id,
                     '_service_id': _service.service_id, 'new_arrival_time': new_arrival_time,
                     'new_departure_time': new_departure_time, 'delay_time': delay_time, 'time_loss': time_loss,
                     'distance': distance, 'total_loss': 10 * time_loss + 3 * distance})
        solution.sort(key=lambda x: x['total_loss'])

        best_solution = solution[0]
        new_vehicle = Vehicle.objects.get(vehicle_id=best_solution['vehicle_id'])
        new_path = VehiclePath(vehicle_id=best_solution['vehicle_id'], service_id=best_solution['next_srvice_id'],
                               node_id=next_service.node_id, node_arrival_time=best_solution['new_arrival_time'],
                               node_departure_time=best_solution['new_departure_time'])
        path_need_update = VehiclePath.objects.filter(
            Q(vehicle_id=best_solution['vehicle_id']) & Q(node_arrival_time__lte=best_solution['new_arrival_time']))
        for path in path_need_update:
            path.node_arrival_time += int(best_solution['delay_time'])
            path.node_departure_time += int(best_solution['delay_time'])
            path.save()

        new_path.save()
        path_list = VehiclePath.objects.filter(vehicle_id=best_solution['vehicle_id'])
        true_path_list = get_vehicle_true_path(new_vehicle, path_list)

        for true_path in true_path_list:
            if VehiclePath.objects.filter(
                    Q(vehicle_id=true_path['vehicle_id']) & Q(node_id=true_path['node_id']) & ~Q(
                        service_id__isnull=True)).exists():
                pass
            VehiclePath(**true_path).save()

        saved_path_list = VehiclePath.objects.filter(vehicle_id=best_solution['vehicle_id'])
        saved_path_dict = []
        for path in saved_path_list:
            path.__dict__.pop('_state')
            saved_path_dict.append(path.__dict__)

        return JsonResponse(saved_path_dict, safe=False)
    except Http404:
        return JsonResponse({'message': 'Instruction not found!'}, safe=False)


def instruction_vehicle_path_change(instruction_id):
    return None


def instruction_roadSection_change(instruction_id):
    print("Road Section Change!")
    try:
        instruction = get_object_or_404(Instruction, pk=instruction_id)
        section_id = json.loads(instruction.instruction_content)['section_id']
        section = get_object_or_404(RoadSections, section_id=section_id)
        section.section_availability = 0
        section.save()

        return JsonResponse({'message': 'Road Section Change Success!'}, safe=False)
    except Http404:
        return JsonResponse({'message': 'Instruction not found!'}, safe=False)


def scene_status(request):
    vehicle_list = Vehicle.objects.all()
    current_time = json.loads(request.body)['current_time']
    vehicle_status_list = []
    for vehicle in vehicle_list:

        from_node, to_node, vehicle_position_x, vehicle_position_y = get_vehicle_position(vehicle_id=vehicle.vehicle_id,
                                                                                          current_time=current_time)
        if from_node is None or to_node is None:
            vehicle_position_x = RoadNodes.objects.get(node_function='-1').node_position_x
            vehicle_position_y = RoadNodes.objects.get(node_function='-1').node_position_y
        vehicle_status_list.append(
            {'vehicle_id': vehicle.vehicle_id, 'from_node': from_node, 'to_node': to_node,
             'vehicle_position_x': vehicle_position_x, 'vehicle_position_y': vehicle_position_y})
    return JsonResponse(vehicle_status_list, safe=False)


def time_data_cal(request):
    time_list = []
    for vehicle in Vehicle.objects.all():

        delay_time = 0
        service_time = 0
        wait_time = 0
        path_list = VehiclePath.objects.filter(vehicle=vehicle)
        if path_list.exists():
            path_list = path_list.order_by('node_arrival_time')
            for path in path_list:
                if path.service_id is not None:
                    wait_time += max(path.service.earliest_start_time - path.node_arrival_time, 0)
                    service_time += path.service.minimum_duration
                    delay_time += max(path.service.latest_start_time - path.node_arrival_time, 0)

            travel_time = path_list[len(path_list) - 1].node_departure_time - path_list[
                0].node_arrival_time - service_time
            time_list.append({'vehicle_id': vehicle.vehicle_id, 'delay_time': delay_time, 'service_time': service_time,
                              'wait_time': wait_time, 'travel_time': travel_time})

    return JsonResponse(time_list, safe=False)
