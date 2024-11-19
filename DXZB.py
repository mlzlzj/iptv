import itertools
import requests
import threading
import os
import json
import re
import threading
from queue import Queue


def read_config(config_path):
    configs = []
    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            for line in file:
                line = line.strip()
                if line:  # 忽略空行
                    config_dict = {}
                    # 使用等号分割键和值
                    for item in line.split(','):
                        parts = item.split('=')
                        if len(parts) == 2:
                            key, value = parts
                            config_dict[key.strip()] = value.strip()
                        else:
                            print(f"配置文件格式错误，无法解析: {item}")
                    configs.append(config_dict)
    except UnicodeDecodeError:
        with open(config_path, 'r', encoding='gbk') as file:
            for line in file:
                line = line.strip()
                if line:  # 忽略空行
                    config_dict = {}
                    # 使用等号分割键和值
                    for item in line.split(','):
                        parts = item.split('=')
                        if len(parts) == 2:  # 确保有键和值
                            key, value = parts
                            config_dict[key.strip()] = value.strip()
                        else:
                            print(f"配置文件格式错误，无法解析项: {item}")
                    configs.append(config_dict)
    return configs


def generate_ip_combinations(start_ip, end_ip, scan_type, ports):
    parts_start = start_ip.split('.')
    parts_end = end_ip.split('.')
    A, B, C_start, D_start = parts_start
    C_end, D_end = parts_end[2], parts_end[3]

    if scan_type == '1':  # 扫D段
        C_range = [C_start]
        D_range = range(int(D_start), int(D_end) + 1)
    elif scan_type == '2':  # C段D段都扫
        C_range = range(0, 256)
        D_range = range(0, 256)

    all_ips = []
    for C, D in itertools.product(C_range, D_range):
        for port in ports:
            all_ips.append((f"{A}.{B}.{C}.{D}", port))

    return all_ips


def check_link_with_semaphore(ip_port_pair, result_set, progress_lock, progress_counter, total_count, semaphore):
    ip, port = ip_port_pair
    link = f"http://{ip}:{port}/iptv/live/1000.json?key=txiptv"
    try:
        response = requests.get(link, timeout=5)
        with progress_lock:
            progress_counter[0] += 1
            progress = (progress_counter[0] / total_count) * 100
            if response.status_code == 200:
                result_set.add(link)
                print(f"[{progress_counter[0]}/{total_count} - {progress:.2f}%] 有效: {link}")
            else:
                print(f"[{progress_counter[0]}/{total_count} - {progress:.2f}%] 无效: {link}")
    except Exception:
        with progress_lock:
            progress_counter[0] += 1
            progress = (progress_counter[0] / total_count) * 100
            print(f"[{progress_counter[0]}/{total_count} - {progress:.2f}%] 无效: {link}")
    finally:
        semaphore.release()


def write_results(result_set, directory, start_ip):
    if not os.path.exists(directory):
        os.makedirs(directory)
    filename = f"{start_ip.replace('.', '_')}.txt"
    file_path = os.path.join(directory, filename)
    with open(file_path, "w", encoding="utf-8") as file:
        for valid_link in result_set:
            file.write(f"{valid_link}\n")


# 定义函数来保存结果到文本文件
def save_results_to_file(result_set, file_path):
    with open(file_path, 'w', encoding='utf-8') as file:
        for valid_link in result_set:
            file.write(f"{valid_link}\n")


