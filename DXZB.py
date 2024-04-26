import time
import os
import requests
import re
import threading
from queue import Queue
import eventlet
import base64
from datetime import datetime

#  获取远程直播源文件
url = "https://mirror.ghproxy.com/https://raw.githubusercontent.com/Fairy8o/IPTV/main/DIYP-v4.txt"
r = requests.get(url)
open('DIYP-v4.txt', 'wb').write(r.content)

keywords = ['凤凰卫视', '凤凰资讯', 'TVB翡翠', 'TVB明珠', 'TVB星河', 'J2', '无线', '有线', '天映', 'VIU', 'RTHK', 'HOY',
            '香港卫视','Viut']  # 需要提取的关键字列表
pattern = '|'.join(keywords)  # 创建正则表达式模式，匹配任意一个关键字
with open('DIYP-v4.txt', 'r', encoding='utf-8') as file, open('HK.txt', 'w', encoding='utf-8') as HK:
    HK.write('\n港澳频道,#genre#\n')
    for line in file:
        if re.search(pattern, line):  # 如果行中有任意关键字
            HK.write(line)  # 将该行写入输出文件

keywords = ['民视', '中视', '台视', '华视', '新闻台', '东森', '龙祥', '公视', '三立', '大爱', '年代新闻', '人间卫视',
            '人間', '大立']  # 需要提取的关键字列表
pattern = '|'.join(keywords)  # 创建正则表达式模式，匹配任意一个关键字
with open('DIYP-v4.txt', 'r', encoding='utf-8') as file, open('TW.txt', 'w', encoding='utf-8') as TW:
    TW.write('\n台湾频道,#genre#\n')
    for line in file:
        if re.search(pattern, line):  # 如果行中有任意关键字
            TW.write(line)  # 将该行写入输出文件

# 读取要合并的香港频道和台湾频道文件
file_contents = []
file_paths = ["HK.txt", "TW.txt"]  # 替换为实际的文件路径列表
for file_path in file_paths:
    with open(file_path, 'r', encoding="utf-8") as file:
        content = file.read()
        file_contents.append(content)
# 生成合并后的文件
with open("GAT.txt", "w", encoding="utf-8") as output:
    output.write('\n'.join(file_contents))


headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 '
                  'Safari/537.36'}

urls = []
shengshi_names = ["changsha", "henyang", "zhuzhou", "loudi", "yueyang", "chenzhou", "xiangtan",
                  "changde", "yiyang", "yongzhou", "huaihua", "zhangjiajie", "shaoyang", "xiangxi"]
for shengshi in shengshi_names:
    url = 'https://fofa.info/result?qbase64='
    # search_txt = f'\"ZHGXTV\"  && region=\"{shengshi}\"'  # 扫省
    search_txt = f'\"ZHGXTV\"  && City=\"{shengshi}\"'  # 扫城市用
    # 将字符串编码为字节流
    bytes_string = search_txt.encode('utf-8')
    # 使用 base64 进行编码
    search_txt = base64.b64encode(bytes_string).decode('utf-8')
    url += search_txt
    print(f"shengshi : {shengshi}，search_url : {url}")
    urls.append(url)

results = []

