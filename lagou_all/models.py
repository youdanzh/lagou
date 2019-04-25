import datetime

from conf import config
from log import error, info, success, warning
from mongoengine import *

connect(host=config.mongoURI) # 与mongodb建立连接


class lagou(Document): # mongodb的数据模型
    positionid = IntField(unique=True) # 职位ID
    salary = StringField() # 薪水范围
    company = StringField() # 公司名称
    positionname = StringField() # 职位名称
    companyid = IntField() # 公司ID
    worktags = ListField() # 工作内容标签
    othertags = ListField() # 公司情况标签
    industry = ListField() # 公司情况标签2
    outtime = StringField() # 发布时间
    city = StringField() # 所在城市
    intime = DateTimeField(default=datetime.datetime.utcnow) # 数据插入时间
