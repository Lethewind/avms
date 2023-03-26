import heapq


# 输入示例：
# 定义图的字典表示
# graph = {
#     'A': {'B': 5, 'C': 2},
#     'B': {'D': 4, 'E': 2},
#     'C': {'B': 8, 'E': 7},
#     'D': {'E': 6, 'F': 3},
#     'E': {'F': 1},
#     'F': {}
# }
#
# # 调用函数获取最短距离和节点列表
# dist, path = dijkstra(graph, 'A', 'F')
#
# # 输出结果
# print('最短距离:', dist)
# print('节点列表:', path)
def dijkstra(graph, start, end, opt):
    # 初始化距离和前驱字典
    dist = {node: float('inf') for node in graph}
    prev = {node: None for node in graph}
    dist[start] = 0

    # 使用优先队列实现Dijkstra算法
    heap = [(0, start)]
    while heap:
        (d, current) = heapq.heappop(heap)
        if current == end:
            break
        if d > dist[current]:
            continue
        for neighbor, weight in graph[current].items():
            distance = dist[current] + weight
            if distance < dist[neighbor]:
                dist[neighbor] = distance
                prev[neighbor] = current
                heapq.heappush(heap, (distance, neighbor))

    # 构造节点列表
    path = []
    node = end
    while node is not None:
        path.append(node)
        node = prev[node]
    path.reverse()

    # 返回最短距离和节点列表,1为两者都返回，2为只返回最短距离（用来计算距离矩阵）
    if opt == 1:
        return dist[end], path
    if opt == 2:
        return dist[end]
    if opt == 3:
        return path
