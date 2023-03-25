from django.db import models
from django.contrib.auth.models import User
from algorithm.dicts import service_type_tuples, service_vehicle_tuples


# Create your models here.

class Flight(models.Model):
    """
    Flight model
    """
    flight_id = models.CharField(max_length=32, primary_key=True, verbose_name="航班号")
    aircraft_id = models.CharField(max_length=32, verbose_name="机号")
    aircraft_type = models.CharField(max_length=16, verbose_name="机型", blank=True, null=True)
    seats_num = models.SmallIntegerField(verbose_name="座位数", blank=True, null=True)
    passenger_num = models.SmallIntegerField(verbose_name="实际载客数", blank=True, null=True)
    flight_type = models.BooleanField(verbose_name="航班类型(国际/国内)", blank=True, null=True)
    parking_id = models.SmallIntegerField(verbose_name="机位号")
    on_block_time = models.IntegerField(verbose_name="上轮挡时间")
    off_block_time = models.IntegerField(verbose_name="撤轮挡时间")
    is_served = models.BooleanField(verbose_name="是否服务", blank=True, null=True, default=False)

    def __str__(self):
        return '<%s>-<%s>-<%s>-<%s>' % (self.flight_id, self.aircraft_id, self.on_block_time, self.off_block_time)

    class Meta:
        verbose_name = "航班信息表"
        verbose_name_plural = "航班信息表"
        ordering = ['-on_block_time']


class Service(models.Model):
    """
    Service model
    """
    #service_id = models.CharField(max_length=32, primary_key=True, verbose_name="服务号")
    id = models.CharField(max_length=32, primary_key=True, verbose_name="服务号")
    flight = models.ForeignKey('Flight', related_name='Service_flight', on_delete=models.SET_NULL, null=True,
                               blank=True,
                               verbose_name="航班号")
    earliest_start_time = models.IntegerField(verbose_name="最早开始时间")
    latest_start_time = models.IntegerField(verbose_name="最晚开始时间")
    minimum_duration = models.IntegerField(verbose_name="最短持续时间")
    maximum_duration = models.IntegerField(verbose_name="最长持续时间")
    earliest_end_time = models.IntegerField(verbose_name="最早结束时间")
    latest_end_time = models.IntegerField(verbose_name="最晚结束时间")
    service_type = models.CharField(choices=service_type_tuples, max_length=16, verbose_name="服务类型")
    service_vehicle_type = models.CharField(choices=service_vehicle_tuples, max_length=16,
                                            verbose_name="服务需求车辆类型")
    service_vehicle_num = models.SmallIntegerField(verbose_name="服务需求车辆数量")
    service_delay_time = models.IntegerField(verbose_name="服务最终延误时间", null=True, blank=True)
    service_start_node = models.ForeignKey('RoadNodes', related_name='Service_service_start_node', null=True,
                                           blank=True,
                                           on_delete=models.SET_NULL, verbose_name="服务起始节点")
    service_end_node = models.ForeignKey('RoadNodes', related_name='Service_service_end_node', null=True, blank=True,
                                         on_delete=models.SET_NULL,
                                         verbose_name="服务结束节点")
    pre_order_service = models.ForeignKey('self', related_name='Service_pre_order_service',
                                          on_delete=models.SET_NULL, null=True, blank=True,
                                          verbose_name="前序服务")
    post_order_service = models.ForeignKey('self', related_name='Service_post_order_service',
                                           on_delete=models.SET_NULL, null=True, blank=True,
                                           verbose_name="后序服务")
    pre_order_maximum_interval = models.SmallIntegerField(verbose_name="前序最大时间间隔", null=True, blank=True)
    is_scheduled = models.BooleanField(verbose_name="是否已安排车辆", blank=True, null=True, default=False)

    def __str__(self):
        return '<%s>-<%s>-<%d>-<%s>-<%s>' % (
            self.id, self.service_vehicle_type, self.service_vehicle_num, self.service_start_node,
            self.service_end_node)

    class Meta:
        verbose_name = "服务信息表"
        verbose_name_plural = "服务信息表"
        ordering = ['id']


class Vehicle(models.Model):
    """
    Vehicle model
    """
    vehicle_id = models.CharField(max_length=32, primary_key=True, verbose_name="车辆号")
    vehicle_type = models.CharField(max_length=16, verbose_name="车辆类型")
    vehicle_energy = models.CharField(max_length=16, verbose_name="车辆能源类型")
    vehicle_full_energy_mileage = models.CharField(max_length=16, verbose_name="车辆满能源里程")  # 最大行驶距离
    vehicle_current_position_x = models.FloatField(verbose_name="车辆当前x坐标")
    vehicle_current_position_y = models.FloatField(verbose_name="车辆当前y坐标")

    vehicle_service_list = models.ManyToManyField(Service, through='VehicleService',
                                                  through_fields=('vehicle_id', 'service_id'))
    vehicle_path_list = models.ManyToManyField('RoadNodes', through='VehiclePath',
                                               through_fields=('vehicle_id', 'node_id'))
    vehicle_status = models.SmallIntegerField(verbose_name="车辆状态", default=1)

    def __str__(self):
        return '<%s>-<%s>' % (self.vehicle_id, self.vehicle_type)

    class Meta:
        verbose_name = "车辆信息表"
        verbose_name_plural = "车辆信息表"
        ordering = ['vehicle_id']


