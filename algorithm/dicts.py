service_type_dict = {
    'QY': '牵引，牵引车',
    'XK': '下客，客梯车',
    'QJ': '清洁，清洁车',
    'JY': '加油，加油车',
    'PC': '配餐，配餐车',
    'SK': '上客，客梯车',
    'HY': '货运，行李牵引车',
    'TC': '推出，牵引车'
}

service_type_tuples = (('QY', '牵引，牵引车'),
                       ('XK', '下客，客梯车'),
                       ('QJ', '清洁，清洁车'),
                       ('JY', '加油，加油车'),
                       ('PC', '配餐，配餐车'),
                       ('SK', '上客，客梯车'),
                       ('HY', '货运，行李牵引车'),
                       ('TC', '推出，牵引车'))

service_vehicle_dict = {
    'QY': 'QY',  # '牵引车',
    'XK': 'KT',  # '客梯车',
    'QJ': 'QJ',  # '清洁车',
    'JY': 'JY',  # '加油车',
    'PC': 'CS',  # '餐食车',
    'SK': 'KT',  # '客梯车',
    'HY': 'XL',  # '行礼牵引车',
    'TC': 'QY'  # '牵引车'
}

service_vehicle_demand_dict = {
    'QY': 1,
    'XK': 1,
    'QJ': 1,
    'JY': 1,
    'PC': 1,
    'SK': 1,
    'HY': 1,
    'TC': 1
}

service_vehicle_tuples = (('QY', 'QY'),
                          ('XK', 'KT'),
                          ('QJ', 'QJ'),
                          ('JY', 'JY'),
                          ('PC', 'CS'),
                          ('SK', 'KT'),
                          ('HY', 'XL'),
                          ('TC', 'QY'))

service_minimum_duration_dict = {
    'QY': 3,
    'XK': 10,
    'QJ': 10,
    'JY': 3,
    'PC': 4,
    'SK': 10,
    'HY': 30,
    'TC': 3
}

service_maximum_duration_dict = {
    'QY': 5,
    'XK': 15,
    'QJ': 15,
    'JY': 10,
    'PC': 7,
    'SK': 25,
    'HY': 40,
    'TC': 5
}

service_minimum_duration_dict_long = {
    'QY': 5,
    'XK': 15,
    'QJ': 20,
    'JY': 15,
    'PC': 15,
    'SK': 15,
    'HY': 40,
    'TC': 5
}

service_maximum_duration_dict_long = {
    'QY': 8,
    'XK': 20,
    'QJ': 25,
    'JY': 20,
    'PC': 30,
    'SK': 30,
    'HY': 50,
    'TC': 8
}
