import importlib

from core.main import logger


class LLM(object):

    @staticmethod
    def get_pretrained_class(llm_config: dict):
        if llm_config is None or llm_config.get('class') is None:
            logger.error('预训练大模型初始化错误')
            raise Exception("PRETRAINED MODEL ERROR")
        module = importlib.import_module('core.main.llm')
        cls = getattr(module, llm_config.get('class'))
        return cls
