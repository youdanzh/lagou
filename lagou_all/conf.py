class config:
    name = "lagou" # 项目名称
    maxConnections = 5 # 并发数量
    fakeHeader = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
        "cache-control": "max-age=0",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_3) AppleWebKit/537.36(KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36",
    } # 伪造header头
    status = {"success": 0, "failed": 0, "total": 0, "updated": 0, "city": ""} # 默认打印记录
    defaultstatus = {"success": 0, "failed": 0, "total": 0, "updated": 0, "city": ""}
    mongoURI = "mongodb://localhost:27017/work" # mongo链接位置


conf = config
