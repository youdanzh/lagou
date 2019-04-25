import copy
import os
import time
from contextlib import contextmanager

from conf import config
from log import info


@contextmanager
def checkTimes(level=3):
    """
        检查运行时间
    """
    timeStart = time.time()
    yield # 实际运行内容
    info(f"cost times: {round(time.time()-timeStart,level)}s") # 计算与一开始时间的差距，保留2位小数

def addsucess():
    """
        添加成功
    """
    config.status["success"] += 1


def addfailed():
    """
        添加失败
    """
    config.status["failed"] += 1

def update_city(city):
    """
        更新当前爬行城市
    """
    config.status["city"] = city