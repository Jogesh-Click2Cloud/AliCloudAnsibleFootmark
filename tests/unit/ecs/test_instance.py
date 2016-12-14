#!/usr/bin/env python
# import sys
# sys.path.append("../../..")
from footmark.ecs.connection import ECSConnection
from tests.unit import ACSMockServiceTestCase
import json

DESCRIBE_INSTANCE = '''
{
  "Instances": {
    "Instance": [
      {
        "CreationTime": "2016-06-20T21:37Z",
        "DeviceAvailable": true,
        "EipAddress": {},
        "ExpiredTime": "2016-10-22T16:00Z",
        "HostName": "xiaozhu_test",
        "ImageId": "centos6u5_64_40G_cloudinit_20160427.raw",
        "InnerIpAddress": {
          "IpAddress": [
            "10.170.106.80"
          ]
        },
        "InstanceChargeType": "PostPaid",
        "InstanceId": "i-94dehop6n",
        "InstanceNetworkType": "classic",
        "InstanceType": "ecs.s2.large",
        "InternetChargeType": "PayByTraffic",
        "InternetMaxBandwidthIn": -1,
        "InternetMaxBandwidthOut": 1,
        "IoOptimized": false,
        "OperationLocks": {
          "LockReason": []
        },
        "PublicIpAddress": {
          "IpAddress": [
            "120.25.13.106"
          ]
        },
        "RegionId": "cn-shenzhen",
        "SecurityGroupIds": {
          "SecurityGroupId": [
            "sg-94kd0cyg0"
          ]
        },
        "SerialNumber": "51d1353b-22bf-4567-a176-8b3e12e43135",
        "Status": "Running",
        "Tags":{
          "Tag":[
            {
              "TagValue":"1.20",
              "TagKey":"xz_test"
            },
            {
              "TagValue":"1.20",
              "TagKey":"xz_test_2"
            }
          ]
        },
        "VpcAttributes": {
          "PrivateIpAddress": {
            "IpAddress": []
          }
        },
        "ZoneId": "cn-shenzhen-a"
      }
    ]
  },
  "PageNumber": 1,
  "PageSize": 10,
  "RequestId": "14A07460-EBE7-47CA-9757-12CC4761D47A",
  "TotalCount": 1
}
'''

MANAGE_INSTANCE = '''
{
    "RequestId": "14A07460-EBE7-47CA-9757-12CC4761D47A",
}
'''

CREATE_INSTANCE = '''
{
    "InstanceId":"i-2zeg0900kzwn7dpo7zrb",
    "RequestId":"9206E7A7-BFD5-457F-9173-91CF4525DE21"
}
'''

MODIFY_INSTANCE= '''
{
    "RequestId":"0C7EFCF3-1517-44CD-B61B-60FA49FEF04E"
}
'''

QUERYING_INSTANCE='''  
{
    "PageNumber": 1,
    "InstanceStatuses":
         {"InstanceStatus": [
            {"Status": "Running", "InstanceId": "i-2zehcagr3vt06iyir7hc"},
            {"Status": "Running", "InstanceId": "i-2zedup3d5p01daky1622"},
            {"Status": "Stopped", "InstanceId": "i-2zei2zq55lx87st85x2j"},
            {"Status": "Running", "InstanceId": "i-2zeaoq67u62vmkbo71o7"},
            {"Status": "Running", "InstanceId": "i-2ze5wl5aeq8kbblmjsx1"}
         ]},
        "TotalCount": 9,
        "PageSize": 5,
        "RequestId": "5D464158-D291-4C69-AA9E-84839A669B9D"
}
'''
JOIN_GROUP='''
{
    "RequestId": "AF3991A3-5203-4F83-8FAD-FDC1253AF15D"
}
'''
LEAVE_GROUP='''
{
    "RequestId": "AF3991A3-5203-4F83-8FAD-FDC1253AF15D"
}
'''
ATTACH_DISK='''
{
    "RequestId": "AF3991A3-5203-4F83-8FAD-FDC1253AF15D"
}
'''
class TestDescribeInstances(ACSMockServiceTestCase):
    connection_class = ECSConnection

    def default_body(self):
        return DESCRIBE_INSTANCE

    def test_instance_attribute(self):
        self.set_http_response(status_code=200, body=DESCRIBE_INSTANCE)
        filters = {}
        instance_ids = ["i-94dehop6n"]
        tag_key = 'xz_test'
        tag_value = '1.20'
        filters['tag:' + tag_key] = tag_value
        instances = self.service_connection.get_all_instances(instance_ids=instance_ids, filters=filters)
        self.assertEqual(len(instances), 1)
        instance = instances[0]
        self.assertEqual(instance.id, 'i-94dehop6n')
        print 'group_id:', instance.group_id
        self.assertEqual(instance.group_id, 'sg-94kd0cyg0')
        self.assertEqual(instance.public_ip, '120.25.13.106')
        self.assertEqual(instance.tags, {"xz_test": "1.20", "xz_test_2": "1.20"})
        self.assertFalse(instance.io_optimized)
        self.assertEqual(instance.status, 'running')
        self.assertEqual(instance.image_id, 'centos6u5_64_40G_cloudinit_20160427.raw')
        return instances

    def test_manage_instances(self):
        self.set_http_response(status_code=200, body=MANAGE_INSTANCE)
        instances = self.test_instance_attribute()
        for inst in instances:
            if inst.state == 'running':
                inst.stop()
            elif inst.state == 'stopped':
                inst.start()
            else:
                inst.reboot()