# 定义函数来获取频道列表
def get_channel_list(url):
    try:
        # 发送GET请求，增加超时时间
        response = requests.get(url, timeout=20)
        if response.status_code == 200:
            data = json.loads(response.text)
            # 检查code是否为0
            if data.get('code') == 0:
                channels = []
                # 解析JSON文件，获取name和url字段
                for item in data['data']:
                    if isinstance(item, dict):
                        name = item.get('name')
                        chid = str(item.get('chid')).zfill(4)
                        srcid = item.get('srcid')
                        ip_port = url.split('/')[2]
                        # 替换频道名称中的特定字符串
                        name = name.replace("中央", "CCTV")
                        name = name.replace("高清", "")
                        name = name.replace("超清", "")
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
                        name = name.replace("CMIPTV", "")
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
                        name = name.replace("CCTV少儿", "CCTV14")
                        name = name.replace("CCTV15音乐", "CCTV15")
                        name = name.replace("CCTV音乐", "CCTV15")
                        name = name.replace("CCTV16奥林匹克", "CCTV16")
                        name = name.replace("CCTV16奥运匹克", "CCTV16")
                        name = name.replace("CCTV17农业农村", "CCTV17")
                        name = name.replace("CCTV17军农", "CCTV17")
                        name = name.replace("CCTV17农业", "CCTV17")
                        name = name.replace("CCTV5+体育赛视", "CCTV5+")
                        name = name.replace("CCTV5+赛视", "CCTV5+")
                        name = name.replace("CCTV5+体育赛事", "CCTV5+")
                        name = name.replace("CCTV5+赛事", "CCTV5+")
                        name = name.replace("CCTV5+体育", "CCTV5+")
                        name = name.replace("CCTV5赛事", "CCTV5+")
                        name = name.replace("凤凰中文台", "凤凰中文")
                        name = name.replace("凤凰资讯台", "凤凰资讯")
                        name = name.replace("CCTV4K测试）", "CCTV4")
                        name = name.replace("CCTV164K", "CCTV16")
                        name = name.replace("CCTNCCTV国际", "CCTVNEWS")
                        name = name.replace("上海东方卫视", "上海卫视")
                        name = name.replace("东方卫视", "上海卫视")
                        name = name.replace("内蒙卫视", "内蒙古卫视")
                        name = name.replace("福建东南卫视", "东南卫视")
                        name = name.replace("广东南方卫视", "南方卫视")
                        name = name.replace("金鹰卡通卫视", "金鹰卡通")
                        name = name.replace("湖南金鹰卡通", "金鹰卡通")
                        name = name.replace("炫动卡通", "哈哈炫动")
                        name = name.replace("卡酷卡通", "卡酷少儿")
                        name = name.replace("卡酷动画", "卡酷少儿")
                        name = name.replace("BRTVKAKU少儿", "卡酷少儿")
                        name = name.replace("优曼卡通", "优漫卡通")
                        name = name.replace("优曼卡通", "优漫卡通")
                        name = name.replace("嘉佳卡通", "佳嘉卡通")
                        name = name.replace("世界地理", "地理世界")
                        name = name.replace("CCTV世界地理", "地理世界")
                        name = name.replace("BTV北京卫视", "北京卫视")
                        name = name.replace("BTV冬奥纪实", "冬奥纪实")
                        name = name.replace("东奥纪实", "冬奥纪实")
                        name = name.replace("卫视台", "卫视")
                        name = name.replace("湖南电视台", "湖南卫视")
                        name = name.replace("少儿科教", "少儿")
                        name = name.replace("影视剧", "影视")
                        if name and chid and srcid:
                            channel_url = f'{name},http://{ip_port}/tsfile/live/{chid}_{srcid}.m3u8'
                            channels.append(channel_url)

                return channels
            else:
                print("错误: ", data.get('msg', '未知错误'))
                return None
        else:
            print("错误: 无法获取到频道列表.")
            return None
    except (requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout) as e:
        print(f"错误: {e}")
        return None
    except requests.exceptions.ConnectionError:
        print("错误: 无法连接到服务器，请检查服务器地址或网络连接。")
        return None
    except json.JSONDecodeError:
        print("错误: 解析JSON数据失败，请检查返回的数据是否为有效的JSON格式。")
        return None


# 定义函数来保存频道列表到文件
def save_channels_to_file(directory, filename, channels):
    if not os.path.exists(directory):
        os.makedirs(directory)
    with open(os.path.join(directory, filename), 'w', encoding='utf-8') as file:
        for channel in channels:
            file.write(channel + '\n')


# 定义函数来合并文件
def merge_files(directory, output_filename):
    if not os.path.exists(directory):
        print(f"错误: 目录 '{directory}' 不存在。")
        return

    # 打开输出文件
    with open(output_filename, 'w', encoding='utf-8') as output_file:
        for filename in os.listdir(directory):
            if filename.endswith('.txt'):
                with open(os.path.join(directory, filename), 'r', encoding='utf-8') as file:
                    content = file.read()
                    output_file.write(content)


