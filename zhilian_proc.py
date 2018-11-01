# !usr/bin/env python3
# encoding:utf-8
"""
@project = zhilianzhaopin
@file = zhilian_proc
@author = 'Easton Liu'
@creat_time = 2018/10/30 17:17
@explain:

"""
import requests
import json
import math
import re
import pymongo
import csv
import pickle
import hashlib
import os
import datetime
from lxml import etree
from log import logger
from multiprocessing import Manager,Pool

city_names = ['深圳']
job_names = ['软件测试']
output_path = 'output'

def load_progress( path):
    '''
    反序列化加载已爬取的URL文件
    :param path:
    :return:
    '''
    logger.info("load url file of already spider：%s" % path)
    try:
        with open(path, 'rb') as f:
            tmp = pickle.load(f)
            return tmp
    except:
        logger.info("not found url file of already spider!")
    return set()

def save_progress(data, path):
    '''
    序列化保存已爬取的URL文件
    :param data:要保存的数据
    :param path:文件路径
    :return:
    '''
    try:
        with open(path, 'wb+') as f:
            pickle.dump(data, f)
            logger.info('save url file success!')
    except Exception as e:
        logger.error('save url file failed:',e)
def hash_url(url):
    '''
    对URL进行加密，取加密后中间16位
    :param url:已爬取的URLL
    :return:加密的URL
    '''
    m = hashlib.md5()
    m.update(url.encode('utf-8'))
    return m.hexdigest()[8:-8]

def get_page_nums(cityname,jobname):
    '''
    获取符合要求的工作页数
    :param cityname: 城市名
    :param jobname: 工作名
    :return: 总数
    '''
    url = r'https://fe-api.zhaopin.com/c/i/sou?pageSize=60&cityId={}&workExperience=-1&education=-1' \
          r'&companyType=-1&employmentType=-1&jobWelfareTag=-1&kw={}&kt=3'.format(cityname,jobname)
    logger.info('start get job count...')
    try:
        rec = requests.get(url)
        if rec.status_code==200:
            j = json.loads(rec.text)
            count_nums = j.get('data')['numFound']
            logger.info('get job count nums sucess:%s'%count_nums)
            page_nums = math.ceil(count_nums/60)
            logger.info('page nums:%s' % page_nums)
            return page_nums
    except Exception as e:
        logger.error('get job count nums faild:%s',e)
def get_urls(total_page,cityname,jobname):
    '''
    获取需要爬取的URL以及部分职位信息
    :param start: 开始的工作条数
    :param cityname: 城市名
    :param jobname: 工作名
    :return: 字典
    '''
    for start in range(total_page):
        url = r'https://fe-api.zhaopin.com/c/i/sou?start={}&pageSize=60&cityId={}&workExperience=-1&education=-1' \
              r'&companyType=-1&employmentType=-1&jobWelfareTag=-1&kw={}&kt=3'.format(start*60,cityname,jobname)
        try:
            rec = requests.get(url)
            if rec.status_code == 200:
                j = json.loads(rec.text)
                results = j.get('data').get('results')
                for job in results:
                    empltype = job.get('emplType')  # 职位类型，全职or校园
                    if empltype=='全职':
                        positionURL = job.get('positionURL') # 职位链接
                        createDate = job.get('createDate') # 招聘信息创建时间
                        updateDate = job.get('updateDate') # 招聘信息更新时间
                        endDate = job.get('endDate') # 招聘信息截止时间
                        positionLabel = job.get('positionLabel')
                        if positionLabel:
                            jobLight_par = (re.search('"jobLight":\[(.*?|[\u4E00-\u9FA5]+)\]',job.get('positionLabel'))) # 职位亮点
                            jobLight = jobLight_par.group(1) if jobLight_par else None
                        else:
                            jobLight = None
                        yield {
                            'positionURL':positionURL,
                            'createDate':createDate,
                            'updateDate':updateDate,
                            'endDate':endDate,
                            'jobLight':jobLight
                        }
        except Exception as e:
            logger.error('get urls faild:%s', e)
            return None
