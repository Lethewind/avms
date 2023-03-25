import xlsxwriter
from numba import njit, cuda, jit
from numba.typed import List
import math
import random
import numpy as np
import copy
import matplotlib.pyplot as plt
import csv
import sys
import time
import pandas as pd
from algorithm.min_dis import dijkstra
from algorithm.dicts import graph_dict

start = time.time()


# 可行解类
class Sol:
    def __init__(self):
        self.obj = None
        self.node_id_list = []
        self.cost_of_distance = None
        self.cost_of_time = None
        self.action_id = None
        self.route_list = []
        self.timetable_list = []


# 节点类
class Node:
    def __init__(self):
        self.id = 0
        self.x_coord = 0
        self.y_coord = 0
        self.demand = 0
        self.depot_capacity = 0
        self.start_time = 0
        self.end_time = 1440
        self.service_time = 0

    def __str__(self):
        return "id:" + str(self.id) + ", x:" + str(self.x_coord) + ", y:" + str(self.y_coord) + ", demand:" + str(
            self.demand) + ", depot_capacity:" + str(self.depot_capacity) + ", start_time:" + str(
            self.start_time) + ", end_time:" + str(
            self.end_time) + ", service_time:" + str(self.service_time)


# 模型类
class Model:
    def __init__(self):
        self.best_sol = None
        self.demand_dict = {}
        self.depot_dict = {}
        self.depot_id_list = []
        self.demand_id_list = []
        self.distance_matrix = {}
        self.time_matrix = {}
        self.number_of_demands = 0
        self.vehicle_cap = 0
        self.vehicle_speed = 500
        self.rand_d_max = 0.4
        self.rand_d_min = 0.1
        self.worst_d_max = 5
        self.worst_d_min = 20
        self.regret_n = 5
        self.r1 = 30
        self.r2 = 18
        self.r3 = 12
        self.rho = 0.6
        self.d_weight = np.ones(2) * 10
        self.d_select = np.zeros(2)
        self.d_score = np.zeros(2)
        self.d_history_select = np.zeros(2)
        self.d_history_score = np.zeros(2)
        self.r_weight = np.ones(3) * 10
        self.r_select = np.zeros(3)
        self.r_score = np.zeros(3)
        self.r_history_select = np.zeros(3)
        self.r_history_score = np.zeros(3)
        self.opt_type = 1
        self.demand_list_N = []


def readFromDict(demands, depots, model):
    for demand in demands:
        node = Node()
        node.id = demand['service_id']
        node.x_coord = demand['x_coord']
        node.y_coord = demand['y_coord']
        node.demand = demand['demand']
        node.start_time = demand['start_time']
        node.end_time = demand['end_time']
        node.service_time = demand['service_time']
        model.demand_dict[node.id] = node
        model.demand_id_list.append(node.id)
    for depot in depots:
        node = Node()
        node.id = depot['deport_id']
        node.x_coord = depot['x_coord']
        node.y_coord = depot['y_coord']
        node.depot_capacity = depot['capacity']
        node.start_time = depot['start_time']
        node.end_time = depot['end_time']
        model.depot_dict[node.id] = node
        model.depot_id_list.append(node.id)



# 计算距离时间矩阵
def calDistanceTimeMatrix(model):
    for i in range(len(model.demand_id_list)):
        from_node_id = model.demand_list_N[i].node_id
        from_node_chaxun = model.demand_id_list[i]
        for j in range(i + 1 , len(model.demand_id_list)):
            to_node_id = model.demand_list_N[j].node_id
            to_node_chaxun = model.demand_id_list[j]
            dist = dijkstra(graph_dict, from_node_id, to_node_id, 2)
            model.distance_matrix[from_node_chaxun, to_node_chaxun] = dist
            model.distance_matrix[to_node_chaxun, from_node_chaxun] = dist
            model.time_matrix[from_node_chaxun, to_node_chaxun] = math.ceil(dist / model.vehicle_speed)
            model.time_matrix[to_node_chaxun, from_node_chaxun] = math.ceil(dist / model.vehicle_speed)
        for _, depot in model.depot_dict.items():
            dist = dijkstra(graph_dict, from_node_id, depot.id, 2)
            # dist = math.sqrt((model.demand_dict[from_node_id].x_coord - depot.x_coord) ** 2
            #                  + (model.demand_dict[from_node_id].y_coord - depot.y_coord) ** 2)
            model.distance_matrix[from_node_chaxun, depot.id] = dist
            model.distance_matrix[depot.id, from_node_chaxun] = dist
            model.time_matrix[from_node_chaxun, depot.id] = math.ceil(dist / model.vehicle_speed)
            model.time_matrix[depot.id, from_node_chaxun] = math.ceil(dist / model.vehicle_speed)


