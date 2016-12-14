# encoding: utf-8
"""
Represents a connection to the SLB service.
"""

import warnings

import six
import time
import json

from footmark.connection import ACSQueryConnection
from footmark.slb.regioninfo import RegionInfo
from footmark.slb.securitygroup import SecurityGroup
from footmark.exception import SLBResponseError

class SLBConnection(ACSQueryConnection):
    SDKVersion = '2014-05-15'
    DefaultRegionId = 'cn-hangzhou'
    DefaultRegionName = u'??'.encode("UTF-8")
    ResponseError = SLBResponseError

    def __init__(self, acs_access_key_id=None, acs_secret_access_key=None,
                 region=None, sdk_version=None, security_token=None):
        """
        Init method to create a new connection to SLB.
        """
        if not region:
            region = RegionInfo(self, self.DefaultRegionName,
                                self.DefaultRegionId)
        self.region = region
        if sdk_version:
            self.SDKVersion = sdk_version

        self.SLBSDK = 'aliyunsdkslb.request.v' + self.SDKVersion.replace('-', '')

        super(SLBConnection, self).__init__(acs_access_key_id,
                                            acs_secret_access_key,
                                            self.region, self.SLBSDK, security_token)
                                                                                 
    # C2C: Method added to create server load balancer
    def create_load_balancer(self, region_id, name=None, address_type=None, internet_charge_type=None, bandwidth=None,
                             ids=None, vswitch_id=None, zones=None, listeners=None, helth_checkup=None, stickness=None):
        """
        :type region: dict
        :param region_id: The instance?s Region ID
        :type name: dict
        :param name: Name to the server load balancer
        :type address_type: dict
        :param address_type:  Address type. value: internet or intranet
        :type internet_charge_type: dict
        :param internet_charge_type: Charging mode for the public network instance
            Value: paybybandwidth or paybytraffic
        :type bandwidth: dict
        :param bandwidth: Bandwidth peak of the public network instance charged per fixed bandwidth
        :type ids: dict
        :param ids: To ensure idempotence of a request
        :type vswitch_id: dict
        :param vswitch_id: The vswitch id of the VPC instance. This option is invalid if address_type parameter is
            provided as internet.
        :return:
        """

        params = {}
        results = []

        self.build_list_params(params, region_id, 'RegionId')
        if name:
            self.build_list_params(params, name, 'LoadBalancerName')
        if address_type:
            self.build_list_params(params, address_type, 'AddressType')
        if internet_charge_type:
            self.build_list_params(params, internet_charge_type, 'InternetChargeType')
        if bandwidth:
            self.build_list_params(params, bandwidth, 'Bandwidth')
        if ids:
            self.build_list_params(params, ids, 'ClientToken')
        if vswitch_id:
            self.build_list_params(params, vswitch_id, 'VSwitchId')
        if zones:
            for idx, val in enumerate(zones):
                if idx == 0:
                    self.build_list_params(params, val, 'MasterZoneId')
                else:
                    self.build_list_params(params, val, 'SlaveZoneId')

        try:
            results = self.get_status('CreateLoadBalancer', params)
        except Exception as ex:
            msg, stack = ex.args
            results.append("Create Load Balancer Error:" + str(msg) + " " + str(stack))
        else:
            slb_id=str(results[u'LoadBalancerId'])
            if slb_id:
                for listener in listeners:
                    if listener:
                        if 'protocol' in listener:
                            if listener['protocol'] in ["HTTP", "http"]:
                                listener_result = self.create_load_balancer_http_listener(slb_id, listener,
                                                                                          helth_checkup, stickness)
                                if listener_result:
                                    results.update({"http_listener_result": listener_result})

                            if listener['protocol'] in ["HTTPS", "https"]:
                                listener_result = self.create_load_balancer_https_listener(slb_id, listener,
                                                                                           helth_checkup, stickness)
                                if listener_result:
                                    results.update({"https_listener_result": listener_result})

                            if listener['protocol'] in ["TCP", "tcp"]:
                                listener_result = self.create_load_balancer_tcp_listener(slb_id, listener,
                                                                                         helth_checkup)
                                if listener_result:
                                    results.update({"tcp_listener_result": listener_result})

                            if listener['protocol'] in ["UDP", "udp"]:
                                listener_result = self.create_load_balancer_udp_listener(slb_id, listener,
                                                                                         helth_checkup)
                                if listener_result:
                                    results.update({"udp_listener_result": listener_result})
        return results

    # C2C: Method added to create load balancer HTTP listener
    def create_load_balancer_http_listener(self, slb_id, listener, helth_checkup, stickness):
        """
        :param listener:
        :param helth_checkup:
        :param stickness:
        :return:
        """
        params = {}
        results = []

        if listener:              
            self.build_list_params(params, slb_id, 'LoadBalancerId')
            if 'load_balancer_port' in listener:
                self.build_list_params(params, listener['load_balancer_port'], 'ListenerPort')
            if 'bandwidth' in listener:
                self.build_list_params(params, listener['bandwidth'], 'Bandwidth')             
            #if 'instance_protocol' in listener:
            #    self.build_list_params(params, listener['instance_protocol'], '')
            if 'instance_port' in listener:
                self.build_list_params(params, listener['instance_port'], 'BackendServerPort')
            #if 'proxy_protocol' in listener:
            #    self.build_list_params(params, listener['proxy_protocol'], '')

        if helth_checkup:
            if 'health_check' in helth_checkup:
                self.build_list_params(params, helth_checkup['health_check'], 'HealthCheck')
            if 'ping_port' in helth_checkup:
                self.build_list_params(params, helth_checkup['ping_port'], 'HealthCheckConnectPort')
            if 'ping_path' in helth_checkup:
                self.build_list_params(params, helth_checkup['ping_path'], 'HealthCheckURI')
            if 'response_timeout' in helth_checkup:
                self.build_list_params(params, helth_checkup['response_timeout'], 'HealthCheckTimeout')
            if 'interval' in helth_checkup:
                self.build_list_params(params, helth_checkup['interval'], 'HealthCheckInterval')
            if 'unhealthy_threshold' in helth_checkup:
                self.build_list_params(params, helth_checkup['unhealthy_threshold'], 'UnhealthyThreshold')
            if 'healthy_threshold' in helth_checkup:
                self.build_list_params(params, helth_checkup['healthy_threshold'], 'HealthyThreshold')

        if stickness:
            if 'enabled' in stickness:
                self.build_list_params(params, stickness['enabled'], 'StickySession')
            if 'type' in stickness:
                self.build_list_params(params, stickness['type'], 'StickySessionType')
            #if 'expiration' in stickness:
            #    self.build_list_params(params, stickness['expiration'], '')
            if 'cookie' in stickness:
                self.build_list_params(params, stickness['cookie'], 'Cookie')
            if 'cookie_timeout' in stickness:
                self.build_list_params(params, stickness['cookie_timeout'], 'CookieTimeout')

        try:
            results = self.get_status('CreateLoadBalancerHTTPListener', params)
        except Exception as ex:
            msg, stack = ex.args
            results.append("Create Load Balancer HTTP Listener Error:" + str(msg) + " " + str(stack))

        return results

    # C2C: Method added to create load balancer HTTPS listener
    def create_load_balancer_https_listener(self, slb_id, listener, helth_checkup, stickness):
        """
        :param listener:
        :param helth_checkup:
        :param stickness:
        :return:
        """
        params = {}
        results = []

        if listener:
            self.build_list_params(params, slb_id, 'LoadBalancerId')
            if 'load_balancer_port' in listener:
                self.build_list_params(params, listener['load_balancer_port'], 'ListenerPort')
            if 'bandwidth' in listener:
                self.build_list_params(params, listener['bandwidth'], 'Bandwidth')             
            #if 'instance_protocol' in listener:
            #    self.build_list_params(params, listener['instance_protocol'], '')
            if 'instance_port' in listener:
                self.build_list_params(params, listener['instance_port'], 'BackendServerPort')
            #if 'proxy_protocol' in listener:
            #    self.build_list_params(params, listener['proxy_protocol'], '')
            if 'ssl_certificate_id' in listener:
                self.build_list_params(params, listener['ssl_certificate_id'], 'ServerCertificateId')

        if helth_checkup:
            if 'health_check' in helth_checkup:
                self.build_list_params(params, helth_checkup['health_check'], 'HealthCheck')
            if 'ping_port' in helth_checkup:
                self.build_list_params(params, helth_checkup['ping_port'], 'HealthCheckConnectPort')
            if 'ping_path' in helth_checkup:
                self.build_list_params(params, helth_checkup['ping_path'], 'HealthCheckURI')
            if 'response_timeout' in helth_checkup:
                self.build_list_params(params, helth_checkup['response_timeout'], 'HealthCheckTimeout')
            if 'interval' in helth_checkup:
                self.build_list_params(params, helth_checkup['interval'], 'HealthCheckInterval')
            if 'unhealthy_threshold' in helth_checkup:
                self.build_list_params(params, helth_checkup['unhealthy_threshold'], 'UnhealthyThreshold')
            if 'healthy_threshold' in helth_checkup:
                self.build_list_params(params, helth_checkup['healthy_threshold'], 'HealthyThreshold')

        if stickness:
            if 'enabled' in stickness:
                self.build_list_params(params, stickness['enabled'], 'StickySession')
            if 'type' in stickness:
                self.build_list_params(params, stickness['type'], 'StickySessionType')
            #if 'expiration' in stickness:
            #    self.build_list_params(params, stickness['expiration'], '')
            if 'cookie' in stickness:
                self.build_list_params(params, stickness['cookie'], 'Cookie')
            if 'cookie_timeout' in stickness:
                self.build_list_params(params, stickness['cookie_timeout'], 'CookieTimeout')

        try:
            results = self.get_status('CreateLoadBalancerHTTPSListener', params)
        except Exception as ex:
            msg, stack = ex.args
            results.append("Create Load Balancer HTTPS Listener Error:" + str(msg) + " " + str(stack))

        return results

    # C2C: Method added to create load balancer TCP listener
    def create_load_balancer_tcp_listener(self, slb_id, listener, helth_checkup):
        """
        :param listener:
        :param helth_checkup:
        :return:
        """
        params = {}
        results = []

        if listener:
            self.build_list_params(params, slb_id, 'LoadBalancerId')
            if 'load_balancer_port' in listener:
                self.build_list_params(params, listener['load_balancer_port'], 'ListenerPort')
            if 'bandwidth' in listener:
                self.build_list_params(params, listener['bandwidth'], 'Bandwidth')
            # if 'instance_protocol' in listener:
            #    self.build_list_params(params, listener['instance_protocol'], '')
            if 'instance_port' in listener:
                self.build_list_params(params, listener['instance_port'], 'BackendServerPort')
            # if 'proxy_protocol' in listener:
            #    self.build_list_params(params, listener['proxy_protocol'], '')

        if helth_checkup:
            if 'ping_port' in helth_checkup:
                self.build_list_params(params, helth_checkup['ping_port'], 'HealthCheckConnectPort')
            if 'response_timeout' in helth_checkup:
                self.build_list_params(params, helth_checkup['response_timeout'], 'HealthCheckConnectTimeout')
            if 'interval' in helth_checkup:
                self.build_list_params(params, helth_checkup['interval'], 'HealthCheckInterval')
            if 'unhealthy_threshold' in helth_checkup:
                self.build_list_params(params, helth_checkup['unhealthy_threshold'], 'UnhealthyThreshold')
            if 'healthy_threshold' in helth_checkup:
                self.build_list_params(params, helth_checkup['healthy_threshold'], 'HealthyThreshold')
        try:
            results = self.get_status('CreateLoadBalancerTCPListener', params)
        except Exception as ex:
            msg, stack = ex.args
            results.append("Create Load Balancer TCP Listener Error:" + str(msg) + " " + str(stack))

        return results

    # C2C: Method added to create load balancer UDP listener
    def create_load_balancer_udp_listener(self, slb_id, listener, helth_checkup):
        """
        :param listener:
        :param helth_checkup:
        :return:
        """
        params = {}
        results = []

        if listener:
            self.build_list_params(params, slb_id, 'LoadBalancerId')
            if 'load_balancer_port' in listener:
                self.build_list_params(params, listener['load_balancer_port'], 'ListenerPort')
            if 'bandwidth' in listener:
                self.build_list_params(params, listener['bandwidth'], 'Bandwidth')
            # if 'instance_protocol' in listener:
            #    self.build_list_params(params, listener['instance_protocol'], '')
            if 'instance_port' in listener:
                self.build_list_params(params, listener['instance_port'], 'BackendServerPort')
            # if 'proxy_protocol' in listener:
            #    self.build_list_params(params, listener['proxy_protocol'], '')

        if helth_checkup:
            if 'ping_port' in helth_checkup:
                self.build_list_params(params, helth_checkup['ping_port'], 'HealthCheckConnectPort')
            if 'response_timeout' in helth_checkup:
                self.build_list_params(params, helth_checkup['response_timeout'], 'HealthCheckConnectTimeout')
            if 'interval' in helth_checkup:
                self.build_list_params(params, helth_checkup['interval'], 'HealthCheckInterval')
            if 'unhealthy_threshold' in helth_checkup:
                self.build_list_params(params, helth_checkup['unhealthy_threshold'], 'UnhealthyThreshold')
            if 'healthy_threshold' in helth_checkup:
                self.build_list_params(params, helth_checkup['healthy_threshold'], 'HealthyThreshold')

        try:
            results = self.get_status('CreateLoadBalancerUDPListener', params)
        except Exception as ex:
            msg, stack = ex.args
            results.append("Create Load Balancer UDP Listener Error:" + str(msg) + " " + str(stack))

        return results
