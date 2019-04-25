import logging

from termcolor import colored

from conf import config


def makeStatus():
    return f"[{config.status['city']}] ✅:{colored(config.status['success'],'green')} 🚫:{colored(config.status['failed'],'red')}] " # 自定义输出内容

logging.basicConfig(format="[%(asctime)s]%(message)s", level=logging.INFO) # 配置标准日志格式
Loger = logging.getLogger(config.name) # 实例化一个日志器


def info(txt): 
    """
        打印常规信息，上色蓝色
    """
    return Loger.info(f"{ makeStatus()} {colored(txt, 'blue')}")


def success(txt):
    """
        打印成功信息，上色绿色
    """
    return Loger.info(f"{makeStatus()} {colored(txt, 'green')}")


def warning(txt):
    """
        打印警告信息，上色黄色
    """
    return Loger.info(f"{makeStatus()} {colored(txt, 'yellow')}")


def error(txt):
    """
        打印错误信息，上色红色
    """
    return Loger.info(f"{makeStatus()} {colored(txt, 'red')}")
