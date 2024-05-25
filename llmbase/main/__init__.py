from contextlib import asynccontextmanager
from datetime import datetime

import nacos
from fastapi import FastAPI, Request
from starlette.middleware.cors import CORSMiddleware

from llmbase.main.common.god import cosmos
from llmbase.main.common.tool.logger import init_logger, logger
from llmbase.main.routers import openai


@asynccontextmanager
async def lifespan(app: FastAPI):
    # app启动
    yield
    # app关闭


def get_asgi_app(config) -> FastAPI:
    app = FastAPI(debug=config.DEBUG, lifespan=lifespan)

    # 保存全局配置到全局变量
    cosmos.config = config
    # 日志
    init_logger(debug=config.DEBUG, package=__package__, level=config.LOGGER_LEVEL)

    logger.debug('这是debug消息')

    """
    支持跨域访问
    """
    init_cors(app=app)
    """
    绑定路由
    """
    __routers = [
        openai.router,
    ]

    for __router in __routers:
        app.include_router(__router)

    # 预训练大模型
    try:
        from llmbase.main.llm import LLM
        _llm_class = LLM.get_pretrained_class(llm_config=config.LLM_CONFIG)
        cosmos.llm = _llm_class(pretrained_model_name_or_path=config.LLM_CONFIG.get('pretrained_model_path'),
                                embedding_model_path=config.LLM_CONFIG.get('embedding_model_path'),
                                cuda_devices=config.LLM_CONFIG.get('cuda_devices'))
        cosmos.nacos_client = nacos.NacosClient(server_addresses='%s:%s' % (config.NACOS_CONFIG.get('host'),
                                                                            config.NACOS_CONFIG.get('port')),
                                                namespace=config.NACOS_CONFIG.get('namespace'))
        # [服务提供方]注册服务
        _service_config = config.NACOS_CONFIG.get('service')
        cosmos.nacos_client.add_naming_instance(service_name=_service_config.get('name'),
                                                ip=_service_config.get('ip'),
                                                port=_service_config.get('port'),
                                                weight=_service_config.get('weight'),
                                                metadata=_service_config.get('metadata'),
                                                enable=_service_config.get('enable'),
                                                ephemeral=_service_config.get('ephemeral'),
                                                group_name=_service_config.get('group_name'),
                                                healthy=_service_config.get('healthy'))
    except Exception as e:
        logger.error(e)

    @app.middleware('http')
    async def _middleware(request: Request, call_next):
        """
        中间件处理请求和开头和结束
        和请求的响应处理不是一个线程
        :param request:
        :param call_next:
        :return:
        """
        # print('before request')
        # print(f'线程id: {threading.current_thread().ident}, request:{request}')
        """
        request的修改无法传递到之后的流程, 只能修改request内部的对象
        """
        start_time = datetime.now()
        # request.app.db = cosmos.db_session()
        _response = await call_next(request)
        # print('after request')
        # print(f'线程id: {threading.current_thread().ident}, request:{request}')
        # cosmos.db_session.remove()

        end_time = datetime.now()
        logger.info(
            f"{_response.status_code} {request.client.host} {request.method} {request.url} {end_time - start_time}")
        return _response

    return app


def init_cors(app: FastAPI) -> None:
    """
    Cross-Origin Resource Sharing
    跨域访问
    """
    origins = [
        # "http://localhost.tiangolo.com",
        # "https://localhost.tiangolo.com",
        # "http://localhost",
        # "http://localhost:8080",
        "*"
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
