# encoding: utf-8
"""
Represents a connection to the ECS service.
"""

import warnings

import six
import time
import json

from footmark.connection import ACSQueryConnection
from footmark.ecs.instance import Instance
from footmark.ecs.regioninfo import RegionInfo
from footmark.ecs.securitygroup import SecurityGroup
from footmark.ecs.volume import Disk
from footmark.exception import ECSResponseError


class ECSConnection(ACSQueryConnection):
    # SDKVersion = footmark.config.get('Footmark', 'ecs_version', '2014-05-26')
    SDKVersion = '2014-05-26'
    DefaultRegionId = 'cn-hangzhou'
    DefaultRegionName = u'杭州'.encode("UTF-8")
    ResponseError = ECSResponseError

    def __init__(self, acs_access_key_id=None, acs_secret_access_key=None,
                 region=None, sdk_version=None, security_token=None, ):
        """
        Init method to create a new connection to ECS.
        """
        if not region:
            region = RegionInfo(self, self.DefaultRegionName,
                                self.DefaultRegionId)
        self.region = region
        if sdk_version:
            self.SDKVersion = sdk_version

        self.ECSSDK = 'aliyunsdkecs.request.v' + self.SDKVersion.replace('-', '')

        super(ECSConnection, self).__init__(acs_access_key_id,
                                            acs_secret_access_key,
                                            self.region, self.ECSSDK, security_token)

    def build_filter_params(self, params, filters):
        if not isinstance(filters, dict):
            return

        flag = 1
        for key, value in filters.items():
            acs_key = key
            if acs_key.startswith('tag:'):
                while (('set_Tag%dKey' % flag) in params):
                    flag += 1
                if flag < 6:
                    params['set_Tag%dKey' % flag] = acs_key[4:]
                    params['set_Tag%dValue' % flag] = filters[acs_key]
                flag += 1
                continue
            if key == 'group_id':
                if not value.startswith('sg-') or len(value) != 12:
                    warnings.warn("The group-id filter now requires a security group "
                                  "identifier (sg-*) instead of a security group ID. "
                                  "The group-id " + value + "may be invalid.",
                                  UserWarning)
                params['set_SecurityGroupId'] = value
                continue
            if not isinstance(value, dict):
                acs_key = ''.join(s.capitalize() for s in acs_key.split('_'))
                params['set_' + acs_key] = value
                continue

            self.build_filters_params(params, value)

    # Instance methods

    def get_all_instances(self, instance_ids=None, filters=None, max_results=None):
        """
        Retrieve all the instance associated with your account.

        :rtype: list
        :return: A list of  :class:`footmark.ecs.instance`

        """
        warnings.warn(('The current get_all_instances implementation will be '
                       'replaced with get_all_instances.'),
                      PendingDeprecationWarning)

        params = {}
        if instance_ids:
            self.build_list_params(params, instance_ids, 'InstanceIds')
        if filters:
            self.build_filter_params(params, filters)
        if max_results is not None:
            params['MaxResults'] = max_results
        instances = self.get_list('DescribeInstances', params, ['Instances', Instance])
        for inst in instances:
            filters = {}
            filters['instance_id'] = inst.id
            volumes = self.get_all_volumes(filters=filters)
            block_device_mapping = {}
            for vol in volumes:
                block_device_mapping[vol.id] = vol
            setattr(inst, 'block_device_mapping', block_device_mapping)
            filters = {}
            filters['security_group_id'] = inst.security_group_id
            security_groups = self.get_all_security_groups(filters=filters)
            setattr(inst, 'security_groups', security_groups)

        return instances

    def start_instances(self, instance_ids=None):
        """
        Start the instances specified

        :type instance_ids: list
        :param instance_ids: A list of strings of the Instance IDs to start

        :rtype: list
        :return: A list of the instances started
        """
        params = {}
        results = []
        if instance_ids:
            if isinstance(instance_ids, six.string_types):
                instance_ids = [instance_ids]
            for instance_id in instance_ids:
                self.build_list_params(params, instance_id, 'InstanceId')
                if self.get_status('StartInstance', params):
                    results.append(instance_id)
        return results

    def stop_instances(self, instance_ids=None, force=False):
        """
        Stop the instances specified

        :type instance_ids: list
        :param instance_ids: A list of strings of the Instance IDs to stop

        :type force: bool
        :param force: Forces the instance to stop

        :rtype: list
        :return: A list of the instances stopped
        """
        params = {}
        results = []
        if force:
            self.build_list_params(params, 'true', 'ForceStop')
        if instance_ids:
            if isinstance(instance_ids, six.string_types):
                instance_ids = [instance_ids]
            for instance_id in instance_ids:
                self.build_list_params(params, instance_id, 'InstanceId')
                if self.get_status('StopInstance', params):
                    results.append(instance_id)
        return results

    def reboot_instances(self, instance_ids=None, force=False):
        """
        Reboot the specified instances.

        :type instance_ids: list
        :param instance_ids: The instances to terminate and reboot

        :type force: bool
        :param force: Forces the instance to stop

        """
        params = {}
        results = []
        if force:
            self.build_list_params(params, 'true', 'ForceStop')
        if instance_ids:
            if isinstance(instance_ids, six.string_types):
                instance_ids = [instance_ids]
            for instance_id in instance_ids:
                self.build_list_params(params, instance_id, 'InstanceId')
                if self.get_status('RebootInstance', params):
                    results.append(instance_id)

        return results

    def terminate_instances(self, instance_ids=None, force=False):
        """
        Terminate the instances specified

        :type instance_ids: list
        :param instance_ids: A list of strings of the Instance IDs to terminate

        :type force: bool
        :param force: Forces the instance to stop

        :rtype: list
        :return: A list of the instance_ids terminated
        """
        params = {}
        result = []
        if force:
            self.build_list_params(params, 'true', 'Force')
        if instance_ids:
            if isinstance(instance_ids, six.string_types):
                instance_ids = [instance_ids]
            for instance_id in instance_ids:
                self.build_list_params(params, instance_id, 'InstanceId')
                if self.get_status('DeleteInstance', params):
                    result.append(instance_id)
        return result

    def get_all_volumes(self, volume_ids=None, filters=None):
        """
        Get all Volumes associated with the current credentials.

        :type volume_ids: list
        :param volume_ids: Optional list of volume ids.  If this list
                           is present, only the volumes associated with
                           these volume ids will be returned.

        :type filters: dict
        :param filters: Optional filters that can be used to limit
                        the results returned.  Filters are provided
                        in the form of a dictionary consisting of
                        filter names as the key and filter values
                        as the value.  The set of allowable filter
                        names/values is dependent on the request
                        being performed.  Check the ECS API guide
                        for details.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: list of :class:`boto.ec2.volume.Volume`
        :return: The requested Volume objects
        """
        params = {}
        if volume_ids:
            self.build_list_params(params, volume_ids, 'DiskIds')
        if filters:
            self.build_filter_params(params, filters)
        return self.get_list('DescribeDisks', params, ['Disks', Disk])

    def get_all_security_groups(self, group_ids=None, filters=None):
        """
        Get all security groups associated with your account in a region.

        :type group_ids: list
        :param group_ids: A list of IDs of security groups to retrieve for
                          security groups within a VPC.

        :type filters: dict
        :param filters: Optional filters that can be used to limit
                        the results returned.  Filters are provided
                        in the form of a dictionary consisting of
                        filter names as the key and filter values
                        as the value.  The set of allowable filter
                        names/values is dependent on the request
                        being performed.  Check the EC2 API guide
                        for details.

        :rtype: list
        :return: A list of :class:`boto.ec2.securitygroup.SecurityGroup`
        """
        params = {}
        if group_ids:
            self.build_list_params(params, group_ids, 'SecurityGroupId')
        if filters:
            self.build_filter_params(params, filters)
        return self.get_list('DescribeSecurityGroups', params, ['SecurityGroups', SecurityGroup])

    # C2C : Method added to create an instance
    def create_instance(self, region_id, image_id, instance_type, group_id=None, zone_id=None,
                        instance_name=None, description=None, internet_data=None, host_name=None,
                        password=None, io_optimized=None, system_disk=None, volumes=None,
                        vswitch_id=None, instance_tags=None, allocate_public_ip=None,
                        bind_eip=None, count=None, instance_charge_type=None, period=None,
                        auto_renew=None, ids=None):
        """
        create an instance in ecs

        :type region: dict
        :param region: The instance’s Region ID

        :type image_id: dict
        :param image_id: ID of an image file, indicating an image selected
            when an instance is started

        :type instance_type: dict
        :param instance_type: Type of the instance

        :type group_id: dict
        :param group_id: ID of the security group to which a newly created
            instance belongs

        :type zone_id: dict
        :param zone_id: ID of a zone to which an instance belongs. If it is
            null, a zone is selected by the system

        :type instance_name: dict
        :param instance_name: Display name of the instance, which is a string
            of 2 to 128 Chinese or English characters. It must begin with an
            uppercase/lowercase letter or a Chinese character and can contain
            numerals, “.”, “_“, or “-“.

        :type description: dict
        :param description: Description of the instance, which is a string of
            2 to 256 characters.

        :type internet_data: list
        :param internet_data: It includes Internet charge type which can be
            PayByTraffic or PayByBandwidth, max_bandwidth_in and max_bandwidth_out

        :type host_name: dict
        :param host_name: Host name of the ECS, which is a string of at least
            two characters. “hostname” cannot start or end with “.” or “-“.
            In addition, two or more consecutive “.” or “-“ symbols are not
            allowed.

        :type password: dict
        :param password: Password to an instance is a string of 8 to 30
            characters

        :type io_optimized: dict
        :param io_optimized: values are (1) none: none I/O Optimized
            (2) optimized: I/O Optimized

        :type system_disk: dict
        :param system_disk: It includes disk_category, disk_size,
            disk_name and disk_description

        :type volumes: list
        :param volumes: It includes device_category, device_size,
            device_name, device_description, delete_on_termination
            and snapshot

        :type vswitch_id: dict
        :param vswitch_id: When launching an instance in VPC, the
            virtual switch ID must be specified

        :type instance_tags: list
        :param instance_tags: A list of hash/dictionaries of instance
            tags, '[{tag_key:"value", tag_value:"value"}]', tag_key
            must be not null when tag_value isn't null

        :type allocate_public_ip: bool
        :param allocate_public_ip: Allocate Public IP Address to Instance

        :type bind_eip: bool
        :param bind_eip: Bind Elastic IP Address

        :type count: dict
        :param count: Create No. of Instances

        :rtype: dict
        :param period: The time that you have bought the resource,
            in month. Only valid when InstanceChargeType is set as
            PrePaid. Value range: 1 to 12

        :rtype: dict
        :param auto_renew: Whether automatic renewal is supported.
            Only valid when InstanceChargeType is set PrePaid. Value
            range True: indicates to automatically renew
                  False，indicates not to automatically renew
            Default value: False.

        :rtype: list
        :param ids: A list of identifier for this instance or set of
            instances, so that the module will be idempotent with
            respect to ECS instances.

        :rtype: dict
        :return: Returns a dictionary of instance information about
            the instances started/stopped. If the instance was not
            able to change state, "changed" will be set to False.
            Note that if instance_ids and instance_tags are both non-
            empty, this method will process the intersection of the two


        """

        params = {}
        results = []

        # Datacenter Region
        self.build_list_params(params, region_id, 'RegionId')

        # Datacenter Zone ID
        if zone_id:
            self.build_list_params(params, zone_id, 'ZoneId')

        # Operating System
        self.build_list_params(params, image_id, 'ImageId')

        # Instance Type
        self.build_list_params(params, instance_type, 'InstanceType')

        # Security Group
        if group_id:
            self.build_list_params(params, group_id, 'SecurityGroupId')

        # input/output optimized
        if io_optimized:
            self.build_list_params(params, io_optimized, 'IoOptimized')

        # VPC Switch Id
        if vswitch_id:
            self.build_list_params(params, vswitch_id, 'VSwitchId')

        # Instance Details
        if instance_name:
            self.build_list_params(params, instance_name, 'InstanceName')

        # Description of an instance
        if description:
            self.build_list_params(params, description, 'Description')

        # Internet Data
        if internet_data:
            if 'charge_type' in internet_data:
                self.build_list_params(params, internet_data[
                    'charge_type'], 'InternetChargeType')
            if 'max_bandwidth_in' in internet_data:
                self.build_list_params(params, internet_data[
                    'max_bandwidth_in'], 'InternetMaxBandwidthIn')
            if 'max_bandwidth_out' in internet_data:
                self.build_list_params(params, internet_data[
                    'max_bandwidth_out'], 'InternetMaxBandwidthOut')

        if instance_charge_type:
            self.build_list_params(params, instance_charge_type, 'InstanceChargeType')

            # when charge type is PrePaid add Period and Auto Renew Parameters
            if instance_charge_type == 'PrePaid':
                # period of an Instance
                if period:
                    self.build_list_params(params, period, 'Period')

                    # auto renewal of instance
                    if auto_renew:
                        self.build_list_params(params, auto_renew, 'AutoRenew')
                        self.build_list_params(params, period, 'AutoRenewPeriod')


                        # Security Setup
        if host_name:
            self.build_list_params(params, host_name, 'HostName')

        # Password to an instance
        if password:
            self.build_list_params(params, password, 'Password')

        # Storage - Primary Disk
        if system_disk:
            if 'disk_category' in system_disk:
                self.build_list_params(params, system_disk[
                    'disk_category'], 'SystemDisk.Category')
            if 'disk_size' in system_disk:
                self.build_list_params(params, system_disk[
                    'disk_size'], 'SystemDisk.Size')
            if 'disk_name' in system_disk:
                self.build_list_params(params, system_disk[
                    'disk_name'], 'SystemDisk.DiskName')
            if 'disk_description' in system_disk:
                self.build_list_params(params, system_disk[
                    'disk_description'], 'SystemDisk.Description')

        # Volumes Details
        volumeno = 1
        if volumes:
            for volume in volumes:
                if volume:
                    if 'device_category' in volume:
                        self.build_list_params(
                            params, volume['device_category'], 'DataDisk' + str(volumeno) + 'Category')
                    if 'device_size' in volume:
                        self.build_list_params(
                            params, volume['device_size'], 'DataDisk' + str(volumeno) + 'Size')
                    if 'device_name' in volume:
                        self.build_list_params(
                            params, volume['device_name'], 'DataDisk' + str(volumeno) + 'DiskName')
                    if 'device_description' in volume:
                        self.build_list_params(
                            params, volume['device_description'], 'DataDisk' + str(volumeno) + 'Description')
                    if 'delete_on_termination' in volume:
                        self.build_list_params(
                            params, volume['delete_on_termination'], 'DataDisk' + str(volumeno) + 'DeleteWithInstance')
                    if 'snapshot' in volume:
                        self.build_list_params(
                            params, volume['snapshot'], 'DataDisk' + str(volumeno) + 'SnapshotId')
                    volumeno = volumeno + 1

        # Instance Tags
        tagno = 1
        if instance_tags:
            for instance_tag in instance_tags:
                if instance_tag:
                    if 'tag_key' in instance_tag:
                        self.build_list_params(params, instance_tag[
                            'tag_key'], 'Tag' + str(tagno) + 'Key')
                    if 'tag_value' in instance_tag:
                        self.build_list_params(params, instance_tag[
                            'tag_value'], 'Tag' + str(tagno) + 'Value')
                    tagno = tagno + 1

        # Client Token
        if ids:
            if len(ids) == count:
                self.build_list_params(params, ids, 'ClientToken')

        for i in range(count):
            # CreateInstance method call, returns newly created instanceId
            try:
                instance_id = self.get_status('CreateInstance', params)
                results.append(instance_id)

            except Exception as ex:
                msg, stack = ex.args
                results.append("Create Instance Error:" +
                               str(msg) + " " + str(stack))
            else:
                try:
                    # Start newly created Instance
                    self.start_instances(instance_id)

                except Exception as ex:
                    msg, stack = ex.args
                    results.append("Start Instance Error:" +
                                   str(msg) + " " + str(stack))
                else:
                    # Allocate Public IP Address
                    try:
                        if allocate_public_ip:
                            # Wait for 1 min to start instance
                            # TODO: Replace this logic once get instance status method
                            # is implemented. once instance comes in running state,
                            # allocate allocate public ip
                            time.sleep(120)
                            allocate_public_ip_params = {}
                            self.build_list_params(
                                allocate_public_ip_params, instance_id, 'InstanceId')
                            self.build_list_params(
                                allocate_public_ip_params, region_id, 'RegionId')
                            public_ip_address_status = self.get_status(
                                'AllocatePublicIpAddress', allocate_public_ip_params)
                    except Exception as ex:
                        msg, stack = ex.args
                        results.append("Allocate Public IP Error:" +
                                       str(msg) + " " + str(stack))

                    # Allocate EIP Address
                    try:
                        if bind_eip:
                            allocate_eip_params = {}
                            self.build_list_params(
                                allocate_eip_params, bind_eip, 'AllocationId')
                            self.build_list_params(
                                allocate_eip_params, instance_id, 'InstanceId')
                            eip_address = self.get_status(
                                'AssociateEipAddress', allocate_eip_params)
                    except Exception as ex:
                        msg, stack = ex.args
                        results.append("Bind EIP Error:" + str(msg) + " " + str(stack))

        return results

    # C2C: Method added to modify instance attributes
    def modify_instance(self, attributes=None):
        """
        modify the instance attributes such as name, description, password and host_name

        :type: list
        :param attributes: A list of dictionary of instance attributes which includes
            id, name, description, password and host_name
        :return: A list of the instance_ids modified
        """
        results = []
        if attributes:
            for attribute in attributes:
                if attribute:
                    params = {}
                    if 'id' in attribute:
                        self.build_list_params(params, attribute['id'], 'InstanceId')
                    if 'name' in attribute:
                        self.build_list_params(params, attribute['name'], 'InstanceName')
                    if 'description' in attribute:
                        self.build_list_params(params, attribute['description'], 'Description')
                    if 'password' in attribute:
                        self.build_list_params(params, attribute['password'], 'Password')
                    if 'host_name' in attribute:
                        self.build_list_params(params, attribute['host_name'], 'HostName')

                    result = self.get_status('ModifyInstanceAttribute', params)
                    results.append(result)
        return results

    # C2C : Method added to assign an existing Instance to an existing  security_group
    def join_security_group(self, instance_id, security_group_id):
        """
        The following method is used to assign an existing instance to an existing security group.
        An instance can be added to security group if, both are in same network (type)
        """
        params = {}
        results = []

        id_of_instance = instance_id[0]
        # Instace Id, which is to be added to a security group
        self.build_list_params(params, id_of_instance, 'InstanceId')

        # Security Group ID, an already existing security group, to which instance is added 
        self.build_list_params(params, security_group_id, 'SecurityGroupId')

        # Method Call, to perform adding action
        try:
            obtained_result = self.get_status('JoinSecurityGroup', params)
            results.append(obtained_result)             

        except Exception as ex:
            msg, stack = ex.args
            results.append("Join Security Group Error:" + str(msg) + " " +  str(stack))
         
        return results
   
    #C2C : Method added to Remove an existing Instance from an existing  security_group
    def leave_security_group(self, instance_id, security_group_id):
        """
        The following method is used to revoke an existing instance to an existing security group.
        """
        params = {}
        results = []

        id_of_instance = instance_id[0]

        # Instace Id, which is to be added to a security group
        self.build_list_params(params, id_of_instance, 'InstanceId')

        # Security Group ID, an already existing security group, to which instance is added 
        self.build_list_params(params, security_group_id, 'SecurityGroupId')

        # Method Call, to perform adding action
        try:
            obtained_result = self.get_status('LeaveSecurityGroup', params)
            results.append(obtained_result)             

        except Exception as ex:
            msg, stack = ex.args
            results.append("Join Security Group Error:" + str(msg) + " " + str(stack))
         
        return results
              
    # C2C : method added to querying instance status
    def querying_instance(self, region_id, zone_id=None, page_number=None, page_size=None):  
        params = {}
        results = []  

        self.build_list_params(params, region_id, 'RegionId')
        if zone_id:
            self.build_list_params(params, zone_id, 'ZoneId')
        if page_number:
            self.build_list_params(params, page_number, 'PageNumber')
        if page_size:
            self.build_list_params(params, page_size, 'PageSize')

        try:
            results = self.get_status('DescribeInstanceStatus', params)    
        except Exception as ex:
            msg, stack = ex.args
            results.append("Querying Instance Status error:" + str(msg) + " " + str(stack))  

        return results


    
    #C2C : method for create disk
    def create_disk(self, region_id, zone_id, disk_name=None, description=None, disk_category=None, size=None, instance_tags=None, ids=None, snapshot=None, count=None):  
        params = {}
        results = []  
        #Region
        self.build_list_params(params, region_id, 'RegionId')
        #Zone Id
        self.build_list_params(params, zone_id, 'ZoneId')
        #DiskName
        if disk_name:
            self.build_list_params(params, disk_name, 'DiskName')
        #Description of disk
        if description:
            self.build_list_params(params, description, 'Description')
        #Disk Category
        if disk_category:
            self.build_list_params(params, disk_category, 'DiskCategory')
        #Size of Disk
        if size:
            self.build_list_params(params, size, 'Size') 
        # Disk Tags
        tagno = 1
        if instance_tags:
            for instance_tag in instance_tags:
                if instance_tag:
                    if 'tag_key' in instance_tag:
                        self.build_list_params(params, instance_tag[
                            'tag_key'], 'Tag' + str(tagno) + 'Key')
                    if 'tag_value' in instance_tag:
                        self.build_list_params(params, instance_tag[
                            'tag_value'], 'Tag' + str(tagno) + 'Value')
                    tagno = tagno + 1       
        # Client Token
        if ids:
            if len(ids) == count:
                self.build_list_params(params, ids, 'ClientToken')
        #Snapshot Id
        if snapshot:
            self.build_list_params(params, snapshot, 'SnapshotId')

        try:
            results = self.get_status('CreateDisk', params)    
        except Exception as ex:
            msg, stack = ex.args
            results.append("Create Disk  error:" + str(msg) + " " + str(stack))  

        return results


     # C2C: Method added to querying Security Group List
    def querying_securitygrouplist(self, region_id, vpc_id=None, group_id=None):
        """
        Querying Security Group List returns the basic information about all
              user-defined security groups.

        :type region: dict
        :param region: The instance’s Region ID

        :type  vpc_id: dict
        :param vpc_id: ID of a vpc to which an security group belongs. If it is
            null, a vpc is selected by the system

        :type group_id: dict
        :param page_number: Provides a list of security groups ids.

        :return: A list of the total number of security groups, region ID of the security group,
                 the ID of the VPC to which the security group belongs

                """

        params = {}
        results = []

        self.build_list_params(params, region_id, 'RegionId')
        if vpc_id:
            self.build_list_params(params, vpc_id, 'VpcId')
        if group_id:
            self.build_list_params(params, group_id, 'SecurityGroupIds')


        try:
            obtained_result = self.get_status('DescribeSecurityGroups', params)
            results.append(obtained_result)
        except Exception as ex:
            msg, stack = ex.args
            results.append("Querying Security Group List error:" + str(msg) + " " + str(stack))

        return results

    #C2C : method for attaching disk
    def attach_disk_to_instance(self, disk_id, instance_id, region_id = None, device = None, delete_with_instance = None):
        """
        Method to attach a disk to instance

        """
        params = {}
        results = []

        id_of_instance = instance_id[0]
        # Instace Id, which is to be added to a security group
        self.build_list_params(params, id_of_instance, 'InstanceId')

        # Disk Id, the diskid to be mapped
        self.build_list_params(params, disk_id, 'DiskId')

        # Device 
        if device:
            self.build_list_params(params, device, 'Device')

        # Disk Id, the diskid to be mapped
        if delete_with_instance:
            self.build_list_params(params, delete_with_instance, 'DeleteWithInstance')

        # Disk Id, the diskid to be mapped
        if region_id:
            self.build_list_params(params, region_id, 'RegionId')


        # Method Call, to perform adding action
        try:
            obtained_result = self.get_status('AttachDisk', params)
            results.append(obtained_result)             

        except Exception as ex:
            msg, stack = ex.args
            results.append("Attach Disk to Instance Error:" + str(msg) + " " +  str(stack))
         
        return results

    #C2C : method for delete Security Group (method do not required group Id for deletion)

    def delete_security_group(self,region_id):
        """
        This method Internaly call DescribeSecurityGroups methods to get all running instances inside security groups
        """
        #call DescribeSecurityGroups method to get response for all running
        #instances
        params = {}
        results = []
        if region_id:
            self.build_list_params(params, region_id, 'RegionId')
        else:
            return results.append("RegionId is Required..!!")
        #hold response of DescribeSecurityGroups
        try:
            jsonObj = ''
            response = self.get_status('DescribeSecurityGroups',params)
            totalInstanceCt = 0
            if len(response) > 0:
                # convert response into json object
                jsonObj = json.loads(response)
                totalInstanceCt = jsonObj['TotalCount']


            if  totalInstanceCt > 0:
                for x in jsonObj['SecurityGroups']['SecurityGroup']:
                    SecurityGroupId = ''
                    AvailableInstanceAmount = 0
                    SecurityGroupId = (x['SecurityGroupId'])
                    AvailableInstanceAmount = (x['AvailableInstanceAmount'])
                    # check point : if their is no running instance inside
                    # security group then call delete security group method
                    if  AvailableInstanceAmount == 1000:
                        params1 = {}
                        self.build_list_params(params1, SecurityGroupId, 'SecurityGroupId')
                        delresponse = self.get_status('DeleteSecurityGroup',params1)
                        if delresponse=='success':
                           results.append('Security group deleted successfully..!! for region '+ str(region_id))
            else:
                results.append('No Security group found.!! for region '+ str(region_id))
        except Exception as ex:
            msg, stack = ex.args
            results.append("Delete Security Group Error:" + str(msg) + " " + str(stack))
        return results

    #C2C : method to delete security group by passing group Id
    def delete_security_groupById(self,region_id,Security_grpId):
        """
        This method used to delete security Group by passing Security group Id
        :param Security_grpId:
        :return:
        """

        result=[]
        param={}
        #Pass Region Id
        if region_id:
            self.build_list_params(param,region_id,'RegionId')
        else:
            return result.append("RegionId is required..!!")
        #Pass Security Group Id
        if Security_grpId:
            self.build_list_params(param,Security_grpId,'SecurityGroupId')
        else:
            return result.append("SecurityGroupId is required..!!")


        try:
            jsonObj = ''
            response = self.get_status('DescribeSecurityGroups', param)
            totalInstanceCt = 0
            if len(response) > 0:
                # convert response into json object
                jsonObj = json.loads(response)
                totalInstanceCt = jsonObj['TotalCount']

            if totalInstanceCt > 0:
                response=self.get_status('DeleteSecurityGroup',param)
                if response=='success':
                    result.append('Security Group deleted Successfully..!!')
            else:
                result.append('SecurityGroupId : '+str(Security_grpId) + ' Not found in region '+ str(region_id) )

        except Exception as ex:
            msg, stack = ex.args
            result.append("Delete Security Group Error: " + str(msg) + " " + str(stack))
        return result
