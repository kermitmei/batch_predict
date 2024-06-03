from starlette.config import Config as StarletteConfig
from starlette.datastructures import Secret


class Config(StarletteConfig):
    DEBUG: bool = False

    """
    CRITICAL = 50
    FATAL = CRITICAL
    ERROR = 40
    WARNING = 30
    WARN = WARNING
    INFO = 20
    DEBUG = 10
    NOTSET = 0
    """
    LOGGER_LEVEL = 10
    LOGGER_PATH = '/tmp/guoxin'

    MAX_CONNECTIONS_COUNT: int = 10
    MIN_CONNECTIONS_COUNT: int = 10
    SECRET_KEY: Secret = 'fastapi'

    # 工作进程
    WORKERS = 1

    SERVICE = {
        'host': "0.0.0.0",
        'port': 5012
    }

    # LLM配置
    LLM_CONFIG = {
        'class': 'ChatGLM3',
        'pretrained_model_path': '/var/llm/chatglm3-6b-32k',
        'cuda_devices': '0'
    }

    # 配置中心
    NACOS_CONFIG = {
        'host': '192.168.1.20',
        'port': 8848,
        'namespace': 'public',
        'service': {
            'name': 'chatglm3-6b-32k',
            'ip': '192.168.31.136',
            'port': 8000,
            'cluster_name': None,
            'weight': 1.0,
            'metadata': {'gpu': 0.0, 'memory': 0.0},
            'enable': True,
            'healthy': True,
            'ephemeral': False,
            'group_name': 'DEFAULT_GROUP'
        }
    }