class TestManageInstances(ACSMockServiceTestCase):
    connection_class = ECSConnection
    instance_ids = ['i-94dehop6n', 'i-95dertop6m']

    def default_body(self):
        return MANAGE_INSTANCE

    def test_start_instance(self):
        self.set_http_response(status_code=200)
        result = self.service_connection.start_instances(instance_ids=self.instance_ids)
        self.assertEqual(len(result), len(self.instance_ids))
        self.assertIn(result[0], self.instance_ids)

    def test_stop_instance(self):
        self.set_http_response(status_code=200)
        result = self.service_connection.stop_instances(instance_ids=self.instance_ids, force=True)
        self.assertEqual(len(result), len(self.instance_ids))
        self.assertIn(result[0], self.instance_ids)

    def test_reboot_instance(self):
        self.set_http_response(status_code=200)
        result = self.service_connection.reboot_instances(instance_ids=self.instance_ids, force=True)
        self.assertEqual(len(result), len(self.instance_ids))
        self.assertIn(result[0], self.instance_ids)

    def test_terminate_instance(self):
        self.set_http_response(status_code=200)
        result = self.service_connection.terminate_instances(instance_ids=self.instance_ids, force=True)
        self.assertEqual(len(result), len(self.instance_ids))
        self.assertIn(result[0], self.instance_ids)


# C2C : Unit Test For CreateInstance Method
class TestCreateInstance(ACSMockServiceTestCase):
    connection_class = ECSConnection

    acs_access_key_id = "N8cvD83K81USpn3u"
    acs_secret_access_key = "fqbuZIKPxOdu36yhFvaBtihNqD2qQ2"
    region_id = "cn-beijing"
    image_id = "ubuntu1404_64_40G_cloudinit_20160727.raw"
    instance_type = "ecs.n1.small"
    group_id = "sg-25y6ag32b"
    zone_id = "cn-beijing-b"
    io_optimized = "optimized"
    instance_name = "MyInstance"
    description = None
    internet_data = {
                        'charge_type': 'PayByBandwidth',
                        'max_bandwidth_in': 200,
                        'max_bandwidth_out': 0
                    }

    host_name = None
    password = None
    system_disk = {"disk_category": "cloud_efficiency", "disk_size": 50 }
    volumes = [
        {
            "device_category": "cloud_efficiency",
            "device_size": 20,
            "device_name": "volume1",
            "device_description": "volume 1 description comes here"
        },
        {
            "device_category": "cloud_efficiency",
            "device_size": 20,
            "device_name": "volume2",
            "device_description": "volume 2 description comes here"
        }
    ]
    vswitch_id = None
    instance_tags = [
        {
            "tag_key": "create_test_1",
            "tag_value": "0.01"
        },
        {
            "tag_key": "create_test_2",
            "tag_value": "0.02"
        }
    ]
    allocate_public_ip = True
    bind_eip = False
    instance_charge_type = None
    period = None
    auto_renew = False
    ids = None
    count = 1    
    
    def default_body(self):
        return CREATE_INSTANCE
                                                                    
    def test_create_instance(self):
        self.set_http_response(status_code=200)
        result = self.service_connection.create_instance(region_id=self.region_id, image_id=self.image_id,
                                                         instance_type=self.instance_type, group_id=self.group_id,
                                                         zone_id=self.zone_id, instance_name=self.instance_name,
                                                         description=self.description, internet_data=self.internet_data,
                                                         host_name=self.host_name, password=self.password,
                                                         io_optimized=self.io_optimized, system_disk=self.system_disk,
                                                         volumes=self.volumes, vswitch_id=self.vswitch_id,
                                                         instance_tags=self.instance_tags,
                                                         allocate_public_ip=self.allocate_public_ip,
                                                         bind_eip=self.bind_eip, count=self.count,
                                                         instance_charge_type=self.instance_charge_type,
                                                         period=self.period, auto_renew=self.auto_renew, ids=self.ids)     
        
        self.assertEqual(len(result), self.count)
        self.assertIn(result[0], "i-2zeg0900kzwn7dpo7zrb")


