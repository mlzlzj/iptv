import requests
import re
import os
# from datetime import datetime

#  获取远程直播源文件
url = "https://mirror.ghproxy.com/https://raw.githubusercontent.com/Fairy8o/IPTV/main/DIYP-v4.txt"
r = requests.get(url)
open('DIYP-v4.txt', 'wb').write(r.content)

keywords = ['凤凰卫视', '凤凰资讯', 'TVB翡翠', 'TVB明珠', 'TVB星河', 'J2', '无线', '有线', '天映', 'VIU', 'RTHK', 'HOY',
            '香港卫视' 'Viu']  # 需要提取的关键字列表
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
