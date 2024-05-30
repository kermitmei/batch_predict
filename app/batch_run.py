# import config   # 服务器运行
import uvicorn
from llmbase.main import get_asgi_app
from app import config
from llmbase.main.common.god import cosmos

app = get_asgi_app(config=config.Config)

if __name__ == '__main__':
    _host = cosmos.config.SERVICE.get("host")
    if _host is None or len(_host) == 0:
        _host = '0.0.0.0'
    _port = cosmos.config.SERVICE.get("port")
    if _port is None or _port == 0:
        _port = 5012
    uvicorn.run(app=app, host=_host, port=_port, workers=config.Config.WORKERS, reload=False)