class TestModifyInstance(ACSMockServiceTestCase):
    connection_class = ECSConnection
    attributes = [
        {
            "id": "i-2zebgzk74po3gx1dwvuo",
            "name": "new_once_again",
            "description": "volumedecsription",
            "password": "Pas@sAdmin",
            "host_name": "hostingAdmin"
        },
        {
            "id": "i-2zeaoq67u62vmkbo71o7",
            "host_name": "adminhostadmin"
        }
    ]

    def default_body(self):
        return MODIFY_INSTANCE

    def test_modify_instance(self):
        self.set_http_response(status_code=200)
        result = self.service_connection.modify_instance(attributes=self.attributes)
        self.assertEqual(len(result), len(self.attributes))
        self.assertIn(result[0], "success")


class TestQueryingInstance(ACSMockServiceTestCase):
    connection_class = ECSConnection
   
    region_id="cn-beijing"
    page_number=1
    page_size=5

    def default_body(self):
        return QUERYING_INSTANCE

    def test_querying_instance(self):
        self.set_http_response(status_code=200)
        result = self.service_connection.querying_instance(region_id=self.region_id, zone_id=None, 
                                                           page_number=self.page_number,
                                                           page_size=self.page_size)
        
        self.assertEqual(result[u'PageNumber'], self.page_number)
        self.assertEqual(result[u'PageSize'], self.page_size)
        
class TestJoinSecGrp(ACSMockServiceTestCase): 
    connection_class = ECSConnection
    acs_access_key = 'LTAIV7yukr6Csf14'
    acs_secret_access_key = 'it9TEJcJvnDyL5uB830fx1BQwzdNdd'
    instance_ids = ["i-j6c5txh3q0wivxt5m807"]
    group_id = 'sg-j6c34iujuqbw29zpd53u'
    region = 'cn-hongkong'
    state = 'join'
    
    def default_body(self):
        return JOIN_GROUP

    def test_join_grp(self):
        self.set_http_response(status_code=200)
        result = self.service_connection.join_security_group(instance_id = self.instance_ids, security_group_id = self.group_id)
        ###self.assertEqual(len(result), len(self.attributes))
        self.assertEqual(result[0], "success")

class TestLeaveSecGrp(ACSMockServiceTestCase): 
    connection_class = ECSConnection
    acs_access_key = 'LTAIV7yukr6Csf14'
    acs_secret_access_key = 'it9TEJcJvnDyL5uB830fx1BQwzdNdd'
    instance_ids = ["i-j6c5txh3q0wivxt5m807"]
    group_id = 'sg-j6c34iujuqbw29zpd53u'
    region = 'cn-hongkong'
    state = 'remove'
    
    def default_body(self):
        return LEAVE_GROUP
    def test_leave_grp(self):
        self.set_http_response(status_code=200)
        result = self.service_connection.leave_security_group(instance_id = self.instance_ids, security_group_id = self.group_id)
        ###self.assertEqual(len(result), len(self.attributes))
        self.assertEqual(result[0], "success")

class TestAttachDisk(ACSMockServiceTestCase): 
    connection_class = ECSConnection
    acs_access_key = 'LTAIV7yukr6Csf14'
    acs_secret_access_key = 'it9TEJcJvnDyL5uB830fx1BQwzdNdd'
    instance_ids = ["i-j6c5txh3q0wivxt5m807"]
    disk_id = 'd-j6cc9ssgxbkjdf55w8p7'
    region = 'cn-hongkong'
    device = None
    delete_with_instance = None
    state = 'attach'
    
    def default_body(self):
        return ATTACH_DISK
    def attach_disk(self):
        self.set_http_response(status_code=200)
        result = self.service_connection.attach_disk_to_instance(disk_id = self.disk_id, instance_id = self.instance_ids,region_id = self.region, device = self.device,delete_with_instance = self.delete_with_instance)
        ###self.assertEqual(len(result), len(self.attributes))
        self.assertEqual(result[0], "success")