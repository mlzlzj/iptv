import threading
from queue import Queue
import time
import random
from bs4 import BeautifulSoup
import re
from playwright.sync_api import sync_playwright
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import os


# 初始化浏览器
def init_browser():
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    context.route("**/*", lambda route, request: intercept_requests(route, request))
    return browser, playwright


# 拦截和过滤 HTTP 请求
def intercept_requests(route, request):
    url = request.url
    if "www.foodieguide.com" in url:
        route.continue_()
    else:
        print("拦截第三方内容:", url)
        route.abort()


# 关闭浏览器
def close_browser(browser, playwright):
    browser.close()
    playwright.stop()


def fetch_channel_info_worker(task_queue, result_queue, place_name):
    browser, playwright = init_browser()
    page = browser.new_page()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0"
    }
    page.set_extra_http_headers(headers)

    while True:
        url_id = task_queue.get()
        if url_id is None:
            break

        channels_info = []
        try:
            page.on('route', lambda route: intercept_requests(route))
            page.goto(f'http://www.foodieguide.com/iptvsearch/hotellist.html?s={url_id}', timeout=180000)  # 增加超时时间到180秒
            time.sleep(random.uniform(5, 10))
            hidden_result = page.query_selector("#hiddenresult")
            if hidden_result:
                print(f"扫描-{place_name}-IP：", url_id, "搜索并解析直播源频道信息......")
                result_html = page.inner_html("#hiddenresult")
                soup = BeautifulSoup(result_html, 'html.parser')
                result_divs = soup.find_all('div', class_='result')

                for _ in range(3):
                    time.sleep(random.uniform(0.5, 1.5))
                    x = random.randint(100, 500)
                    y = random.randint(100, 500)
                    page.mouse.move(x, y)

                for result_div in result_divs:
                    channel_name_element = result_div.find('div', class_='channel')
                    channel_name_link = channel_name_element.find('a') if channel_name_element else None
                    if channel_name_link:
                        channel_name = channel_name_link.text.strip()
                    else:
                        continue
                    m3u8_element = result_div.find('div', class_='m3u8')
                    if m3u8_element:
                        url_td = m3u8_element.find('td', style=re.compile(r'padding-left:\s*6px;'))
                        if url_td:
                            channel_url = url_td.text.strip()
                        else:
                            continue
                    else:
                        continue
                    channels_info.append((channel_name, channel_url, 2))
            else:
                print(f"扫描-{place_name}-IP：", url_id, "未搜索到直播源频道信息......")

            if channels_info:
                result_queue.put((url_id, channels_info))

        except Exception as e:
            print(f"获取频道信息时发生异常: {e} - URL: {url_id}")

        task_queue.task_done()

    page.close()
    close_browser(browser, playwright)


# 获取酒店 IPTV 组播搜索结果
def get_hotel_multicast_search_results(search_term):
    browser, playwright = init_browser()
    page = browser.new_page()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0"
    }
    page.set_extra_http_headers(headers)
    url_dict = {}
    try:
        page.set_default_timeout(600000)
        page.on('route', lambda route: intercept_requests(route))
        page.goto('http://www.foodieguide.com/iptvsearch/hoteliptv.php')
        for char in search_term:
            page.type('#search', char, delay=random.uniform(0.1, 0.3))
            time.sleep(random.uniform(0.1, 0.3))
        time.sleep(random.uniform(1, 3))
        page.click('#form1 [type="submit"]')
        time.sleep(random.uniform(1, 3))
        channel_links = page.query_selector_all('.channel a')
        for i, link in enumerate(channel_links):
            href = link.get_attribute('href')
            ip_port = href.split("hotellist.html?s=")[-1]
            url_dict[ip_port] = i
    except Exception as e:
        print("获取酒店组播时发生错误:", e)
    finally:
        page.close()
        close_browser(browser, playwright)  # 在这里关闭浏览器和 playwright 对象

    return url_dict


