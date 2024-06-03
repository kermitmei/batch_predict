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
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - 进程%(process)d:线程%(thread)d - %(filename)s:%(funcName)s:%(lineno)d: %(message)s')


# def init_logger(debug: bool, package: str, level: int = logging.INFO, logger_path=None) -> None:
#     # 支持打印level可配置
#     logger.setLevel(level)
#     # Debug模式不输出日志文件
#     if debug:
#         console_handler = logging.StreamHandler(sys.stdout)
#         console_handler.setFormatter(fmt=formatter)
#         logger.addHandler(console_handler)
#     else:
#         # log文件路径需要在Dockerfile中mkdir -p /var/${GROUP}/${PROJECT}/app 的路径下
#         _logger_path = logger_path or os.path.join('log', '%s.log' % package)
#         if not os.path.exists(os.path.join('log')):
#             os.mkdir(os.path.join('log'))
#         file_handler = handlers.TimedRotatingFileHandler(filename=os.path.join('log', '%s.log' % package), when='midnight', encoding='utf-8')
#         file_handler.setFormatter(fmt=formatter)
#         logger.addHandler(file_handler)


def init_logger(debug: bool, package: str, level: int = logging.INFO, logger_path: str = None) -> None:
    # 创建一个logger
    logger.setLevel(level)

    # Debug模式不输出日志文件
    if debug:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    else:
        # 如果logger_path为None或者为空字符串，使用当前目录
        if not logger_path or len(logger_path) == 0:
            logger_path = os.path.join(os.getcwd(), f"{package}.log")
        else:
            logger_path = os.path.join(logger_path, f"{package}.log")

        # 确保日志文件所在的目录存在
        os.makedirs(os.path.dirname(logger_path), exist_ok=True)

        # 创建并设置文件handler
        file_handler = logging.FileHandler(logger_path, encoding='utf-8')
        file_handler.setFormatter(formatter)
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