def selectDepot(route, depot_dict, model):
    min_in_out_distance = float('inf')
    index = None
    for _, depot in depot_dict.items():
        if depot.depot_capacity > 0:
            in_out_distance = model.distance_matrix[depot.id, route[0]] + model.distance_matrix[route[-1], depot.id]
            if in_out_distance < min_in_out_distance:
                index = depot.id
                min_in_out_distance = in_out_distance
    if index is None:
        print("there is no vehicle to dispatch")
        sys.exit(0)
    route.insert(0, index)
    route.append(index)
    depot_dict[index].depot_capacity = depot_dict[index].depot_capacity - 1
    return route, depot_dict


# @jit(parallel=True, fastmath=True, cache=True)
def calTravelCost(route_list, time_matrix, demand_dict, distance_matrix):
    timetable_list = []
    cost_of_distance = 0
    cost_of_time = 0
    for route in route_list:
        timetable = []
        for i in range(len(route)):
            if i == 0:
                depot_id = route[i]
                next_node_id = route[i + 1]
                travel_time = time_matrix[depot_id, next_node_id]
                departure = max(0, demand_dict[next_node_id].start_time - travel_time)
                timetable.append((departure, departure))
            elif 1 <= i <= len(route) - 2:
                last_node_id = route[i - 1]
                current_node_id = route[i]
                current_node = demand_dict[current_node_id]
                travel_time = time_matrix[last_node_id, current_node_id]
                arrival = max(timetable[-1][1] + travel_time, current_node.start_time)
                departure = arrival + current_node.service_time
                timetable.append((arrival, departure))
                cost_of_distance += distance_matrix[last_node_id, current_node_id]
                cost_of_time += time_matrix[last_node_id, current_node_id] + current_node.service_time + max(
                    current_node.start_time - timetable[-1][1] - travel_time, 0)
            else:
                last_node_id = route[i - 1]
                depot_id = route[i]
                travel_time = time_matrix[last_node_id, depot_id]
                departure = timetable[-1][1] + travel_time
                timetable.append((departure, departure))
                cost_of_distance += distance_matrix[last_node_id, depot_id]
                cost_of_time += time_matrix[last_node_id, depot_id]
        timetable_list.append(timetable)
        # print(timetable_list)
        # exit()
    return timetable_list, cost_of_time, cost_of_distance


def extractRoutes(node_id_list, Pred, model):
    depot_dict = copy.deepcopy(model.depot_dict)
    route_list = []
    route = []
    label = Pred[node_id_list[0]]
    for node_id in node_id_list:
        if Pred[node_id] == label:
            route.append(node_id)
        else:
            route, depot_dict = selectDepot(route, depot_dict, model)
            route_list.append(route)
            route = [node_id]
            label = Pred[node_id]
    route, depot_dict = selectDepot(route, depot_dict, model)
    route_list.append(route)
    return route_list


