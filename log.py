# !usr/bin/env python3
# -*- coding:utf-8 -*- 
"""
@project = Spider_zhilian
@file = log
@author = Easton Liu
@time = 2018/10/20 21:42
@Description: 定义日志输出，同时输出到文件和控制台

"""
import logging
import os
from logging.handlers import TimedRotatingFileHandler


class Logger:
    def __init__(self, logger_name='easton'):
        self.logger = logging.getLogger(logger_name)
        logging.root.setLevel(logging.NOTSET)
        self.log_file_name = 'spider_zhilian.log'
        self.backup_count = 5
        # 日志输出级别
        self.console_output_level = 'WARNING'
        self.file_output_level = 'DEBUG'
        # 日志输出格式
        pattern='%(asctime)s - %(levelname)s - %(message)s'
        self.formatter = logging.Formatter(pattern)
        # 日志路径
        if not os.path.exists('log'):
            os.mkdir('log')
        self.log_path = os.path.join(os.getcwd(),'log')


    def get_logger(self):
        """在logger中添加日志句柄并返回，如果logger已有句柄，则直接返回"""
        if not self.logger.handlers:
            console_handler=logging.StreamHandler()
            console_handler.setFormatter(self.formatter)
            console_handler.setLevel(self.console_output_level)
            self.logger.addHandler(console_handler)

            # 每天重新创建一个日志文件，最多保留backup_count份
            file_handler = TimedRotatingFileHandler(filename=os.path.join(self.log_path, self.log_file_name),
                                                    when='D',
                                                    interval=1,
                                                    backupCount=self.backup_count,
                                                    delay=True,
                                                    encoding='utf-8'
                                                    )
            file_handler.setFormatter(self.formatter)
            file_handler.setLevel(self.file_output_level)
            self.logger.addHandler(file_handler)
        return self.logger
logger = Logger().get_logger()



