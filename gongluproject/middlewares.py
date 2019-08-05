# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/spider-middleware.html
from scrapy import signals
import requests
import json
import logging
from scrapy import signals
import base64
from .utils import fetch_one_proxy
import time
import random
from scrapy.conf import settings
from scrapy.utils.response import response_status_message
from scrapy.downloadermiddlewares.retry import RetryMiddleware

DOWNLOADER_MIDDLEWARES=settings.get("DOWNLOADER_MIDDLEWARES")
if "gongluproject.middlewares.KuaidailiMiddleware" in DOWNLOADER_MIDDLEWARES:
	proxy = fetch_one_proxy()
maxtime=settings.get("MAXTIME")
t=0
p=0
class AbuyunProxyMiddleware():
	def __init__(self,proxyuser,proxypass,proxyserver):
		self.proxyuser=proxyuser
		self.proxypass=proxypass
		self.proxyserver=proxyserver
		self.proxyauth = "Basic " + base64.urlsafe_b64encode(bytes((self.proxyuser + ":" + self.proxypass), "ascii")).decode("utf8")
	def process_request(self,request,spider):
		request.meta["proxy"] = self.proxyserver
		request.headers["Proxy-Authorization"] = self.proxyauth
		print("正在使用代理："+str(self.proxyserver))
	@classmethod
	def from_crawler(cls,crawler):
		return cls(
			proxyuser=crawler.settings.get("PROXYUSER"),
			proxypass=crawler.settings.get("PROXYPASS"),
			proxyserver=crawler.settings.get("PROXYSERVER"),
		)

class KuaidailiMiddleware():
	def __init__(self,username,password):
		self.username=username
		self.password=password
	def process_request(self, request, spider):
		proxy_url = 'http://%s:%s@%s' % (self.username, self.password, proxy)
		request.meta['proxy'] = proxy_url  # 设置代理
	@classmethod
	def from_crawler(cls,crawler):
		return cls(
			username=crawler.settings.get("KUAI_USERNAME"),
			password=crawler.settings.get("KUAI_PASSWORD")
			)
class MyRetryMiddleware(RetryMiddleware):
	logger = logging.getLogger(__name__)
	def process_response(selfself,request,response,spider ):
		print(response.status)
		global proxy, t
		if 400<=response.status<500 or response.status>=600:
			if t == 0:
				proxy = fetch_one_proxy()
				print('403更换代理' + proxy)
				t += 1
			else:
				t += 1
				if t >=maxtime:
					t=0
		return response
	def process_exception(self, request, exception, spider):
		global proxy,p
		if isinstance(exception, self.EXCEPTIONS_TO_RETRY) and not request.meta.get('dont_retry', False):
			if not isinstance(exception,TimeoutError):
				#更换代理
				print(exception)
				if p == 0:
					proxy = fetch_one_proxy()
					print('已更换代理' + proxy)
					p += 1
				else:
					p += 1
					if p >=maxtime:
						p=0
					print(p)

			return self._retry(request, exception, spider)
		else:
			print(exception)
			err = input("异常")

class MyUseragent():
	def process_request(self,request,spider):
		USER_AGENT_LIST = [
		'MSIE (MSIE 6.0; X11; Linux; i686) Opera 7.23',
		'Opera/9.20 (Macintosh; Intel Mac OS X; U; en)',
		'Opera/9.0 (Macintosh; PPC Mac OS X; U; en)',
		'iTunes/9.0.3 (Macintosh; U; Intel Mac OS X 10_6_2; en-ca)',
		'Mozilla/4.76 [en_jp] (X11; U; SunOS 5.8 sun4u)',
		'iTunes/4.2 (Macintosh; U; PPC Mac OS X 10.2)',
		'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:5.0) Gecko/20100101 Firefox/5.0',
		'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:9.0) Gecko/20100101 Firefox/9.0',
		'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:16.0) Gecko/20120813 Firefox/16.0',
		'Mozilla/4.77 [en] (X11; I; IRIX;64 6.5 IP30)',
		'Mozilla/4.8 [en] (X11; U; SunOS; 5.7 sun4u)'
			]
		agent = random.choice(USER_AGENT_LIST)
		request.headers['User_Agent'] =agent