def splitRoutes(node_id_list, model):
    depot = model.depot_id_list[0]
    V = {id: float('inf') for id in model.demand_id_list}#V好像存储的是cost
    V[depot] = 0
    Pred = {id: depot for id in model.demand_id_list}#pred好像存储的是路径
    for i in range(len(node_id_list)):
        n_1 = node_id_list[i]
        demand = 0
        departure = 0
        j = i
        cost = 0
        while True:
            n_2 = node_id_list[j]
            demand = demand + model.demand_dict[n_2].demand
            if n_1 == n_2:
                arrival = max(model.demand_dict[n_2].start_time,
                              model.depot_dict[depot].start_time + model.time_matrix[depot, n_2])#开始服务时间
                departure = arrival + model.demand_dict[n_2].service_time#离开时间
                if model.opt_type == 0:#计算成本
                    cost = model.distance_matrix[depot, n_2] * 2
                else:
                    cost = model.time_matrix[depot, n_2] * 2
            else:#如果不是一个节点
                n_3 = node_id_list[j - 1]
                arrival = max(departure + model.time_matrix[n_3, n_2], model.demand_dict[n_2].start_time)
                departure = arrival + model.demand_dict[n_2].service_time
                if model.opt_type == 0:
                    cost = cost - model.distance_matrix[n_3, depot] + model.distance_matrix[n_3, n_2] + \
                           model.distance_matrix[n_2, depot]
                else:
                    cost = cost - model.time_matrix[n_3, depot] + model.time_matrix[n_3, n_2] \
                           + max(model.demand_dict[n_2].start_time - arrival, 0) + model.time_matrix[n_2, depot]
            if demand <= model.vehicle_cap and departure <= model.demand_dict[n_2].end_time:
                if departure + model.time_matrix[n_2, depot] <= model.depot_dict[depot].end_time:
                    n_4 = node_id_list[i - 1] if i - 1 >= 0 else depot
                    if V[n_4] + cost <= V[n_2]:
                        V[n_2] = V[n_4] + cost
                        Pred[n_2] = i - 1
                    j = j + 1
            else:
                break
            if j == len(node_id_list):
                break
    route_list = extractRoutes(node_id_list, Pred, model)
    return len(route_list), route_list


def calObj(sol, model):
    node_id_list = copy.deepcopy(sol.node_id_list)
    num_vehicle, sol.route_list = splitRoutes(node_id_list, model)
    # travel cost
    sol.timetable_list, sol.cost_of_time, sol.cost_of_distance = calTravelCost(sol.route_list, model.time_matrix,
                                                                               model.demand_dict, model.distance_matrix)
    if model.opt_type == 0:
        sol.obj = sol.cost_of_distance
    else:
        sol.obj = sol.cost_of_time


# 生成初始解
def genInitialSol(node_id_list):
    node_id_list = copy.deepcopy(node_id_list)
    random.seed(0)
    random.shuffle(node_id_list)
    return node_id_list


# 定义destory算子
# @njit(parallel=True)
def createRandomDestory(rand_d_min, rand_d_max, demand_id_list):
    d = random.uniform(rand_d_min, rand_d_max)
    remove_list = random.sample(range(len(demand_id_list)), int(d * len(demand_id_list)))
    return remove_list


def createWorseDestory(model, sol):
    deta_f = []
    for node_id in sol.node_id_list:
        sol_ = copy.deepcopy(sol)
        sol_.node_id_list.remove(node_id)
        calObj(sol_, model)
        deta_f.append(sol.obj - sol_.obj)
    sorted_id = sorted(range(len(deta_f)), key=lambda k: deta_f[k], reverse=True)
    d = random.randint(model.worst_d_min, model.worst_d_max)
    remove_list = sorted_id[:d]
    return remove_list


# 定义repair算子
def createRandomRepair(remove_list, model, sol):
    unassigned_nodes_id = []
    assigned_nodes_id = []
    # remove node from current solution
    for i in range(len(model.demand_id_list)):
        if i in remove_list:
            unassigned_nodes_id.append(sol.node_id_list[i])
        else:
            assigned_nodes_id.append(sol.node_id_list[i])
    # insert
    for node_id in unassigned_nodes_id:
        index = random.randint(0, len(assigned_nodes_id) - 1)
        assigned_nodes_id.insert(index, node_id)
    new_sol = Sol()
    new_sol.node_id_list = copy.deepcopy(assigned_nodes_id)
    calObj(new_sol, model)
    return new_sol


def findGreedyInsert(unassigned_nodes_id, assigned_nodes_id, model):
    best_insert_node_id = None
    best_insert_index = None
    best_insert_cost = float('inf')
    sol_1 = Sol()
    sol_1.node_id_list = assigned_nodes_id
    calObj(sol_1, model)
    for node_id in unassigned_nodes_id:
        for i in range(len(assigned_nodes_id)):
            sol_2 = Sol()
            sol_2.node_id_list = copy.deepcopy(assigned_nodes_id)
            sol_2.node_id_list.insert(i, node_id)
            calObj(sol_2, model)
            deta_f = sol_2.obj - sol_1.obj
            if deta_f < best_insert_cost:
                best_insert_index = i
                best_insert_node_id = node_id
                best_insert_cost = deta_f
    return best_insert_node_id, best_insert_index


