# coding:utf-8
import os
import sys
import logging
from functools import wraps
from logging import handlers

# 设置core日志
logger = logging.getLogger(__package__)
# logger.setLevel(logging.INFO)
# @20201108增加打印进程ID和线程ID
formatter = logging.Formatter('%(asctime)s - %(levelname)s - 进程%(process)d:线程%(thread)d - %(filename)s:%(funcName)s:%(lineno)d: %(message)s')


def init_logger(debug: bool, package: str, level: int = logging.INFO) -> None:
    # 支持打印level可配置
    logger.setLevel(level)
    # Debug模式不输出日志文件
    if debug:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(fmt=formatter)
        logger.addHandler(console_handler)
    else:
        # log文件路径需要在Dockerfile中mkdir -p /var/${GROUP}/${PROJECT}/app 的路径下
        if not os.path.exists(os.path.join('log')):
            os.mkdir(os.path.join('log'))
        file_handler = handlers.TimedRotatingFileHandler(filename=os.path.join('log', '%s.log' % package), when='midnight', encoding='utf-8')
        file_handler.setFormatter(fmt=formatter)
        logger.addHandler(file_handler)


def log(func):
    """
    :param func:
    :return:
    """
    @wraps(func)
    def function_log(*args, **kwargs):
        """
        :return:
        """
        logger.info("%s(%r | %r)", func.__name__, args[1:].__str__(), kwargs.__str__())
        result = func(*args, **kwargs)

        # 要求这里返回的都是dict
        # try:
        #     logger.info("%s = %s(%r | %r)", result.__str__(), func.__name__, args[1:].__str__(), kwargs.__str__())
        # except Exception as e:
        #     logger.error(e)

        return result
    return function_log


def print_box(message: str):
    return """
=================================================================
%s
=================================================================
    """ % message
