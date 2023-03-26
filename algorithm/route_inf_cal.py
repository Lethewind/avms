from algorithm.min_dis import dijkstra


# 计算一辆车在每个路段节点的时间窗
# alns计算出来的到达时间应该是开始服务时间！

# graph: 路网 onepath_inf:一辆车的任务列表，onepath_window：一辆车的任务时间窗
# onepath_inf = [N38, N1, N2, N38]
# onepath_window = [[234,234], [245,256],....]
def cal_all_windows(graph, onepath_inf, onepath_window, road_dict):
    # 生成全部列表
    all_path_perv = []
    # print(onepath_inf)
    all_path_perv.append(onepath_inf[0])
    all_path_win = []
    all_path_win.append(onepath_window[0])
    for i in range(len(onepath_inf) - 1):
        from_node_id = onepath_inf[i]
        to_node_id = onepath_inf[i + 1]
        mid_path = dijkstra(graph, from_node_id, to_node_id, 3)
        departure_last = onepath_window[i][1]
        for j in range(len(mid_path) - 1):
            road_id = road_dict[mid_path[j]][mid_path[j + 1]].section_id
            road_length = road_dict[mid_path[j]][mid_path[j + 1]].section_length
            # all_path_perv.append(road_id)#添加路段字段
            all_path_perv.append(mid_path[j + 1])  # 添加中间路段的后序节点
            travel_time = road_length / 400  # 400为speed
            # all_path_win.append([departure_last, departure_last+travel_time])#路段！
            if j != len(mid_path) - 2:
                departure_last += travel_time
                all_path_win.append([departure_last, departure_last])  # 节点
            if j == len(mid_path) - 2:
                arrival_time_get = onepath_window[i + 1][0]
                arrival_time_cal = departure_last + travel_time  # 其实就是上面if的departure_last
                idle_time = arrival_time_get - arrival_time_cal
                all_path_win.append([arrival_time_cal, onepath_window[i + 1][1]])  # 真实的到达、离开时间
    return all_path_perv, all_path_win

# 查询一辆车的位置
# def time_to_location(vehicle_id, path_window, path, time):
# 遍历列表
# for i in path:
#     if path[0] == 'N':
#         if
#     if path[0] == 'R':
