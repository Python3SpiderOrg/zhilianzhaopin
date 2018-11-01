# zhilianzhaopin
根据职位名称和地点爬取智联招聘上职位信息：

zhilian.py:为单进程爬取

zhilian_proc.py:为多进程爬取，实测了下，爬取速度为单进程的三倍，在没有靠谱的代理情况下，不建议多进程，不然分分钟被封IP

输出为CSV文件，并根据职位名和城市名自动命名

记录了整个爬虫过程中的日志

对每个已爬取的URL进行了hashlib加密，取中间16位字符，爬取结束后序列化保存到本地磁盘，在下次爬取的时候反序列化加载，实现增量爬取
