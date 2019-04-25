import asks
import trio
from conf import config
from parser import Parser
from urllib.parse import quote
from log import info, success, error, warning
from common import checkTimes, addsucess, addfailed, update_city
from exporter import CreateJson
from models import lagou
from getcookie import update_cookie_chrome


asks.init("trio")


class LaGou(object):
    def __init__(self):
        super(LaGou, self).__init__()
        self.main_url = "https://www.lagou.com" # 拉钩主页
        self.target_url = (
            "https://www.lagou.com/jobs/list_{}?px=default&city={}#filterBox"
        ) # 拉钩单页模板
        self.limit = trio.CapacityLimiter(config.maxConnections * 10) # 请求并发限制池为并发数的10倍
        self.result = {} # 数据存储
        self.page_list = {}
        self.citys = ["全国", "北京", "上海", "杭州", "广州", "武汉", "深圳", "成都", "江苏"]

    async def __init_mount(self):
        """
            初始化异步session、配置session模拟头
        """
        self.AsyncSession = asks.Session(connections=config.maxConnections) # 配置AsyncSession 并设定最大并发数config.maxConnections
        self.AsyncSession.headers = config.fakeHeader # 配置配置AsyncSession的header
        

    def __init_cookie(self):
        """
            初始化cookie
        """
        self.cookies = update_cookie_chrome(
            [self.main_url, self.target_url.format("Java", "杭州")],
            headless=True,
            item_sleep=0,
            sleep=0,
        ) # 通过模拟浏览器访问如上链接来或许所需的cookie
        info(self.cookies) # 打印cookie内容

    def update_city(self, city):
        """
            将city推入cookie并应用于请求
        """
        self.cookies["index_location_city"] = quote(city) # 将city cookie推入cookies
        update_city(city) # 更新当前日志打印首部为当前city

    async def get_classifications(self):
        """
            获取当前全部分类
        """
        url = self.main_url 
        warning(f"fetching {url}...") # 打印当前访问url
        try:
            resp = await self.AsyncSession.get(url) # 请求该url
            self.targets = list(Parser.get_classifications(resp)) # 通过处理取得全部分类
            success(f"{url}: targets[{len(self.targets)}]") # 打印当前全部分类长度
            for item in self.targets: # 迭代每一个类型
                item["positions"] = [] # 设定positions 为空列表
                item["key"] = item["href"].split("/")[-1] # 根据/切分href内容取到最后一位作为key值
            success(self.targets[0]) # 打印一条案例结果
            addsucess() # 增加一次成功
        except Exception as e:
            error(f"{url}: {e}") # 打印错误日志
            addfailed() # 如果失败了就增加一次失败

    async def get_singel(self, url, key, city, for_max=False):
        """
            获取单个数据，参数包裹默认模板url,所使用键值，所爬城市，是否为取到最大页数的请求
        """
        async with self.limit: # 限制全局并发
            warning(url) # 打印访问警告
            try:
                resp = await self.AsyncSession.get(url, cookies=self.cookies) # 附带cookie并发送异步请求
                if resp.status_code == 404: # 如果状态码为404
                    return # 则跳过
                if for_max: # 如果这个请求是为了获取某某城市的某类型的最大页数
                    self.page_list[f"{key}_{city}"] = Parser.get_max_pages(resp) # 则取到最大页数并丢入page_list
                for item in Parser.get_positions(resp): # 取到当前页的所有招聘卡片信息
                    pid = item["positionid"] # 取数positionid赋值给pid
                    item["city"] = city # 将city推入该item内
                    if pid not in self.result: # 判断是否重复爬取
                        success(f'{item["positionname"]}') # 打印当前的职位名称
                        lagou(**item).save() # 通过mongoengine存入mongodb
                        self.result[pid] = item # 同时也将数据存入result作为临时debug调试数据
                        addsucess() # 增加一条成功
            except Exception as e:
                addfailed() # 增加一条失败
                error(f"get_single_error: {e}") #打印当前错误信息

    async def get_max_pages(self):
        """
            并发获取最大页数
        """
        info("get all max pages") # 打印当前事件目的
        for city in self.citys: # 迭代城市
            self.update_city(city) #  将city推入cookie并应用于请求 
            async with trio.open_nursery() as nursery: # 开启并发管理器
                for item in self.targets: # 迭代所有职位类型
                    nursery.start_soon( 
                        self.get_singel, item["href"], item["key"], city, True
                    ) # 启动一个并发任务

    async def get_all_datas(self):
        """
            获取全部城市数据
        """
        info("get all info  datas") # 打印当前事件目的
        for city in self.citys: # 迭代城市
            self.update_city(city) #  将city推入cookie并应用于请求 
            async with trio.open_nursery() as nursery: # 开启并发管理器
                for item in self.targets:  # 迭代所有职位类型
                    for page in range(1, self.page_list[f"{item['key']}_{city}"]):
                        nursery.start_soon(
                            self.get_singel,
                            item["href"] + f"{page}/",
                            item["key"],
                            city,
                        ) # 启动一个并发任务

    def run(self):
        """
            主运行逻辑
        """
        self.__init_cookie() # 初始化应用cookie，解决部分jscookie无法自生成
        trio.run(self.__init_mount) # 初始化session
        with checkTimes(): # 记录下级执行所花时间 
            try:
                trio.run(self.get_classifications) # 获取所有职位分类
                trio.run(self.get_max_pages) # 获取所有城市的所有职位的最大页数
                trio.run(self.get_all_datas) # 数去所有数据
            finally:
                CreateJson(self.targets, "lagou_targets.json") # 临时存储所有职位分类数据
                CreateJson(self.result, "lagou_result.json") # 临时存储所有职位数据


if __name__ == "__main__": 
    with checkTimes(): # 记录下级执行所花时间 
        try:
            LaGou().run() # 实例化一个LaGou类并执行run
        except KeyboardInterrupt: # 如果为Ctrl+C退出则不打印错误
            pass
        except Exception as e: # 如果为其他错误 ，则打印错误
            raise e
        finally:
            info("finished") # 打印结束