class VehicleService(models.Model):
    """
    VehicleService model
    """
    vehicle = models.ForeignKey('Vehicle', related_name='VehicleService_vehicle', on_delete=models.CASCADE,
                                verbose_name="车辆号")
    service = models.ForeignKey('Service', related_name='VehicleService_service', on_delete=models.CASCADE,
                                verbose_name="服务号")

    def __str__(self):
        return '<%s>-<%s>' % (self.vehicle_id, self.service_id)

    class Meta:
        verbose_name = "车辆服务信息表"
        verbose_name_plural = "车辆服务信息表"
        ordering = ['vehicle_id', 'service_id']


class VehiclePath(models.Model):
    """
    VehiclePath model
    """
    vehicle = models.ForeignKey('Vehicle', related_name='VehiclePath_vehicle', on_delete=models.CASCADE,
                                verbose_name="车辆号")
    service = models.ForeignKey('Service', related_name='VehiclePath_service', on_delete=models.SET_NULL, null=True,
                                blank=True, verbose_name="服务号")
    node = models.ForeignKey('RoadNodes', related_name='VehiclePath_node', on_delete=models.SET_NULL, null=True,
                             blank=True,
                             verbose_name="路径节点号")
    node_arrival_time = models.IntegerField(verbose_name="路径节点到达时间", blank=True, null=True)
    node_departure_time = models.IntegerField(verbose_name="路径节点离开时间", blank=True, null=True)
    node_dwell_time = models.IntegerField(verbose_name="路径节点停留时间", blank=True, null=True)
    node_delay_time = models.IntegerField(verbose_name="路径节点延误时间", blank=True, null=True)

    def __str__(self):
        return '<%s>-<%s>-<%s>' % (self.vehicle_id, self.node_id, self.node_arrival_time)

    class Meta:
        verbose_name = "车辆路径表"
        verbose_name_plural = "车辆路径表"
        ordering = ['vehicle_id']


class RoadNodes(models.Model):
    """
    RoadNodes model
    """
    node_id = models.CharField(max_length=32, primary_key=True, verbose_name="道路节点号")
    node_position_x = models.FloatField(verbose_name="x坐标", default=0)
    node_position_y = models.FloatField(verbose_name="y坐标", default=0)
    node_type = models.CharField(max_length=8, verbose_name="道路节点类型", null=True)
    node_function = models.IntegerField(verbose_name="道路节点功能", null=True)  # -1车库 / 0 / n机位号
    node_capacity = models.SmallIntegerField(verbose_name="节点容量", null=True, blank=True)
    node_availability = models.BooleanField(max_length=8, verbose_name="道路节点可用状态", default=True)  # 可用/不可用
    node_adjacent_list = models.ManyToManyField('self', through='RoadSections',
                                                through_fields=('section_start_node', 'section_end_node'))

    def __str__(self):
        return '<%s>-<%s>-<%s>' % (self.node_id, self.node_position_x, self.node_position_y)

    class Meta:
        verbose_name = "道路节点信息表"
        verbose_name_plural = "道路节点信息表"
        ordering = ['node_id']


class RoadSections(models.Model):
    """
    RoadSections model
    """
    section_id = models.CharField(max_length=32, primary_key=True, verbose_name="路段号")
    section_type = models.CharField(max_length=8, verbose_name="路段类型", blank=True, null=True)
    section_availability = models.BooleanField(verbose_name="路段可用状态", default=True)
    section_speed_limit = models.FloatField(max_length=8, verbose_name="路段限速", blank=True, null=True)
    section_lanes_num = models.SmallIntegerField(verbose_name="路段车道数", blank=True, null=True)
    section_start_node = models.ForeignKey('RoadNodes', related_name='RoadSections_section_start_node',
                                           on_delete=models.CASCADE, verbose_name="路段开始节点")
    section_end_node = models.ForeignKey('RoadNodes', related_name='RoadSections_section_end_node',
                                         on_delete=models.CASCADE, verbose_name="路段结束节点")
    section_length = models.FloatField(max_length=8, verbose_name="路段长度", default=0)
    section_is_one_way = models.BooleanField(verbose_name="是否是单向路段", blank=True, null=True, default=False)

    def __str__(self):
        return '<%s>-<%s>-<%s>-<%s>' % (
            self.section_id, self.section_type, self.section_start_node, self.section_end_node)

    class Meta:
        verbose_name = "路段信息表"
        verbose_name_plural = "路段信息表"
        ordering = ['section_id']
