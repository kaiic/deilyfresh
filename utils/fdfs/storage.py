from django.core.files.storage import Storage
from fdfs_client.client import *
from django.conf import settings

class FDFSStorage(Storage):
    '''fdfs dfs文件存储类'''
    def __init__(self,client_conf=None,base_url=None):
        '''初始化'''
        if client_conf is None:
            # FDFS_CLIENT_CONF = './utils/fdfs/client.conf'
            client_conf = settings.FDFS_CLIENT_CONF
        self.client_conf = client_conf

        if base_url is None:
            # FDFS_URL = 'http://198.168.0.236:8888/'
            base_url = settings.FDFS_URL
        self.base_url = base_url

    def _open(self,name,mode='rb'):
        '''打开文件时使用'''
        pass

    def _save(self,name,content):
        '''保存文件时使用'''
        # name:是保存文件的名字
        # content:包含上传文件内容的File对象

        # 创建一个Fdfs_client对象
        trackers = get_tracker_conf(self.client_conf)
        client = Fdfs_client(trackers)
        
        # 上传文件到fast dfs
        res = client.upload_by_buffer(content.read())
        # 返回的是字典
        # dict
        # {
        #     'Group name': group_name,
        #     'Remote file_id': remote_file_id,
        #     'Status': 'Upload successed.',
        #     'Local file name': local_file_name,
        #     'Uploaded size': upload_size,
        #     'Storage IP': storage_ip
        # }

        if res.get('Status') != 'Upload successed.':
            # 上传失败,抛出异常
            raise Exception('上传文件到FSAT dfs失败')

        # 获取返回的文件id
        filename = res.get('Remote file_id')
        #只能返回str类型, filename为bytes类型(需要转换类型，不然会报错)
        filename = filename.decode()

        return filename

    def exists(self, name):
        '''django判断文件名是否可用'''
        # True:名称在文件系统中存在，不可用
        # False：名称可用于新文件
        return False

    def url(self, name):
        '''返回访问文件url路径'''
        return self.base_url+ name