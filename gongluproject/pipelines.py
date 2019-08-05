# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import psycopg2
import datetime,time
import re
from pykafka import KafkaClient
from kafka import KafkaProducer
class GongluprojectPipeline(object):
	def process_item(self, item, spider):
		it=item.get("content")
		ite=it.get("data")
		new_dict = {}
		for key,value in ite.items():
			new_dict[key.lower()] = value
		for key,value in new_dict.items():
			if isinstance(value,str):
				result=re.findall('.*?>(.*?)<.*?',value,re.S)
				if result:
					new_dict[key]=''.join(result)
				if "出错页面" in value:
					new_dict[key]=''
		it["data"]=new_dict
		it["data"]["isdelete"]=0
		it["data"]["updatetime"]=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
		it["data"]["createtime"]=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
		return item
class WriteToSqlPipeline():
	def __init__(self,database,user,password,host,port):
		self.database=database
		self.user=user
		self.password=password
		self.host=host
		self.port=port
	def open_spider(self,spider):
		self.db=psycopg2.connect(database=self.database, user=self.user, password=self.password, host=self.host, port=self.port)
		self.cursor=self.db.cursor()
	def close_spider(self,spider):
		self.cursor.close()
		self.db.close()
	def process_item(self, item, spider):
		it=item.get("content")
		ite=it.get("data")
		for key,value in ite.items():
			if key =="end":
				ite['ends']=ite.pop('end')
			if key =="begin":
				ite['begins']=ite.pop('begin')
		sql="INSERT INTO {} (".format(it.get("collection"))
		v_list=[]
		k_list=[]
		for key,value in ite.items():
			#if value !="Null" and value !="-" and value !="":
			sql += "{},"
			v_list.append(ite[key])
			k_list.append(key)
		sql=sql.format(*k_list)[:-1]+")"+" VALUES ("
		for key,value in ite.items():
			#if value !="Null" and value !="-" and value !="":
			sql += "'{}',"
		sql=sql.format(*v_list)[:-1]+")"
		#print(sql)
		try:
			global jishu
			self.cursor.execute(sql)
			self.db.commit()
			print("写入成功-----"+it.get("collection"))
		except Exception as e:
			print(e)
			print(it)
			print(sql)
			self.db=psycopg2.connect(database=self.database, user=self.user, password=self.password, host=self.host, port=self.port)
			self.cursor=self.db.cursor()
			self.cursor.execute(sql)
			self.db.commit()
		return item
	@classmethod
	def from_crawler(cls,crawler):
		return cls(
			database=crawler.settings.get("PGSQL_DATABASE"),
			user=crawler.settings.get("PGSQL_USER"),
			password=crawler.settings.get("PGSQL_PASSWORD"),
			host=crawler.settings.get("PGSQL_HOST"),
			port=crawler.settings.get("PGSQL_PORT")
			)

class ScrapyKafkaPipeline(object):
	def __init__(self,kafka_ip_port,topic):
		self.kafka_ip_port = kafka_ip_port
		self.topic=topic
	def open_spider(self,spider):
		self._client = KafkaClient(hosts=self.kafka_ip_port)
		self._producer = self._client.topics[self.topic.encode(encoding="UTF-8")].get_producer()
		print("已连接队列")
	def close_spider(self,spider):
		self._producer.stop()
		print("已退出队列")
	def process_item(self, item, spider):
		try:
			self._producer.produce(json.dumps(item,ensure_ascii=False).encode(encoding="UTF-8"))
		except:
			self._producer = self._client.topics[self.topic.encode(encoding="UTF-8")].get_producer()
		return item
	@classmethod
	def from_crawler(cls,crawler):
		return cls(
			kafka_ip_port=crawler.settings.get("BOOTSTRAP_SERVER"),
			topic=crawler.settings.get("TOPIC")
			)