def createGreedyRepair(remove_list, model, sol):
    unassigned_nodes_id = []
    assigned_nodes_id = []
    # remove node from current solution
    for i in range(len(model.demand_id_list)):
        if i in remove_list:
            unassigned_nodes_id.append(sol.node_id_list[i])
        else:
            assigned_nodes_id.append(sol.node_id_list[i])
    # insert
    while len(unassigned_nodes_id) > 0:
        insert_node_id, insert_index = findGreedyInsert(unassigned_nodes_id, assigned_nodes_id, model)
        assigned_nodes_id.insert(insert_index, insert_node_id)
        unassigned_nodes_id.remove(insert_node_id)
    new_sol = Sol()
    new_sol.node_id_list = copy.deepcopy(assigned_nodes_id)
    calObj(new_sol, model)
    return new_sol


def findRegretInsert(unassigned_nodes_id, assigned_nodes_id, model):
    opt_insert_node_id = None
    opt_insert_index = None
    opt_insert_cost = -float('inf')
    sol_ = Sol()
    for node_id in unassigned_nodes_id:
        n_insert_cost = np.zeros((len(assigned_nodes_id), 3))
        for i in range(len(assigned_nodes_id)):
            sol_.node_id_list = copy.deepcopy(assigned_nodes_id)
            sol_.node_id_list.insert(i, node_id)
            calObj(sol_, model)
            n_insert_cost[i, 0] = node_id
            n_insert_cost[i, 1] = i
            n_insert_cost[i, 2] = sol_.obj
        n_insert_cost = n_insert_cost[n_insert_cost[:, 2].argsort()]
        deta_f = 0
        for i in range(1, model.regret_n):
            deta_f = deta_f + n_insert_cost[i, 2] - n_insert_cost[0, 2]
        if deta_f > opt_insert_cost:
            opt_insert_node_id = int(n_insert_cost[0, 0])
            opt_insert_index = int(n_insert_cost[0, 1])
            opt_insert_cost = deta_f
    return opt_insert_node_id, opt_insert_index


def createRegretRepair(remove_list, model, sol):
    unassigned_nodes_id = []
    assigned_nodes_id = []
    # remove node from current solution
    for i in range(len(model.demand_id_list)):
        if i in remove_list:
            unassigned_nodes_id.append(sol.node_id_list[i])
        else:
            assigned_nodes_id.append(sol.node_id_list[i])
    # insert
    while len(unassigned_nodes_id) > 0:
        insert_node_id, insert_index = findRegretInsert(unassigned_nodes_id, assigned_nodes_id, model)
        assigned_nodes_id.insert(insert_index, insert_node_id)
        unassigned_nodes_id.remove(insert_node_id)
    new_sol = Sol()
    new_sol.node_id_list = copy.deepcopy(assigned_nodes_id)
    calObj(new_sol, model)
    return new_sol


@njit(parallel=True, fastmath=True)
def selectDestoryRepair(d_weight, r_weight):
    d_cumsumprob = (d_weight / sum(d_weight)).cumsum()
    d_cumsumprob -= np.random.rand()
    destory_id = list(d_cumsumprob > 0).index(True)

    r_cumsumprob = (r_weight / sum(r_weight)).cumsum()
    r_cumsumprob -= np.random.rand()
    repair_id = list(r_cumsumprob > 0).index(True)
    return destory_id, repair_id


def doDestory(destory_id, model, sol):
    if destory_id == 0:
        reomve_list = createRandomDestory(model.rand_d_min, model.rand_d_max, model.demand_id_list)
    else:
        reomve_list = createWorseDestory(model, sol)
    return reomve_list


def doRepair(repair_id, reomve_list, model, sol):
    if repair_id == 0:
        new_sol = createRandomRepair(reomve_list, model, sol)
    elif repair_id == 1:
        new_sol = createGreedyRepair(reomve_list, model, sol)
    else:
        new_sol = createRegretRepair(reomve_list, model, sol)
    return new_sol


def resetScore(model):
    model.d_select = np.zeros(2)
    model.d_score = np.zeros(2)

    model.r_select = np.zeros(3)
    model.r_score = np.zeros(3)


