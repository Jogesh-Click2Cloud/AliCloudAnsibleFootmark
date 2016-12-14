#
import logging
import logging.config
import os

from footmark.pyami.config import Config, FootmarkLoggingConfig, DefaultLoggingConfig

__version__ = '1.0.6'
Version = __version__  # for backware compatibility

def init_logging():
    try:
        Config().init_config()
        try:
            logging.config.fileConfig(os.path.expanduser(FootmarkLoggingConfig))
        except:
            logging.config.dictConfig(DefaultLoggingConfig)
    except:
        pass

init_logging()
log = logging.getLogger('footmark')

def connect_ecs(acs_access_key_id=None, acs_secret_access_key=None, **kwargs):
    """
    :type acs_access_key_id: string
    :param acs_access_key_id: Your AWS Access Key ID

    :type acs_secret_access_key: string
    :param acs_secret_access_key: Your AWS Secret Access Key

    :rtype: :class:`footmark.ecs.connection.ECSConnection`
    :return: A connection to Amazon's ECS
    """
    from footmark.ecs.connection import ECSConnection
    return ECSConnection(acs_access_key_id, acs_secret_access_key, **kwargs)

#acs_access_key_id = "LTAIV7yukr6Csf14"
#acs_secret_access_key = "it9TEJcJvnDyL5uB830fx1BQwzdNdd"
#region_id = "ap-southeast-1"
#conn = connect_ecs(acs_access_key_id,acs_secret_access_key,region=region_id)
#attributes = [{"id":"i-t4ninnyuqc4l495f123t","name":"new","description":"asdfg","password":"Pass","host_name":"zxc"}]
#conn.modify_instance(attributes)

#acs_access_key_id = "LTAIV7yukr6Csf14"
#acs_secret_access_key = "it9TEJcJvnDyL5uB830fx1BQwzdNdd"
#region_id = "cn-beijing"
#conn = connect_ecs(acs_access_key_id,acs_secret_access_key,region=region_id)
#vpc_id = ["vpc-2zease6hez9iwat8kfpvn"]
#conn.querying_securitygrouplist(vpc_id)

#acs_access_key_id = "LTAIV7yukr6Csf14"
#acs_secret_access_key = "it9TEJcJvnDyL5uB830fx1BQwzdNdd"
#region_id = "cn-beijing"
#conn = connect_ecs(acs_access_key_id,acs_secret_access_key,region=region_id)
#zone_id,size,description = ["cn-beijing-b", "40","desc"]
#conn.create_disk(region_id=region_id, zone_id=zone_id, disk_name=None, description=description, disk_category=None, size=size, instance_tags=None, ids=None, snapshot=None)


