def time_arrange_small(on_block_time, off_block_time):
    """
    :param on_block_time: 入轮挡时间
    :param off_block_time: 撤轮挡时间
    :return: 一个字典，键为服务类型，值返回一个数组[最早到达时间，最晚到达时间]
    """
    crossing = off_block_time - on_block_time
    sts_min = [3, 10, 10, 3, 4, 10, 30, 3]
    sts_max = [5, 15, 15, 10, 7, 25, 40, 5]
    stl_min = [5, 15, 20, 15, 15, 15, 40, 5]
    stl_max = [8, 20, 25, 20, 30, 30, 50, 8]

    e = []
    l = []
    if crossing <= 100:
        e.append([on_block_time - 10,  # qy
                  on_block_time + sts_min[0],  # xk
                  on_block_time + sts_min[0] + sts_min[4],  # qj
                  on_block_time + sts_min[0] + sts_min[2],  # yj
                  on_block_time + sts_min[0],  # pc
                  on_block_time + sts_min[0],  # sk
                  on_block_time + sts_min[0],  # hy
                  off_block_time - sts_max[7]  # tc
                  ])
        l.append([
            on_block_time,  # qy
            min(off_block_time - 30 - sts_max[3] - sts_max[1], on_block_time + sts_min[0] + 5),  # xk
            off_block_time - 30 - sts_max[2],  # qj
            off_block_time - 30 - sts_max[4],  # jy
            off_block_time - 30 - sts_max[2] - sts_max[4],  # pc
            off_block_time - 30,  # sk,撤轮挡前30分钟开始
            min(off_block_time - 5 - sts_max[6], on_block_time + sts_min[0] + 5),  # hy
            off_block_time - stl_max[7] + 10  # tc
        ])
    else:
        e.append([on_block_time - 10,  # qy
                  on_block_time + stl_min[0],  # xk
                  on_block_time + stl_min[0] + stl_min[4],  # qj
                  on_block_time + stl_min[0] + stl_min[2],  # yj
                  on_block_time + stl_min[0],  # pc
                  on_block_time + stl_min[0],  # sk
                  on_block_time + stl_min[0],  # hy
                  off_block_time - stl_max[7]  # tc
                  ])
        l.append([
            on_block_time,  # qy
            min(off_block_time - 30 - stl_max[3] - stl_max[1], on_block_time + stl_min[0] + 5),
            # xk
            off_block_time - 30 - stl_max[2],  # qj
            off_block_time - 30 - stl_max[3],  # yj
            off_block_time - 30 - stl_max[2] - stl_max[4],  # pc
            off_block_time - 30,  # sk,撤轮挡前30分钟开始
            min(off_block_time - 5 - stl_max[6], on_block_time + stl_min[0] + 5),  # hy
            off_block_time - stl_max[7] + 10  # tc
        ])
    service_type = ['QY', 'XK', 'QJ', 'JY', 'PC', 'SK', 'HY', 'TC']
    e = [[int(num) for num in row] for row in e]
    l = [[int(num) for num in row] for row in l]
    e = e[0]
    l = l[0]
    result = {}
    for i in range(len(service_type)):
        result[service_type[i]] = [e[i], l[i]]
    return result


result = time_arrange_small(535, 595)
# 输出：一个字典，键为服务类型，值返回一个数组[最早到达时间，最晚到达时间]

# 服务类型：
# service_type_dict = {
#     'QY': '牵引，牵引车',
#     'XK': '下客，客梯车',
#     'QJ': '清洁，清洁车',
#     'JY': '加油，加油车',
#     'PC': '配餐，配餐车',
#     'SK': '上客，客梯车',
#     'HY': '货运，行李牵引车',
#     'TC': '推出，牵引车'
# }

# 测试
# result = time_arrange_small(535, 595)
# 结果：{'QY': [525, 535], 'XK': [538, 540], 'QJ': [542, 550], 'JY': [548, 558], 'PC': [538, 543], 'SK': [538, 565], 'HY': [538, 543], 'TC': [590, 597]}