def updateWeight(model):
    for i in range(model.d_weight.shape[0]):
        if model.d_select[i] > 0:
            model.d_weight[i] = model.d_weight[i] * (1 - model.rho) + model.rho * model.d_score[i] / model.d_select[i]
        else:
            model.d_weight[i] = model.d_weight[i] * (1 - model.rho)
    for i in range(model.r_weight.shape[0]):
        if model.r_select[i] > 0:
            model.r_weight[i] = model.r_weight[i] * (1 - model.rho) + model.rho * model.r_score[i] / model.r_select[i]
        else:
            model.r_weight[i] = model.r_weight[i] * (1 - model.rho)
    model.d_history_select = model.d_history_select + model.d_select
    model.d_history_score = model.d_history_score + model.d_score
    model.r_history_select = model.r_history_select + model.r_select
    model.r_history_score = model.r_history_score + model.r_score


def plotObj(obj_list):
    plt.rcParams['font.sans-serif'] = ['SimHei']  # show chinese
    plt.rcParams['axes.unicode_minus'] = False  # Show minus sign
    plt.plot(np.arange(1, len(obj_list) + 1), obj_list)
    plt.xlabel('Iterations')
    plt.ylabel('Obj Value')
    plt.grid()
    plt.xlim(1, len(obj_list) + 1)
    #plt.show()


def outPut(model):
    work = xlsxwriter.Workbook('algorithm/result.xlsx')
    worksheet = work.add_worksheet()
    worksheet.write(0, 0, 'cost_of_time')
    worksheet.write(0, 1, 'cost_of_distance')
    worksheet.write(0, 2, 'opt_type')
    worksheet.write(0, 3, 'obj')
    worksheet.write(1, 0, model.best_sol.cost_of_time)
    worksheet.write(1, 1, model.best_sol.cost_of_distance)
    worksheet.write(1, 2, model.opt_type)
    worksheet.write(1, 3, model.best_sol.obj)
    worksheet.write(2, 0, 'vehicleID')
    worksheet.write(2, 1, 'route')
    worksheet.write(2, 2, 'timetable')
    for row, route in enumerate(model.best_sol.route_list):
        worksheet.write(row + 3, 0, 'v' + str(row + 1))
        r = [str(i) for i in route]
        worksheet.write(row + 3, 1, '-'.join(r))
        r = [str(i) for i in model.best_sol.timetable_list[row]]
        worksheet.write(row + 3, 2, '-'.join(r))
    work.close()


def plotRoutes(model):
    for route in model.best_sol.route_list:
        x_coord = [model.depot_dict[route[0]].x_coord]
        y_coord = [model.depot_dict[route[0]].y_coord]
        for node_id in route[1:-1]:
            x_coord.append(model.demand_dict[node_id].x_coord)
            y_coord.append(model.demand_dict[node_id].y_coord)
        x_coord.append(model.depot_dict[route[-1]].x_coord)
        y_coord.append(model.depot_dict[route[-1]].y_coord)
        plt.grid()
        if route[0] == 'd1':
            plt.plot(x_coord, y_coord, marker='o', color='black', linewidth=0.5, markersize=5)
        elif route[0] == 'd2':
            plt.plot(x_coord, y_coord, marker='o', color='orange', linewidth=0.5, markersize=5)
        else:
            plt.plot(x_coord, y_coord, marker='o', color='b', linewidth=0.5, markersize=5)
    plt.xlabel('x_coord')
    plt.ylabel('y_coord')
    #plt.show()