def get_job_info(job,old_url,csv_filename):
    '''
    获取工作详情
    :param url_list: 列表
    :return: 字典
    '''
    url = job.get('positionURL')
    h_url = hash_url(url)
    if not h_url in old_url:
        logger.info('spider url:%s'%url)
        try:
            response = requests.get(url)
            if response.status_code == 200:
                s = etree.HTML(response.text)
                job_stat = s.xpath('//div[@class="main1 cl main1-stat"]')[0]
                stat_li_first = job_stat.xpath('./div[@class="new-info"]/ul/li[1]')[0]
                job_name = stat_li_first.xpath('./h1/text()')[0] # 工作名
                salary = stat_li_first.xpath('./div/strong/text()')[0] # 月薪
                stat_li_second = job_stat.xpath('./div[@class="new-info"]/ul/li[2]')[0]
                company_url = stat_li_second.xpath('./div[1]/a/@href')[0] # 公司URL
                company_name = stat_li_second.xpath('./div[1]/a/text()')[0] # 公司名称
                city_name = stat_li_second.xpath('./div[2]/span[1]/a/text()')[0] # 城市名
                workingExp = stat_li_second.xpath('./div[2]/span[2]/text()')[0] # 工作经验
                eduLevel = stat_li_second.xpath('./div[2]/span[3]/text()')[0] # 学历
                amount = stat_li_second.xpath('./div[2]/span[4]/text()')[0] # 招聘人数
                job_text = s.xpath('//div[@class="pos-ul"]//text()') # 工作要求
                job_desc = ''
                for job_item in job_text:
                    job_desc = job_desc+job_item.replace('\xa0','').strip('\n')
                job_address_path = s.xpath('//p[@class="add-txt"]/text()') # 上班地址
                job_address = job_address_path[0] if job_address_path else None
                company_text = s.xpath('//div[@class="intro-content"]//text()') # 公司信息
                company_info=''
                for item in company_text:
                    company_info = company_info+item.replace('\xa0','').strip('\n')
                promulgator = s.xpath('//ul[@class="promulgator-ul cl"]/li')
                compant_industry = promulgator[0].xpath('./strong//text()')[0] #公司所属行业
                company_type = promulgator[1].xpath('./strong/text()')[0] #公司类型：民营，国企，上市
                totall_num = promulgator[2].xpath('./strong/text()')[0] #公司总人数
                company_addr = promulgator[4].xpath('./strong/text()')[0].strip() #公司地址
                logger.info('get job info success!')
                old_url.append(h_url)
                return {
                    'job_name':job_name, # 工作名称
                    'salary':salary, # 月薪
                    'company_name':company_name, # 公司名称
                    'eduLevel':eduLevel, # 学历
                    'workingExp':workingExp, # 工作经验
                    'amount':amount, # 招聘总人数
                    'jobLight':job.get('jobLight'), # 职位亮点
                    'city_name':city_name, # 城市
                    'job_address':job_address, # 上班地址
                    'createDate':job.get('createDate'), # 创建时间
                    'updateDate':job.get('updateDate'), # 更新时间
                    'endDate':job.get('endDate'), # 截止日期
                    'compant_industry':compant_industry, # 公司所属行业
                    'company_type':company_type, # 公司类型
                    'totall_num':totall_num, # 公司总人数
                    'company_addr':company_addr, # 公司地址
                    'job_desc':job_desc, # 岗位职责
                    'job_url':url, # 职位链接
                    'company_info':company_info, # 公司信息
                    'company_url':company_url, # 公司链接
                    'csv_filename':csv_filename
                }
        except Exception as e:
            logger.error('get job info failed:',url,e)
    return None

headers = ['职业名', '月薪', '公司名', '学历', '经验', '招聘人数', '公司亮点','城市', '上班地址',
               '创建时间', '更新时间', '截止时间', '行业', '公司类型', '公司总人数', '公司地址',
               '岗位描述', '职位链接', '信息', '公司网址']

def write_csv_headers(csv_filename):
    with open(csv_filename,'a',newline='',encoding='utf-8-sig') as f:
        f_csv = csv.DictWriter(f,headers)
        f_csv.writeheader()

def mycallback(data):
    if data:
        csv_filename = data.pop('csv_filename')
        with open(csv_filename,'a+',newline='',encoding='utf-8-sig') as f:
            f_csv = csv.DictWriter(f,data.keys())
            f_csv.writerow(data)

if __name__=='__main__':
    start_time = datetime.datetime.now()
    logger.info('*' * 20 + "start running spider!" + '*' * 20)
    old_url_l = load_progress('old_url.txt')
    manager = Manager()
    old_url = manager.list(old_url_l)
    if not os.path.exists(output_path):
        os.mkdir(output_path)
    for jobname in job_names:
        for cityname in city_names:
            pool = Pool()
            logger.info('*'*10+'start spider '+'jobname:'+jobname+'city:'+cityname+'*'*10)
            total_page = get_page_nums(cityname,jobname)
            csv_filename=output_path+'/{0}_{1}.csv'.format(jobname,cityname)
            if not os.path.exists(csv_filename):
                write_csv_headers(csv_filename)
            urls = get_urls(total_page, cityname, jobname)
            for url in urls:
                pool.apply_async(get_job_info,args=(url,old_url,csv_filename),callback=mycallback)
            pool.close()
            pool.join()
            logger.info('*'*10+'jobname:'+jobname+'city:'+cityname+' spider finished!'+'*'*10)
    save_progress(set(old_url), 'old_url.txt')
    end_time = datetime.datetime.now()
    logger.info('*' * 20 + "spider finished!Running time:%s" % (end_time - start_time) + '*' * 20)
    print("Running time:%s" % (end_time - start_time))