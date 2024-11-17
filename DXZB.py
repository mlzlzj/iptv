import os
import re
import time
import requests
import threading
from queue import Queue
from threading import Thread
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed


def check_ip(ip, port):
    try:
        url = f"http://{ip}:{port}/status"
        response = requests.get(url, timeout=1)  # 设置超时为1秒
        if response.status_code == 200 and 'udpxy status' in response.text:
            print(f"扫描到有效ip: {ip}:{port}")
            return f"{ip}:{port}"
    except requests.RequestException:
        return None
    return None


def generate_ips(ip_part, option):
    a, b, c, d = map(int, ip_part.split('.'))
    if option == 0:
        return [f"{a}.{b}.{c}.{d}" for d in range(1, 256)]
    else:
        return [f"{a}.{b}.{c}.{d}" for c in range(0, 256) for d in range(0, 256)]


def save_to_file(filename, valid_ips):
    with open(filename, 'w') as f:
        for ip in valid_ips:
            f.write(f"{ip}\n")


def read_config(config_path):
    configs = []
    try:
        with open(config_path, 'r') as file:
            for line in file:
                line = line.strip()
                if line:
                    parts = line.split(',')
                    ip_port = parts[0].strip()  # 去除IP:端口部分前后的空格
                    if len(parts) == 2:
                        option = int(parts[1].strip())  # 去除扫描类型部分前后的空格，并转换为整数
                    else:
                        option = 0  # 默认为0
                    if ':' in ip_port:
                        ip, port = ip_port.split(':')
                        configs.append((ip, port, option))
                    else:
                        print(f"配置文件中的 IP:端口 格式错误: {line}")
    except FileNotFoundError:
        print(f"配置文件 '{config_path}' 不存在。")
        return []
    except ValueError as e:
        print(f"配置文件格式错误: {e}")
        return []
    except Exception as e:
        print(f"读取配置文件出错: {e}")
        return []
    return configs


def replace_ip_in_channels(ip, channels):
    return [channel.replace("udp://", f"http://{ip}/udp/") for channel in channels]


# 定义一个集合，用于存储唯一的 IP 地址及端口组合
unique_ip_ports = set()

# 读取配置文件
config_path = 'config.txt'
configs = read_config(config_path)

# 使用集合去除重复的 IP 地址及端口
unique_configs = []
for ip_part, port, option in configs:
    ip_port = f"{ip_part}:{port}"
    if ip_port not in unique_ip_ports:
        unique_ip_ports.add(ip_port)
        unique_configs.append((ip_part, port, option))

# 执行 IP 扫描
all_valid_ips = []
for ip_part, port, option in unique_configs:
    print(f"开始扫描地址: {ip_part}, 端口: {port}, 类型: {option}")
    ips_to_check = generate_ips(ip_part, option)

    valid_ips = []
    total_ips = len(ips_to_check)
    checked_count = [0]


    def update_status(checked_count):
        while checked_count[0] < total_ips:
            print(f"验证数量: {checked_count[0]}, 有效数量: {len(valid_ips)}")
            time.sleep(10)


    # 启动状态更新线程
    status_thread = threading.Thread(target=update_status, args=(checked_count,))
    status_thread.start()

    max_workers = 10 if option == 0 else 100  # 扫描IP线程数量
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_ip = {executor.submit(check_ip, ip, port): ip for ip in ips_to_check}
        for future in as_completed(future_to_ip):
            ip = future_to_ip[future]
            result = future.result()
            if result is not None:
                valid_ips.append(result)
            checked_count[0] += 1

    # 等待状态线程结束
    status_thread.join()
    all_valid_ips.extend(valid_ips)

save_to_file('ip.txt', all_valid_ips)

for ip in all_valid_ips:
    print(ip)

# 读取湖南_电信.txt文件中的频道列表
with open('湖南_电信.txt', 'r', encoding='utf-8') as f:
    channels = f.readlines()

# 将所有替换后的频道列表写入湖南_组播.txt文件中
with open('湖南_组播.txt', 'w', encoding='utf-8') as f:
    for ip in all_valid_ips:
        replaced_channels = replace_ip_in_channels(ip, channels)
        for channel in replaced_channels:
            f.write(f"{channel}")
        # 在每个IP地址的频道列表后添加一个空行，避免一行中写入两个频道列表
        f.write("\n")

print(f"共扫描获取到有效IP {len(all_valid_ips)} 个，已全部匹配到湖南_组播.txt文件中\n。")

# 开始对组播源频道列表进行下载速度检测
# 定义一个全局队列，用于存储需要测速的频道信息
speed_test_queue = Queue()

