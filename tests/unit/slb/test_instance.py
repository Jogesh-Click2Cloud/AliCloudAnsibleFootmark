#!/usr/bin/env python
# import sys
# sys.path.append("../../..")
from footmark.slb.connection import SLBConnection
from tests.unit import ACSMockServiceTestCase
import json


CREATE_LOAD_BALANCER = '''
{
    "Address": "60.205.131.32",
    "LoadBalancerId": "lb-2ze9vjx6o2hnmte7s71d6",
    "LoadBalancerName": "my_slb",
    "NetworkType": "classic",
    "RequestId": "3C97A537-4D50-4079-93BE-26E3B5C8B527",
    "VSwitchId": "",
    "VpcId": "",
    "http_listener_result": "success"
} 
'''


# C2C : Unit Test For CreateLoadBalancer Method
class TestCreateLoadBalancer(ACSMockServiceTestCase):
    connection_class = SLBConnection

    acs_access_key_id = "N8cvD83K81USpn3u"
    acs_secret_access_key = "fqbuZIKPxOdu36yhFvaBtihNqD2qQ2"
    region_id = "cn-beijing"
    listeners=[
        {
            "protocol":"http",
            "load_balancer_port":"80",
            "instance_port":"80",
            "bandwidth":"1"        
        }
    ]
    helth_checkup={
        "health_check":"on",
        "ping_port":"80",
        "ping_path":"/index.html",
        "response_timeout":"5",
        "interval":"30",
        "unhealthy_threshold":"2",
        "healthy_threshold":"10"
    }
    stickness={
        "enabled":"on",
        "type":"insert",
        "cookie":"300",
        "cookie_timeout":"1"
    }
    name="my_slb"
    address_type=None
    internet_charge_type=None
    bandwidth=None
    ids=None

    def default_body(self):
        return CREATE_LOAD_BALANCER
                                                                    
    def test_create_load_balancer(self):
        self.set_http_response(status_code=200)
        result = self.service_connection.create_load_balancer(region_id=self.region_id, name=self.name,
                                                              address_type=self.address_type,
                                                              internet_charge_type=self.internet_charge_type,
                                                              bandwidth=self.bandwidth, ids=self.ids,
                                                              listeners=self.listeners,
                                                              helth_checkup=self.helth_checkup,
                                                              stickness=self.stickness)
        
        self.assertEqual(result[u'LoadBalancerId'],  u'lb-2ze9vjx6o2hnmte7s71d6')




        

