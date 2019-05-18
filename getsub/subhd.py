# coding: utf-8
# !/usr/bin/env python3

from __future__ import print_function
import time
import json
import re
from contextlib import closing
from collections import OrderedDict as order_dict

import requests
from bs4 import BeautifulSoup

from .sys_global_var import py, prefix
from .progress_bar import ProgressBar


''' SubHD 字幕下载器
'''


class SubHDDownloader(object):
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5)\
                            AppleWebKit 537.36 (KHTML, like Gecko) Chrome",
            "Accept-Language": "zh-CN,zh;q=0.8",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,\
                            image/webp,*/*;q=0.8"
        }
        self.site_url = 'http://subhd.com'
        self.search_url = 'http://subhd.com/search/'

    def get_subtitles(self, keywords, sub_num=5):

        """ 传入关键字列表，返回有序字典。
                keywords:重要度降序的关键字列表
                sub_num: 字幕结果数，默认为5
            返回：
                字幕字典:{
                            '字幕名': {'lan': '字幕包含语言值',
                                       'link': '字幕链接'}
                         }
                         按语言值降序排列
                字幕包含语言值：英文加1， 繁体加2， 简体加4， 双语加8 """

        #print(prefix + ' Searching SUBHD...', end='\r')

        keywords = list(keywords)
        keyword = ''
        for one in keywords:
            keyword += (one + ' ')

        sub_dict = order_dict()
        s = requests.session()
        while True:
            # 当前关键字查询
            r = s.get(self.search_url + keyword, headers=self.headers, timeout=10)
            bs_obj = BeautifulSoup(r.text, 'html.parser')
            try:
                if py == 2:
                    small_text = bs_obj.find('small').text.encode('utf8')
                else:
                    small_text = bs_obj.find('small').text
            except AttributeError as e:
                char_error = 'The URI you submitted has disallowed characters'
                if char_error in bs_obj.text:
                    print(prefix + ' [SUBHD ERROR] '
                          + char_error + ': ' + keyword)
                    return None
                # 搜索验证按钮
                time.sleep(2)
                continue

            if '总共 0 条' not in small_text:
                for one_box in bs_obj.find_all('div', {'class': 'box'}):
                    a = one_box.find('div', {'class': 'd_title'}).find('a')
                    sub_url = self.site_url + a.attrs['href']
                    sub_name = '[SUBHD]' + a.text.encode('utf8') if py == 2 \
                               else '[SUBHD]' + a.text
                    if py == 2:
                        text = one_box.text.encode('utf8')
                    else:
                        text = one_box.text
                    if '/ar' in a.attrs['href']:
                        type_score = 0
                        type_score += ('英文' in text) * 1
                        type_score += ('繁体' in text) * 2
                        type_score += ('简体' in text) * 4
                        type_score += ('双语' in text) * 8
                        sub_dict[sub_name] = {'lan': type_score,
                                              'link': sub_url}
                    if len(sub_dict) >= sub_num:
                        del keywords[:]  # 字幕条数达到上限，清空keywords
                        break

            if len(keywords) > 1:  # 字幕数未满，更换关键词继续查询
                keyword = keyword.replace(keywords[-1], '')
                keywords.pop(-1)
                continue

            break

        if (len(sub_dict.items()) > 0
                and list(sub_dict.items())[0][1]['lan'] < 8):
            # 第一个候选字幕没有双语
            sub_dict = order_dict(
                sorted(sub_dict.items(),
                       key=lambda e: e[1]['lan'], reverse=False)
            )
        return sub_dict

    def download_file(self, file_name, sub_url):

        """ 传入字幕页面链接， 字幕包标题， 返回压缩包类型，压缩包字节数据 """

        sid = sub_url.split('/')[-1]
        r = requests.get(sub_url, headers=self.headers)
        bs_obj = BeautifulSoup(r.text, 'html.parser')
        dtoken = bs_obj.find('button', {'id': 'down'})['dtoken']

        r = requests.post('http://subhd.com/ajax/down_ajax',
                          data={'sub_id': sid, 'dtoken': dtoken},
                          headers=self.headers)

        content = r.content.decode('unicode-escape')
        if json.loads(content)['success'] is False:
            return None, None, 'false'
        res = re.search('http:.*(?=")', r.content.decode('unicode-escape'))
        download_link = res.group(0).replace('\\/', '/')
        try:
            with closing(requests.get(download_link, stream=True)) as response:
                chunk_size = 1024  # 单次请求最大值
                # 内容体总大小
                content_size = int(response.headers['content-length'])
                #bar = ProgressBar(prefix + ' Get',
                                  #file_name.strip(), content_size)
                sub_data_bytes = b''
                for data in response.iter_content(chunk_size=chunk_size):
                    sub_data_bytes += data
                    #bar.refresh(len(sub_data_bytes))
            # sub_data_bytes = requests.get(download_link, timeout=10).content
        except requests.Timeout:
            return None, None, 'false'
        if 'rar' in download_link:
            datatype = '.rar'
        elif 'zip' in download_link:
            datatype = '.zip'
        elif '7z' in download_link:
            datatype = '.7z'
        else:
            datatype = 'Unknown'

        return datatype, sub_data_bytes, 'success'