for url in urls:
    try:
        response = requests.get(url, headers=headers, timeout=15)
        page_content = response.text
        # 查找所有符合指定格式的网址
        pattern = r"http://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+"  # 设置匹配的格式，如http://8.8.8.8:8888
        urls_all = re.findall(pattern, page_content)
        # urls = list(set(urls_all))  # 去重得到唯一的URL列表
        urls = set(urls_all)  # 去重得到唯一的URL列表
        # 遍历网址列表，获取JSON文件并解析
        for url in urls:
            try:
                # 发送GET请求获取JSON文件，设置超时时间为0.5秒
                json_url = f'{url}/ZHGXTV/Public/json/live_interface.txt'
                response = requests.get(json_url, timeout=5)
                json_data = response.content.decode('utf-8')
                try:
                    # 按行分割数据
                    lines = json_data.split('\n')
                    for line in lines:
                        line = line.strip()
                        if line:
                            name, channel_url = line.split(',', 1)
                            urls = channel_url.split('/', 3)
                            url_data = json_url.split('/', 3)
                            if len(urls) >= 4:
                                urld = f"{urls[0]}//{url_data[2]}/{urls[3]}"
                            else:
                                urld = f"{urls[0]}//{url_data[2]}"
                            if name and urld:
                             # 删除特定文字
                                name = name.replace("中央", "CCTV")
                                name = name.replace("高清", "")
                                name = name.replace("HD", "")
                                name = name.replace("标清", "")
                                name = name.replace("超高", "")
                                name = name.replace("频道", "")
                                name = name.replace("-", "")
                                name = name.replace(" ", "")
                                name = name.replace("PLUS", "+")
                                name = name.replace("＋", "+")
                                name = name.replace("(", "")
                                name = name.replace(")", "")
                                name = name.replace("L", "")
                                name = name.replace("cctv", "CCTV")
                                name = re.sub(r"CCTV(\d+)台", r"CCTV\1", name)
                                name = name.replace("CCTV1综合", "CCTV1")
                                name = name.replace("CCTV2财经", "CCTV2")
                                name = name.replace("CCTV3综艺", "CCTV3")
                                name = name.replace("CCTV4国际", "CCTV4")
                                name = name.replace("CCTV4中文国际", "CCTV4")
                                name = name.replace("CCTV4欧洲", "CCTV4")
                                name = name.replace("CCTV5体育", "CCTV5")
                                name = name.replace("CCTV5+体育", "CCTV5+")
                                name = name.replace("CCTV6电影", "CCTV6")
                                name = name.replace("CCTV7军事", "CCTV7")
                                name = name.replace("CCTV7军农", "CCTV7")
                                name = name.replace("CCTV7农业", "CCTV7")
                                name = name.replace("CCTV7国防军事", "CCTV7")
                                name = name.replace("CCTV8电视剧", "CCTV8")
                                name = name.replace("CCTV8纪录", "CCTV9")
                                name = name.replace("CCTV9记录", "CCTV9")
                                name = name.replace("CCTV9纪录", "CCTV9")
                                name = name.replace("CCTV10科教", "CCTV10")
                                name = name.replace("CCTV11戏曲", "CCTV11")
                                name = name.replace("CCTV12社会与法", "CCTV12")
                                name = name.replace("CCTV13新闻", "CCTV13")
                                name = name.replace("CCTV新闻", "CCTV13")
                                name = name.replace("CCTV14少儿", "CCTV14")
                                name = name.replace("央视14少儿", "CCTV14")
                                name = name.replace("CCTV少儿超", "CCTV14")
                                name = name.replace("CCTV15音乐", "CCTV15")
                                name = name.replace("CCTV音乐", "CCTV15")
                                name = name.replace("CCTV16奥林匹克", "CCTV16")
                                name = name.replace("CCTV17农业农村", "CCTV17")
                                name = name.replace("CCTV17军农", "CCTV17")
                                name = name.replace("CCTV17农业", "CCTV17")
                                name = name.replace("CCTV5+体育赛视", "CCTV5+")
                                name = name.replace("CCTV5+赛视", "CCTV5+")
                                name = name.replace("CCTV5+体育赛事", "CCTV5+")
                                name = name.replace("CCTV5+赛事", "CCTV5+")
                                name = name.replace("CCTV5+体育", "CCTV5+")
                                name = name.replace("CCTV5赛事", "CCTV5+")
                                name = name.replace("CCTV4K测试）", "CCTV4")
                                name = name.replace("CCTV164K", "CCTV16")
                                name = name.replace("金鹰卡通卫视", "金鹰卡通")
                                name = name.replace("湖南金鹰卡通", "金鹰卡通")
                                name = name.replace("炫动卡通", "哈哈炫动")
                                name = name.replace("卡酷卡通", "卡酷少儿")
                                name = name.replace("卡酷动画", "卡酷少儿")
                                name = name.replace("BRTVKAKU少儿", "卡酷少儿")
                                name = name.replace("优曼卡通", "优漫卡通")
                                name = name.replace("优曼卡通", "优漫卡通")
                                name = name.replace("嘉佳卡通", "佳嘉卡通")
                                name = name.replace("卫视台", "卫视")
                                name = name.replace("湖南电视台", "湖南卫视")
                                name = name.replace("湖南教育电视台", "湖南教育")
                                name = name.replace("湖南教育台", "湖南教育")
                                name = name.replace("湖南爱晚", "湖南公共")
                                name = name.replace("影视剧", "影视")
                                if "udp://" not in urld:
                                    results.append(f"{name},{urld}")
                except:
                    continue
            except:
                continue
    except:
        continue

channels = []

for result in results:
    line = result.strip()
    if result:
        channel_name, channel_url = result.split(',')
        channels.append((channel_name, channel_url))
# 写入频道列表文件iptv.txt
with open("iptv.txt", 'w', encoding='utf-8') as file:
    for result in results:
        file.write(result + "\n")
        print(result)