# 读取配置文件
config_path = 'config.txt'
try:
    configs = read_config(config_path)
except Exception as e:
    print(f"读取配置文件出错: {e}")

# 定义一个集合来存储所有的有效链接
all_valid_links = set()

for config in configs:
    name = config['name']
    start_ip = config['start_ip']  # 起始ip
    end_ip = config['end_ip']  # 结束ip
    scan_type = config['scan_type']  # 扫描类型，1为扫D段，2为扫C,D段

    # 如 'port_1=9901','port_2=8881','port_3=808' 等作为定义要扫描的每一个端口，可一次性扫一段ip多个端口。
    ports = []
    for i in range(1, len(config) + 1):
        port_key = f'port_{i}'
        if port_key in config:
            ports.append(int(config[port_key]))

    for port in ports:
        # 生成IP地址组合和端口
        all_ip_port_pairs = generate_ip_combinations(start_ip, end_ip, scan_type, [port])
        total_count = len(all_ip_port_pairs)

        result_set = set()
        progress_counter = [0]
        progress_lock = threading.Lock()

        # 根据 scan_type 设置不同的线程数量
        semaphore = threading.BoundedSemaphore(50 if scan_type == '1' else 200)  # 线程数量

        threads = []
        for ip_port_pair in all_ip_port_pairs:
            semaphore.acquire()
            thread = threading.Thread(target=check_link_with_semaphore,
                                      args=(
                                          ip_port_pair, result_set, progress_lock, progress_counter, total_count,
                                          semaphore))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # 打印有效链接数量，每个有效链接打印在新的一行
        valid_links_count = len(result_set)
        print(f"扫描到{valid_links_count}个有效链接：")
        for valid_link in result_set:
            print(valid_link)
        print()  # 打印一个空行以分隔不同的端口扫描结果
        all_valid_links.update(result_set)

# 将所有扫描到的有效链接写入txiptv.txt文件中
txiptv_file_path = 'txiptv.txt'
save_results_to_file(all_valid_links, txiptv_file_path)

# 打印有效链接数量及链接
valid_links_count = len(all_valid_links)
for valid_link in all_valid_links:
    print(valid_link)

print(f"本次扫描共获取到{valid_links_count}条有效链接,所有扫描到的有效链接已保存到 {txiptv_file_path}")

# 检查并准备 "酒店源" 文件夹
directory = '酒店源'
if not os.path.exists(directory):
    os.makedirs(directory)
else:
    # 删除文件夹中的所有 .txt 文件
    for filename in os.listdir(directory):
        if filename.endswith('.txt'):
            file_path = os.path.join(directory, filename)
            os.remove(file_path)

# 读取 txiptv.txt 文件中的链接
with open(txiptv_file_path, 'r', encoding='utf-8') as file:
    urls = file.readlines()

# 遍历读取的链接
for url in urls:
    url = url.strip()
    if not url:
        continue

    # 获取频道列表
    channels = get_channel_list(url)

    # 检查频道列表是否为空
    if channels:
        print(f"\n解析 {url} 下的频道列表:")
        for channel in channels:
            print(channel)
        # 从URL中提取IP地址并生成文件名
        ip_address = url.split('/')[2].split(':')[0]
        filename = ip_address + '.txt'
        directory = '酒店源'

        # 保存频道列表到文件
        save_channels_to_file(directory, filename, channels)

        print(f"解析到的频道地址已保存到 {directory}/{filename}")
    else:
        print(f"\n跳过链接 {url}，因为无法获取到频道列表。")

# 合并文件
directory = '酒店源'
output_filename = 'iptv.txt'
merge_files(directory, output_filename)

print(f"所有频道地址已合并保存到 {output_filename}")

import os
import re
import time
import datetime
import threading
from queue import Queue
import requests
from datetime import datetime
import eventlet

eventlet.monkey_patch()
# 线程安全的队列，用于存储下载任务
task_queue = Queue()

# 线程安全的列表，用于存储结果
results = []

