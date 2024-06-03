# import config   # 服务器运行
import uvicorn
from llmbase.main import get_asgi_app
from app import config
from llmbase.main.common.god import cosmos

app = get_asgi_app(config=config.Config)

if __name__ == '__main__':
    _host = cosmos.config.SERVICE.get("host") or '0.0.0.0'
    _port = cosmos.config.SERVICE.get("port") or 5012
    uvicorn.run(app=app, host=_host, port=_port, workers=config.Config.WORKERS, reload=False)