def channel_key(channel_name):
    match = re.search(r'\d+', channel_name)
    if match:
        return int(match.group())
    else:
        return float('inf')  # 返回一个无穷大的数字作为关键字


# 对频道进行排序
results.sort(key=lambda x: channel_key(x[0]))

result_counter = 10  # 每个频道需要的个数

with open("iptvlist.txt", 'w', encoding='utf-8') as file:
    channel_counters = {}
    file.write('央视频道,#genre#\n')
    for result in results:
        channel_name, channel_url = result.split(',', 1)
        if 'CCTV' in channel_name:
            if channel_name in channel_counters:
                if channel_counters[channel_name] >= result_counter:
                    continue
                else:
                    file.write(f"{channel_name},{channel_url}\n")
                    channel_counters[channel_name] += 1
            else:
                file.write(f"{channel_name},{channel_url}\n")
                channel_counters[channel_name] = 1

    channel_counters = {}
    file.write('卫视频道,#genre#\n')
    for result in results:
        channel_name, channel_url = result.split(',', 1)
        if '卫视' in channel_name:
            if channel_name in channel_counters:
                if channel_counters[channel_name] >= result_counter:
                    continue
                else:
                    file.write(f"{channel_name},{channel_url}\n")
                    channel_counters[channel_name] += 1
            else:
                file.write(f"{channel_name},{channel_url}\n")
                channel_counters[channel_name] = 1

    channel_counters = {}
    file.write('湖南频道,#genre#\n')
    for result in results:
        channel_name, channel_url = result.split(',', 1)
        if '湖南' in channel_name or '长沙' in channel_name:
            if channel_name in channel_counters:
                if channel_counters[channel_name] >= result_counter:
                    continue
                else:
                    file.write(f"{channel_name},{channel_url}\n")
                    channel_counters[channel_name] += 1
            else:
                file.write(f"{channel_name},{channel_url}\n")
                channel_counters[channel_name] = 1

    channel_counters = {}
    file.write('其他频道,#genre#\n')
    for result in results:
        channel_name, channel_url = result.split(',',1)
        if 'CCTV' not in channel_name and '卫视' not in channel_name and '测试' not in channel_name and '湖南' not in channel_name and '长沙' not in channel_name:
            if channel_name in channel_counters:
                if channel_counters[channel_name] >= result_counter:
                    continue
                else:
                    file.write(f"{channel_name},{channel_url}\n")
                    channel_counters[channel_name] += 1
            else:
                file.write(f"{channel_name},{channel_url}\n")
                channel_counters[channel_name] = 1

# 合并所有的txt文件
file_contents = []
file_paths = ["iptvlist.txt", "GAT.txt", "zdy.txt"]  # 替换为实际的文件路径列表
for file_path in file_paths:
    with open(file_path, 'r', encoding="utf-8") as file:
        content = file.read()
        file_contents.append(content)

    # 写入合并后的txt文件
with open("iptv_list.txt", "w", encoding="utf-8") as output:
    output.write('\n'.join(file_contents))

    # 写入更新日期时间
    # file.write(f"{now_today}更新,#genre#\n")
    now = datetime.now()
    output.write(f"\n更新时间,#genre#\n")
    output.write(f"{now.strftime("%Y-%m-%d")},url\n")
    output.write(f"{now.strftime("%H:%M:%S")},url\n")

os.remove("DIYP-v4.txt")
os.remove("iptv.txt")
os.remove("HK.txt")
os.remove("TW.txt")
os.remove("GAT.txt")
os.remove("iptvlist.txt")

print("iptv_list.txt频道文件生成完毕！")

# 将txt文件转换为m3u文件
def txt_to_m3u(input_file, output_file):
    # 读取txt文件内容
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 打开m3u文件并写入内容
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('#EXTM3U\n')

        # 初始化genre变量
        genre = ''

        # 遍历txt文件内容
        for line in lines:
            line = line.strip()
            if "," in line: # 防止文件里面缺失“,”号报错
            # if line:
                # 检查是否是genre行
                channel_name, channel_url = line.split(',', 1)
                if channel_url == '#genre#':
                    genre = channel_name
                    print(genre)
                else:
                    # 将频道信息写入m3u文件
                    f.write(f'#EXTINF:-1 group-title="{genre}",{channel_name}\n')
                    f.write(f'{channel_url}\n')


# 运行实例
txt_to_m3u('iptv_list.txt', 'iptv_list.m3u')
