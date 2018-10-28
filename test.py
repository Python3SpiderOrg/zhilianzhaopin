# !usr/bin/env python3
# -*- coding:utf-8 -*- 
"""
@project = Spider_zhilian
@file = test
@author = Easton Liu
@time = 2018/10/28 21:22
@Description: 

"""
import requests
from lxml import etree
url = r'https://jobs.zhaopin.com/CC120072290J00155201606.htm'

html = requests.get(url).text
s = etree.HTML(html)
job_address = s.xpath('//p[@class="add-txt"]/text()')
print(job_address)