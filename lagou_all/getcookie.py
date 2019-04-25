from selenium import webdriver
import time


def update_cookie_chrome(targets, proxy=None, headless=True, item_sleep=0, sleep=0):
    """
        通过无头浏览器获取cookie
    """

    driver = None # 默认driver为空
    try:
        options = webdriver.ChromeOptions()
        if proxy: # 判断是否需要代理
            options.add_argument(f"--proxy-server={proxy}") 
        if headless: # 判断是否需要使用无头模式
            options.add_argument("headless")
        driver = webdriver.Chrome(chrome_options=options) # 将配置应用于webdriver
        driver.set_page_load_timeout(30) # 默认超时等待30秒
        for target in targets: # 迭代需要访问的页码
            driver.get(target) # 访问
            driver.implicitly_wait(30) # 智能等待30秒，提前加载完则提前结束
            time.sleep(item_sleep) # 每个目标访问等待时间
        time.sleep(sleep) # 全局等待时间
        return {i["name"]: i["value"] for i in driver.get_cookies()} # 返回全部cookie
    except Exception as e:
        print(e)
    finally:
        if driver:
            driver.close()
