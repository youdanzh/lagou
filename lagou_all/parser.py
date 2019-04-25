from urllib.parse import urljoin, urlparse

import moment
import numpy
from bs4 import BeautifulSoup as bs4
from common import checkTimes, addsucess, addfailed
from log import success, info, error
from pyquery import PyQuery as jq
from exporter import CreateJson
from conf import config
import moment


class Parser:
    @staticmethod
    def get_classifications(resp):
        """
            解析全部分类
        """
        bs4_data = bs4(resp.text, "html")  # 将内容转换为bs4对象
        for target in bs4_data.select(".menu_box [data-lg-tj-id]"): # 根据相应css路径取到target
            datas = target.attrs # 获取target的全部属性键值对
            datas.update({"name": target.string}) 
            yield datas # 生成器方式返回单个数据

    @staticmethod
    def get_max_pages(resp):
        """
            解析最大页数
        """
        bs4_data = bs4(resp.text, "html") # 将内容转换为bs4对象
        try:
            return int(
                bs4_data.select_one(
                    "#s_position_list > div.item_con_pager > div > a:nth-child(5)"
                )["data-index"]
            ) # 根据css路径取到范围最大页数
        except Exception as e:
            error(f"get_max_pages: {e}") # 打印错误日志
            addfailed() # 增加一次错误
            return 0 # 默认返回0

    @staticmethod
    def get_positions(resp):
        jq_data = jq(resp.text) # 将内容转换为pyquery对象
        tmp_list = []
        for item in jq_data(".con_list_item").items(): # 根据css路径取到每项
            try:
                detail = {
                    "positionid": int(item.attr("data-positionid")), 
                    "salary": item.attr("data-salary"),
                    "company": item.attr("data-company"),
                    "positionname": item.attr("data-positionname"),
                    "companyid": int(item.attr("data-companyid")),
                    "worktags": item(".list_item_bot>.li_b_l").text().split(),
                    "othertags": item(".list_item_bot>.li_b_r")
                    .text()
                    .replace("“", "")
                    .replace("，", " ")
                    .split(),
                    "industry": item(".industry").text().replace(" ", "").split("/"),
                    "outtime": moment.date(
                        item(".format-time").text().replace("发布", "")
                    ).format("YYYY-MM-DD HH:mm:ss"), # 将不规则的时间转换为标准格式
                }
                tmp_list.append(detail)
            except Exception as e:
                error(f"positions_error: {e}")

        return tmp_list # 返回每页数据