# 用于存储测速结果的列表
speed_results = []


# 读取iptv_list.txt文件中的所有频道，并将它们添加到队列中
def load_channels_to_speed_test():
    with open('湖南_组播.txt', 'r', encoding='utf-8') as file:
        for line in file:
            channel_info = line.strip().split(',')
            if len(channel_info) >= 2:  # 假设至少有名称和URL
                name, url = channel_info[:2]  # 只取名称和URL
                speed_test_queue.put((name, url))


# 执行下载速度测试
def download_speed_test():
    while not speed_test_queue.empty():
        channel = speed_test_queue.get()
        name, url = channel
        download_time = 5  # 设置下载时间为 5 秒
        chunk_size = 1024  # 设置下载数据块大小为 1024 字节

        try:
            start_time = time.time()
            response = requests.get(url, stream=True, timeout=download_time)
            response.raise_for_status()
            size = 0
            for chunk in response.iter_content(chunk_size=chunk_size):
                size += len(chunk)
                if time.time() - start_time >= download_time:
                    break
            download_time = time.time() - start_time
            download_rate = round(size / download_time / 1024 / 1024, 2)
        except requests.RequestException as e:
            print(f"请求异常: {e}")
            download_rate = 0

        print(f"{name},{url}, {download_rate} MB/s")
        speed_test_queue.task_done()
        speed_results.append((download_rate, name, url))


# 创建并启动线程
def start_speed_test_threads(num_threads):
    threads = []
    for _ in range(num_threads):
        thread = Thread(target=download_speed_test)
        thread.start()
        threads.append(thread)
    for thread in threads:
        thread.join()


load_channels_to_speed_test()
start_speed_test_threads(10)  # 测试下载速度线程数
speed_results.sort(reverse=True)

# 写入分类排序后的频道信息
with open("speed.txt", 'w', encoding='utf-8') as file:
    for result in speed_results:
        download_rate, channel_name, channel_url = result
        file.write(f"{channel_name},{channel_url},{download_rate}\n")


# 对经过下载速度检测后的所有组播频道列表进行分组排序
# 从测速后的文件中读取频道列表
with open('speed.txt', 'r', encoding='utf-8') as file:
    channels = []
    for line in file:
        line = line.strip()
        if line:
            parts = line.split(',')
            if len(parts) == 3:
                name, url, speed = parts
                channels.append((name, url, speed))


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
              or '益阳' in name or '衡阳' in name or '道县' in name or '邵阳' in name or '郴州' in name):
            groups['湖南频道,#genre#'].append((name, url, speed))
        else:
            groups['其他频道,#genre#'].append((name, url, speed))

        # 对每组进行排序
        for group in groups.values():
            group.sort(key=lambda x: (
                natural_key(x[0]),  # 名称自然排序
                -float(x[2]) if x[2] is not None else float('-inf')  # 速度从高到低排序
            ))

    # 筛选相同名称的频道，只保存10个
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

            if seen_names[name] < 9:
                filtered_list.append(channel)
                seen_names[name] += 1
            else:
                overflow_list.append(channel)

        filtered_groups[group_name] = filtered_list
        overflow_groups[group_name] = overflow_list

    # # 获取当前时间
    now = datetime.now()
    update_time_line = f"更新时间,#genre#\n{now.strftime('%Y-%m-%d %H:%M:%S')},url\n"
    # 保存到 iptv_list.txt 文件
    with open('iptv_list.txt', 'w', encoding='utf-8') as file:
        file.write(update_time_line)
        for group_name, channel_list in filtered_groups.items():
            file.write(f"{group_name}:\n")
            for name, url, speed in channel_list:
                # if speed >= 0.3:  # 只写入下载速度大于或等于 0.3 MB/s 的频道
                file.write(f"{name},{url}\n")
            file.write("\n")  # 打印空行分隔组

    # # 保存频道数量超过10个的频道列表到新文件
    # with open('Filtered_iptv.txt', 'w', encoding='utf-8') as file:
    #     for group_name, channel_list in overflow_groups.items():
    #         if channel_list:  # 只写入非空组
    #             file.write(f"{group_name}\n")
    #             for name, url, speed in channel_list:
    #                 file.write(f"{name},{url}\n")
    #             file.write("\n")  # 打印空行分隔组
    return groups


# 对频道列表进行分组和排序
grouped_channels = group_and_sort_channels(channels)
os.remove("湖南_组播.txt")
os.remove("speed.txt")
# os.remove("ip.txt")

print(f"\n经过测速分类排序后的频道列表已全部写入iptv_list.txt文件中。")
