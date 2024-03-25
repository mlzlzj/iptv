import time
import os
import re
import base64
import requests
import threading
from queue import Queue

# 线程安全的队列，用于存储下载任务
task_queue = Queue()

headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'}

#urls = ['shenzhen','dongguan','jiangmen','huizhou','meizhou','jieyang','shantou','shanwei','zhuhai','foshan','zhongshan','guangzhou'] #广东省
urls = ['changsha','zhuzhou','hengyang','yueyang','yiyang','zhuzhou','huaihua','loudi'] #湖南省


results = []
channel = []
urls_all = []
resultsx = []
error_channels = []

for url in urls:
    url_0 = str(base64.b64encode((f'"Server: udpxy" && city="{url}" && org="Chinanet"').encode("utf-8")), "utf-8")
    url_64 =f'https://fofa.info/result?qbase64={url_0}'
    print(url_64)
    response = requests.get(url_64, headers=headers, timeout = 15)
    page_content = response.text
    pattern = r'href="(http://\d+\.\d+\.\d+\.\d+:\d+)"'
    page_urls = re.findall(pattern, page_content)
    for urlx in page_urls:
        try:
            response = requests.get(url=urlx+'/status', timeout=1)
            response.raise_for_status()  # 返回状态码不是200异常
            page_content = response.text
            pattern = r'class="proctabl"'
            page_proctabl = re.findall(pattern, page_content)
            if page_proctabl:
                urls_all.append(urlx)
                print(f"{urlx} 可以访问")
            else:
                print(f"{urlx} 访问失败")

        except requests.RequestException as e:
            print(f"{urlx} 访问失败")
            pass

urls_all = set(urls_all)  # 去重得到唯一的URL列表
for urlx in urls_all:
    channel = [f'{name},{url.replace("http://8.8.8.8:8", urlx)}' for name, url in [line.strip().split(',') for line in open("hunan.txt", 'r', encoding='utf-8')]]
    results.extend(channel)

results = sorted(results)

with open("itv.txt", 'w', encoding='utf-8') as file:
    for result in results:
        file.write(result + "\n")
        print(result)

# 定义工作线程函数
def worker():
    while True:
        result = task_queue.get()
        channel_name, channel_url = result.split(',', 1)
        try:
            response = requests.get(channel_url, stream=True, timeout=3)
            if response.status_code == 200:
                resultsx.append(result)
                numberx = (len(resultsx) + len(error_channels)) / len(results) * 100
                print(f"可用频道：{len(resultsx)} , 不可用频道：{len(error_channels)} 个 , 总频道：{len(results)} 个 ,总进度：{numberx:.2f} %。")
            else:
                error_channels.append(result)
                numberx = (len(resultsx) + len(error_channels)) / len(results) * 100
                print(f"可用频道：{len(resultsx)} 个 , 不可用频道：{len(error_channels)} , 总频道：{len(results)} 个 ,总进度：{numberx:.2f} %。")
        except:
            error_channels.append(result)
            numberx = (len(resultsx) + len(error_channels)) / len(results) * 100
            print(f"可用频道：{len(resultsx)} 个 , 不可用频道：{len(error_channels)} 个 , 总频道：{len(results)} 个 ,总进度：{numberx:.2f} %。")

        # 标记任务完成
        task_queue.task_done()

# 创建多个工作线程
num_threads = 20
for _ in range(num_threads):
    t = threading.Thread(target=worker, daemon=True)
    t.start()

# 添加下载任务到队列
for result in results:
    task_queue.put(result)

# 等待所有任务完成
task_queue.join()

with open("itvlist.txt", 'w', encoding='utf-8') as file:
    for result in resultsx:
        file.write(result + "\n")
        print(result)