channels = []
error_channels = []

with open("iptv.txt", 'r', encoding='utf-8') as file:
    lines = file.readlines()
    for line in lines:
        line = line.strip()
        if line:
            channel_name, channel_url = line.split(',')
            # if '卫视' in channel_name or 'CCTV' in channel_name:
            channels.append((channel_name, channel_url))


# 定义工作线程函数
def worker():
    while True:
        # 从队列中获取一个任务
        channel_name, channel_url = task_queue.get()
        try:
            channel_url_t = channel_url.rstrip(channel_url.split('/')[-1])  # m3u8链接前缀
            lines = requests.get(channel_url, timeout=1).text.strip().split('\n')  # 获取m3u8文件内容
            ts_lists = [line.split('/')[-1] for line in lines if line.startswith('#') == False]  # 获取m3u8文件下视频流后缀
            ts_lists_0 = ts_lists[0].rstrip(ts_lists[0].split('.ts')[-1])  # m3u8链接前缀
            ts_url = channel_url_t + ts_lists[0]  # 拼接单个视频片段下载链接

            # 多获取的视频数据进行5秒钟限制
            with eventlet.Timeout(5, False):
                start_time = time.time()
                content = requests.get(ts_url, timeout=1).content
                end_time = time.time()
                response_time = (end_time - start_time) * 1

            if content:
                with open(ts_lists_0, 'ab') as f:
                    f.write(content)  # 写入文件
                file_size = len(content)
                download_speed = file_size / response_time / 1024
                normalized_speed = min(max(download_speed / 1024, 0.001), 100)  # 将速率从kB/s转换为MB/s并限制在1~100之间
                print(
                    f"\n检测频道: {channel_name},{channel_url}\n下载速度：{download_speed:.3f} kB/s，标准化后的速率：{normalized_speed:.3f} MB/s")

                # 删除下载的文件
                os.remove(ts_lists_0)
                result = channel_name, channel_url, f"{normalized_speed:.3f} MB/s"
                results.append(result)
                numberx = (len(results) + len(error_channels)) / len(channels) * 100
                print(
                    f"可用频道：{len(results)} 个 , 不可用频道：{len(error_channels)} 个 , 总频道：{len(channels)} 个 ,总进度：{numberx:.2f} %。")
        except:
            error_channel = channel_name, channel_url
            error_channels.append(error_channel)
            numberx = (len(results) + len(error_channels)) / len(channels) * 100
            print(
                f"可用频道：{len(results)} 个 , 不可用频道：{len(error_channels)} 个 , 总频道：{len(channels)} 个 ,总进度：{numberx:.2f} %。")

        # 标记任务完成
        task_queue.task_done()


# 创建多个工作线程
num_threads = 5
for _ in range(num_threads):
    t = threading.Thread(target=worker, daemon=True)
    t.start()

# 添加下载任务到队列
for channel in channels:
    task_queue.put(channel)

# 等待所有任务完成
task_queue.join()


def channel_key(channel_name):
    match = re.search(r'\d+', channel_name)
    if match:
        return int(match.group())
    else:
        return float('inf')  # 返回一个无穷大的数字作为关键字


# 对频道进行排序
results.sort(key=lambda x: (x[0], -float(x[2].split()[0])))
results.sort(key=lambda x: channel_key(x[0]))

# 将结果写入文件
with open("speed.txt", 'w', encoding='utf-8') as file:
    for result in results:
        channel_name, channel_url, speed = result
        file.write(f"{channel_name},{channel_url},------{speed}\n")

# with open("iptv_speed.txt", 'w', encoding='utf-8') as file:
#     for result in results:
#         channel_name, channel_url, speed = result
#         file.write(f"{channel_name},{channel_url}\n")


# 对经过下载速度检测后的所有组播频道列表进行分组排序
# 从测速后的文件中读取频道列表
with open('speed.txt', 'r', encoding='utf-8') as file:
    channels = []
    for line in file:
        line = line.strip()
        if line:
            parts = line.split(',')
            if len(parts) == 3:
                channel_name, channel_url, speed = parts
                channels.append((channel_name, channel_url, speed))


def natural_key(string):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', string)]


