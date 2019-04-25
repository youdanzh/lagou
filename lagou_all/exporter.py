import json

import pandas

from log import success
from common import checkTimes

def CreateJson(datas, filename="res.json"):
    """
        导出json
    """
    with checkTimes():
        with open(filename, "w") as f:
            f.write(json.dumps(datas, ensure_ascii=False, indent=4))
            success(f"Saved {filename}")