def alns(demands, depots, rand_d_max, rand_d_min, worst_d_min, worst_d_max, regret_n, r1, r2, r3, rho, phi,
         epochs, pu, v_cap,
         v_speed, opt_type, demand_list_N
        ):
    """
    :param demand_file: demand file path
    :param depot_file: depot file path
    :param rand_d_max: max degree of random destruction
    :param rand_d_min: min degree of random destruction
    :param worst_d_max: max degree of worst destruction
    :param worst_d_min: min degree of worst destruction
    :param regret_n:  n next cheapest insertions
    :param r1: score if the new solution is the best one found so far.
    :param r2: score if the new solution improves the current solution.
    :param r3: score if the new solution does not improve the current solution, but is accepted.
    :param rho: reaction factor of action weight
    :param phi: the reduction factor of threshold
    :param epochs: Iterations
    :param pu: the frequency of weight adjustment
    :param v_cap: Vehicle capacity
    :param v_speed Vehicle free speed
    :param opt_type: Optimization type:0:Minimize the number of vehicles,1:Minimize travel distance
    :return:
    """
    pd.DataFrame(demands).to_csv('algorithm/demand.csv')
    pd.DataFrame(depots).to_csv('algorithm/depot.csv')
    model = Model()
    model.rand_d_max = rand_d_max
    model.rand_d_min = rand_d_min
    model.worst_d_min = worst_d_min
    model.worst_d_max = worst_d_max
    model.regret_n = regret_n
    model.r1 = r1
    model.r2 = r2
    model.r3 = r3
    model.rho = rho
    model.vehicle_cap = v_cap
    model.opt_type = opt_type
    model.vehicle_speed = v_speed
    # readCSVFile(demand_file, depot_file, model)
    readFromDict(demands, depots, model)
    model.demand_list_N = demand_list_N
    calDistanceTimeMatrix(model)
    history_best_obj = []
    sol = Sol()
    sol.node_id_list = genInitialSol(model.demand_id_list)
    calObj(sol, model)
    model.best_sol = copy.deepcopy(sol)
    history_best_obj.append(sol.obj)
    for ep in range(epochs):
        T = sol.obj * 0.2
        resetScore(model)
        for k in range(pu):
            destory_id, repair_id = selectDestoryRepair(model.d_weight, model.r_weight)
            model.d_select[destory_id] += 1
            model.r_select[repair_id] += 1
            reomve_list = doDestory(destory_id, model, sol)
            new_sol = doRepair(repair_id, reomve_list, model, sol)
            if new_sol.obj < sol.obj:
                sol = copy.deepcopy(new_sol)
                if new_sol.obj < model.best_sol.obj:
                    model.best_sol = copy.deepcopy(new_sol)
                    model.d_score[destory_id] += model.r1
                    model.r_score[repair_id] += model.r1
                else:
                    model.d_score[destory_id] += model.r2
                    model.r_score[repair_id] += model.r2
            elif new_sol.obj - sol.obj < T:
                sol = copy.deepcopy(new_sol)
                model.d_score[destory_id] += model.r3
                model.r_score[repair_id] += model.r3
            T = T * phi
            print("%s/%s:%s/%s， best obj: %s" % (ep, epochs, k, pu, model.best_sol.obj))
            history_best_obj.append(model.best_sol.obj)
        updateWeight(model)

    plotObj(history_best_obj)
    plotRoutes(model)
    outPut(model)
    print('Demand_dict', model.demand_dict)
    print('Depot_dict', model.depot_dict)
    print('Demand_id_list', model.demand_id_list)
    print("random destory weight is {:.3f}\tselect is {}\tscore is {:.3f}".format(model.d_weight[0],
                                                                                  model.d_history_select[0],
                                                                                  model.d_history_score[0]))
    print("worse destory weight is {:.3f}\tselect is {}\tscore is {:.3f} ".format(model.d_weight[1],
                                                                                  model.d_history_select[1],
                                                                                  model.d_history_score[1]))
    print("random repair weight is {:.3f}\tselect is {}\tscore is {:.3f}".format(model.r_weight[0],
                                                                                 model.r_history_select[0],
                                                                                 model.r_history_score[0]))
    print("greedy repair weight is {:.3f}\tselect is {}\tscore is {:.3f}".format(model.r_weight[1],
                                                                                 model.r_history_select[1],
                                                                                 model.r_history_score[1]))
    print("regret repair weight is {:.3f}\tselect is {}\tscore is {:.3f}".format(model.r_weight[2],
                                                                                 model.r_history_select[2],
                                                                                 model.r_history_score[2]))
    return model.best_sol.cost_of_time, model.best_sol.cost_of_distance, model.opt_type, model.best_sol.obj, \
        model.best_sol.route_list, model.best_sol.timetable_list


# if __name__ == '__main__':
#     demand_file = 'demand.csv'
#     depot_file = 'depot.csv'
#     run(demand_file=demand_file, depot_file=depot_file, rand_d_max=0.4, rand_d_min=0.1,
#         worst_d_min=5, worst_d_max=20, regret_n=5, r1=30, r2=20, r3=10, rho=0.5,
#         phi=0.9, epochs=1, pu=5, v_cap=80, v_speed=0.5, opt_type=1)

print("The time used to execute this is given below")
end = time.time()

print(end - start)