# 获取酒店 IPTV 频道信息
def get_hotel_multicast_channel_info(url_dict, place_name):
    ip_folder = "Valid_ip"
    os.makedirs(ip_folder, exist_ok=True)  # Create the IP folder if it doesn't exist
    ip_file_path = os.path.join(ip_folder, "ip.txt")

    if not os.path.exists(ip_file_path):
        open(ip_file_path, 'w', encoding='utf-8').close()

    existing_urls = set()
    with open(ip_file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            existing_urls.add(line)  # 直接将整行作为 URL 添加到集合中

    task_queue = Queue()
    result_queue = Queue()

    for url_id in url_dict.keys():
        task_queue.put(url_id)

    threads = []
    for _ in range(10):  # 创建 10 个线程
        worker_thread = threading.Thread(target=fetch_channel_info_worker, args=(task_queue, result_queue, place_name))
        worker_thread.start()
        threads.append(worker_thread)

    task_queue.join()

    for _ in range(10):  # 停止所有线程
        task_queue.put(None)
    for thread in threads:
        thread.join()

    channels_info_dict = {}
    new_url_info = {}
    while not result_queue.empty():
        url_id, channels_info = result_queue.get()
        if channels_info:
            for name, url, speed in channels_info:
                channels_info_dict[url] = (name, url, speed)
                if url_id not in existing_urls:
                    if url_id not in new_url_info:
                        new_url_info[url_id] = []
                    new_url_info[url_id].append((name, url, speed))

    channels_info = list(channels_info_dict.values())

    # 去重处理
    unique_channels = {}
    for name, url, speed in channels_info:
        if url not in unique_channels:
            unique_channels[url] = (name, url, speed)

    unique_channels_info = list(unique_channels.values())

    if not unique_channels_info:
        print("未解析到直播源频道信息！")
    else:
        with open('iptv.txt', 'w', encoding='utf-8') as f:
            for channel_info in unique_channels_info:
                f.write(f"{channel_info[0]},{channel_info[1]},{channel_info[2]}\n")

            # 将有效的ip地址写入Valid_ip文件夹
            ip_folder = "Valid_ip"
            os.makedirs(ip_folder, exist_ok=True)
            ip_file_path = os.path.join(ip_folder, f"{place_name}_ip.txt")
            with open(ip_file_path, 'w', encoding='utf-8') as f:
                for url_id in new_url_info.keys():
                    f.write(f"{url_id}\n")

        return unique_channels_info


# 执行下载速度测试
def download_speed_test(channel):
    session = requests.Session()
    if len(channel) == 3:
        name, url, download_rate = channel
    else:
        name, url = channel
    download_time = 10  # 设置下载时间为 10 秒
    chunk_size = 8192  # 设置下载数据块大小为 8192 字节

    try:
        start_time = time.time()
        response = session.get(url, stream=True, timeout=download_time)
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

    print(f"{name},{url}, {download_rate}  MB/s")
    return name, url, download_rate


# 过滤和修改直播源频道名称
def filter_and_modify_sources(sources):
    filtered_sources = []
    name_dict = ['购物', '理财', '导视', '指南', '测试', '芒果', 'IPTV', 'CGTN']

    for name, url, speed in sources:
        if float(speed) < 0.3:
            continue
        if any(word.lower() in name.lower() for word in name_dict):
            print("过滤频道:" + name)
        else:
            # 进行频道名称的替换操作
            name = name.replace("FHD", "").replace("HD", "").replace("hd", "").replace("频道", "").replace("高清", "") \
                .replace("超清", "").replace("20M", "").replace("-", "").replace("4k", "").replace("4K", "") \
                .replace("4kR", "")

            if "cctv" in name.lower() and any(char.isdigit() for char in name):
                if "cctv4" not in name.lower():
                    name = re.sub(r'[\u4e00-\u9fff]+', '', name)
            filtered_sources.append((name, url, speed))
    return filtered_sources


# 频道排序的关键函数
def channel_key(channel_name):
    match = re.search(r'\d+', channel_name)
    if match:
        return int(match.group())
    else:
        return float('inf')  # 返回一个无穷大的数字作为关键字


# 对所有频道列表进行分类排序
def classify_and_sort_sources():
    results = []
    with open("iptv.txt", 'r', encoding='utf-8') as file:
        for line in file:
            channel_info = line.strip().split(',')
            channel_name = channel_info[0]
            channel_url = channel_info[1]
            download_rate = channel_info[2]
            results.append((channel_name, channel_url, download_rate))

    # 对频道进行排序
    results.sort(key=lambda x: channel_key(x[0]))
    result_counter = 10  # 每个频道需要的个数
    # 写入分类排序后的频道信息
    with open("iptv_list.txt", 'w', encoding='utf-8') as file:
        channel_counters = {}
        file.write('央视频道,#genre#\n')
        for result in results:
            channel_name, channel_url, download_rate = result
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
        file.write('\n卫视频道,#genre#\n')
        for result in results:
            channel_name, channel_url, download_rate = result
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
        file.write('\n湖南频道,#genre#\n')
        for result in results:
            channel_name, channel_url, download_rate = result
            if '湖南' in channel_name or '长沙' in channel_name or '金鹰' in channel_name or 'CHC' in channel_name \
                    or '凤凰' in channel_name or '常德' in channel_name or '娄底' in channel_name or '永州' in channel_name \
                    or '湘西' in channel_name or '张家界' in channel_name or '衡阳' in channel_name or '邵阳' in channel_name \
                    or '浏阳' in channel_name or '怀化' in channel_name:
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
        file.write('\n其他频道,#genre#\n')
        for result in results:
            channel_name, channel_url, download_rate = result
            if 'CCTV' not in channel_name and '卫视' not in channel_name and '长沙' not in channel_name \
                    and '金鹰' not in channel_name and 'CHC' not in channel_name and '湖南' not in channel_name \
                    and '凤凰' not in channel_name and '常德' not in channel_name and '娄底' not in channel_name \
                    and '永州' not in channel_name and '湘西' not in channel_name and '衡阳' not in channel_name \
                    and '邵阳' not in channel_name and '浏阳' not in channel_name and '张家界' not in channel_name \
                    and '怀化' not in channel_name:
                if channel_name in channel_counters:
                    if channel_counters[channel_name] >= result_counter:
                        continue
                    else:
                        file.write(f"{channel_name},{channel_url}\n")
                        channel_counters[channel_name] += 1
                else:
                    file.write(f"{channel_name},{channel_url}\n")
                    channel_counters[channel_name] = 1

    # 写入更新日期时间
    with open("iptv_list.txt", 'a', encoding='utf-8') as file:
        now = datetime.now()
        file.write(f"\n更新时间,#genre#\n")
        file.write(f"{now.strftime('%Y-%m-%d %H:%M:%S')},url\n")

    print("\n频道分类列表已完成，写入iptv_list.txt文件。")


# 主函数
def main(search_terms):
    print(f"...本次扫描-{search_terms}-地区的组播源...")
    region_folder = "地区组播源"
    os.makedirs(region_folder, exist_ok=True)
    all_results = {}
    for search_term in search_terms:
        print(f"\n...开始获取-{search_term}-ip地址...")
        place_name = search_term
        result = get_hotel_multicast_search_results(search_term)  # 获取搜索结果
        if result:
            sources = get_hotel_multicast_channel_info(result, place_name)  # 传递 place_name 参数

            if sources is None:
                sources = []

            # 使用 ThreadPoolExecutor 进行多线程测速
            speed_test_results = []
            with ThreadPoolExecutor(max_workers=10) as executor:
                # 过滤掉 None 值后再创建 future_to_channel 字典
                future_to_channel = {executor.submit(download_speed_test, source): source for source in sources if
                                     source}
                for future in as_completed(future_to_channel):
                    channel = future_to_channel[future]
                    try:
                        result = future.result()
                        if result:  # 确保结果是有效的
                            speed_test_results.append(result)
                    except Exception as exc:
                        print(f"频道：{channel[0]} 测速时发生异常：{exc}")

            # 对测速结果按照下载速率降序排序写入以地方命名的.txt文件中
            speed_test_results.sort(key=lambda x: x[2], reverse=True)

            region_file_path = os.path.join(region_folder, f'{search_term}.txt')
            with open(region_file_path, 'w', encoding='utf-8') as f:
                for name, url, speed in speed_test_results:
                    if speed >= 0.3:  # 修改条件判断，只有速率大于或等于0.3MB/s时写入文件
                        f.write(f"{name},{url},{speed} MB/s\n")

            # 确保 all_results 中的每个元素都是一个包含三个值的元组
            all_results[search_term] = [(name, url, speed) for name, url, speed in speed_test_results if speed >= 0.3]

    # 将Valid_ip文件夹内所有地方名_ip.txt文件合并为ip.txt的文件
    ip_folder = "Valid_ip"
    combined_ip_file_path = os.path.join(ip_folder, "ip.txt")
    with open(combined_ip_file_path, 'w', encoding='utf-8') as combined_ip_file:
        for search_term in search_terms:
            ip_file_path = os.path.join(ip_folder, f"{search_term}_ip.txt")
            if os.path.exists(ip_file_path):
                with open(ip_file_path, 'r', encoding='utf-8') as ip_file:
                    for line in ip_file:
                        combined_ip_file.write(line)

    # 合并地区文件夹内所有地方名称.txt文件为iptv.txt的文件
    iptv_file_path = "iptv.txt"
    channels_dict = {}

    for search_term in search_terms:
        region_file_path = os.path.join(region_folder, f"{search_term}.txt")
        if os.path.exists(region_file_path):
            with open(region_file_path, 'r', encoding='utf-8') as region_file:
                for line in region_file:
                    parts = line.strip().split(',')
                    if len(parts) == 3:
                        name, url, speed = parts
                        speed = float(speed.strip(' MB/s'))
                        # 如果频道和URL已经存在，则只保留下载速率最高的频道
                        if (name, url) in channels_dict:
                            if channels_dict[(name, url)][2] < speed:
                                channels_dict[(name, url)] = (name, url, speed)
                        else:
                            channels_dict[(name, url)] = (name, url, speed)

    # 将去重后的频道列表写入 iptv.txt 文件中
    with open(iptv_file_path, 'w', encoding='utf-8') as f:
        for channel in channels_dict.values():
            name, url, speed = channel
            f.write(f"{name},{url},{speed} MB/s\n")

    # 调用 filter_and_modify_sources 方法过滤和修改直播源频道名称
    all_results_list = []
    for results in all_results.values():
        for channel in results:
            if isinstance(channel, tuple) and len(channel) == 3:
                all_results_list.append(channel)

    filtered_and_modified_sources = filter_and_modify_sources(all_results_list)

    # 将过滤和修改后的频道列表重新写入 iptv.txt 文件中
    with open(iptv_file_path, 'w', encoding='utf-8') as f:
        for name, url, speed in filtered_and_modified_sources:
            f.write(f"{name},{url},{speed} MB/s\n")

    # 调用 classify_and_sort_sources 方法进行分类和排序
    classify_and_sort_sources()


if __name__ == "__main__":
    search_terms = ["长沙", "娄底", "衡阳", "常德", "株洲", "湘潭", "邵阳", "张家界", "益阳", "郴州", "永州", "怀化"]
    main(search_terms)