def group_and_sort_channels(channels):
    groups = {
        '央视频道,#genre#': [],
        '卫视频道,#genre#': [],
        '湖南频道,#genre#': [],
        '其他频道,#genre#': []
    }

    for name, url, speed in channels:
        if 'cctv' in name.lower():
            groups['央视频道,#genre#'].append((name, url, speed))
        elif '卫视' in name or '凤凰' in name or '翡翠' in name or 'CHC' in name:
            groups['卫视频道,#genre#'].append((name, url, speed))
        elif ('湖南' in name or '金鹰' in name or '长沙' in name or '娄底' in name or '岳阳' in name or '常德' in name
              or '张家界' in name or '怀化' in name or '新化' in name or '株洲' in name or '桂东' in name or '武冈' in name
              or '永州' in name or '津市' in name or '浏阳' in name or '湘潭' in name or '湘西' in name or '溆浦' in name
              or '益阳' in name or '衡阳' in name or '道县' in name or '邵阳' in name or '郴州' in name or '双峰' in name):
            groups['湖南频道,#genre#'].append((name, url, speed))
        else:
            groups['其他频道,#genre#'].append((name, url, speed))

    # 筛选相同名称的频道，只保存9个
    filtered_groups = {}
    overflow_groups = {}

    for group_name, channel_list in groups.items():
        seen_names = {}
        filtered_list = []
        overflow_list = []

        for channel in channel_list:
            name = channel[0]
            if name not in seen_names:
                seen_names[name] = 0

            if seen_names[name] < 10:
                filtered_list.append(channel)
                seen_names[name] += 1
            else:
                overflow_list.append(channel)

        filtered_groups[group_name] = filtered_list
        overflow_groups[group_name] = overflow_list

    #  获取当前时间
    now = datetime.now()
    update_time_line = f"更新时间,#genre#\n{now.strftime('%Y-%m-%d %H:%M:%S')},url\n"
    with open('iptv_list.txt', 'w', encoding='utf-8') as file:
        file.write(update_time_line)
        total_channels = 0  # 用于统计频道总数
        for group_name, channel_list in filtered_groups.items():
            file.write(f"{group_name}:\n")
            print(f"{group_name}:")  # 打印分组名称
            for channel_name, channel_url, speed in channel_list:
                # if speed >= 0.3:  # 只写入下载速度大于或等于 0.3 MB/s 的频道
                file.write(f"{channel_name},{channel_url}\n")
                print(f"  {channel_name},{channel_url}")  # 打印频道信息
                total_channels += 1  # 统计频道总数
            file.write("\n")
            print()  # 打印空行分隔组

    print(f"\n经过测速分类排序后的频道列表数量为: {total_channels} 个，已全部写入iptv_list.txt文件中。")

    # # 保存频道数量超过10个的频道列表到新文件
    # with open('Filtered_iptv.txt', 'w', encoding='utf-8') as file:
    #     for group_name, channel_list in overflow_groups.items():
    #         if channel_list:  # 只写入非空组
    #             file.write(f"{group_name}\n")
    #             for name, url, speed in channel_list:
    #                 file.write(f"{name},{url}\n")
    #             file.write("\n")  # 打印空行分隔组
    # return groups


# 对频道列表进行分组和排序
group_and_sort_channels(channels)


# os.remove("txiptv.txt")
# os.remove("iptv.txt")
# os.remove("speed.txt")
# os.remove("iptv_speed.txt")


# # 获取AKTV频道列表AKTV.txt
# url = "http://aktv.top/live.txt"
# r = requests.get(url)
# open('AKTV.txt', 'wb').write(r.content)

# 合并所有的txt文件
file_contents = []
file_paths = ["iptv_list.txt", "AKTV.txt", "hnyd.txt"]  # 替换为实际的文件路径列表
for file_path in file_paths:
    with open(file_path, 'r', encoding="utf-8") as file:
        content = file.read()
        file_contents.append(content)


# 写入合并后的txt文件
with open("iptv_list.txt", "w", encoding="utf-8") as output:
    output.write('\n'.join(file_contents))

print("\n频道分类完毕已写入iptv_list.txt。")
