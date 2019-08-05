# -*- coding: utf-8 -*-
import scrapy
from scrapy import FormRequest,Request
import json
from gongluproject.items import *
from scrapy_redis.spiders import RedisSpider
from scrapy.conf import settings

rows= settings.get("ROWS")
class GongluSpider(RedisSpider):
	name = 'gonglu'
	#allowed_domains = ['glxy.mot.gov.cn']
	redis_key='GongluSpider:start_urls'
	def parse(self,response):
		url1="https://glxy.mot.gov.cn/company/getCompanyAptitude.do"
		type_list=['0','1','2']
		for type in type_list:
			data1={
				'page':'1',
				'rows':rows,
				'type':type,  #0,1,2
				'text':''
				}
			yield FormRequest(url=url1,formdata=data1,callback=self.parsegonglu,meta={"type":type})

		for type in type_list:
			url="https://glxy.mot.gov.cn/person/getPersonList.do?type="+type
			data={
				'page':'1',
				'rows':'999999',
				'viewType':'1'
				}
			yield FormRequest(url=url,formdata=data,callback=self.parsperson,meta={"type":type})	
		
	def parsegonglu(self,response):
		company_list=json.loads(response.text).get('rows')
		for company in company_list:
			companyid = company.get('id')
			#companyid='1103819b44da4ba482bb6d1b1e2698c4'
			#企业基本信息
			url = "https://glxy.mot.gov.cn/company/CompanyInfo.do"
			data={
				'comId':companyid
			}
			yield scrapy.FormRequest(url=url,formdata=data,callback=self.getcompanyinfo,meta={"companyid":companyid})
			#人员基本信息
			if response.meta.get("type")=='1':
				url1="https://glxy.mot.gov.cn/person/getPersonList.do"
				type_list=['1','4']
				for type in type_list:
					data1={
						'type':type,  #企业类型4-监理行政  2-设计  0-施工  1-监理工程师
						'rows':'9999',
						'page':'1',
						'comId':companyid
						}
					yield scrapy.FormRequest(url=url1,formdata=data1,callback=self.getpersoninfo,meta={"companyid":companyid})
			#项目列表
				url3="https://glxy.mot.gov.cn/company/getCompanyAchieveList.do?companyId={}&type={}".format(companyid,'1')
				data3={
					'page':'1',
					'rows':'9999'
					}
				yield scrapy.FormRequest(url=url3,formdata=data3,callback=self.getproject,meta={"companyid":companyid})
			else:
				#人员基本信息
				url1="https://glxy.mot.gov.cn/person/getPersonList.do"
				data1={
					'type':response.meta.get("type"),  #企业类型4-监理行政  2-设计  0-施工  1-监理工程师
					'rows':'9999',
					'page':'1',
					'comId':companyid
					}
				yield scrapy.FormRequest(url=url1,formdata=data1,callback=self.getpersoninfo,meta={"companyid":companyid})
				#业绩信息
				type_list2=['11','12','21','22']
				source_list=['1','2','3']
				for type in type_list2:
					for source in source_list:
						url6="https://glxy.mot.gov.cn/company/getCompanyAchieveList.do?companyId={}&type={}".format(companyid,type)
						data={
								'page':'1',
								'rows':'9999',
								'sourceInfo':source,
								'projectname':'',
								'provinceSearch':''
							}
						yield scrapy.FormRequest(url6,formdata=data,callback=self.getprojectinfo)
				#良好行为记录
				url3="https://glxy.mot.gov.cn/awards/getAwardsList.do"
				data3={
					'page':'1',
					'rows':'9999',
					'comId':companyid
					}
				yield scrapy.FormRequest(url=url3,formdata=data3,callback=self.getAwardsList)
				#不良行为记录
				url4="https://glxy.mot.gov.cn/Punishment/getPunishmentList.do?companyId="+companyid
				data4={
					'page':'1',
					'rows':'9999'
					}
				yield scrapy.FormRequest(url=url4,formdata=data4,callback=self.getPunishmentList)
				#在各地信用等级
				url5="https://glxy.mot.gov.cn/evaluate/getEvaluateList.do"
				data5={
					'page':'1',
					'rows':'9999',
					'comId':companyid
					}
				yield scrapy.FormRequest(url=url5,formdata=data5,callback=self.getEvaluate)
			#企业资质
			url2="https://glxy.mot.gov.cn/company/getCompanyAptitudeList.do?comId="+companyid
			data2={
				'page':'1',
				'rows':'9999'
				}
			yield scrapy.FormRequest(url=url2,formdata=data2,callback=self.getaptitude,meta={"companyid":companyid})	
	#企业基本信息
	def getcompanyinfo(self,response):
		item=GongluprojectItem()
		item["content"] ={
			'collection':'companyinfo',
			'data':json.loads(response.text).get("data")
		}
		yield item	
	#人员基本信息		
	def getpersoninfo(self,response):
		rows=json.loads(response.text).get('rows')
		if len(rows):
			for data in rows:
				item=GongluprojectItem()
				item["content"]={
						'collection':'personinfo',
						'data':data
					}	
				yield item
	#企业资质
	def getaptitude(self,response):
		rows=json.loads(response.text).get('rows')
		if len(rows):
			for data in rows:
				item=GongluprojectItem()
				item["content"]={
						'collection':'aptitude',
						'data':data
					}
				yield item
	#项目列表
	def getproject(self,response):  
		pdata=json.dumps(json.loads(response.text).get("rows"),ensure_ascii=False)
		rows=json.loads(response.text).get("rows")
		for row in rows:
			projectid=row.get("project_id")
			#print(projectid)
			#获取项目详细信息
			method="post"
			url2="https://glxy.mot.gov.cn/project/getProjectInfo.do?id="+projectid
			yield scrapy.FormRequest(url=url2,callback=self.getprojectdetail)
			# #项目结构物信息
			url3="https://glxy.mot.gov.cn/ProjectStructure/getProjectStructureList.do"
			data3={
				'page':'1',
				'rows':'9999',
				'projectId':projectid
			}
			yield scrapy.FormRequest(url3,formdata=data3,callback=self.getProjectStructureList)
			# #施工合同段信息
			url4="https://glxy.mot.gov.cn/ProjectConsSegment/getProjectConsSegmentList.do"
			data4={
				'page':'1',
				'rows':'9999',
				'projectId':projectid
			}
			yield scrapy.FormRequest(url4,formdata=data4,callback=self.getProjectConsSegmentList)
			# #监理合同段信息
			url5="https://glxy.mot.gov.cn/ProjectSupervisorSegment/getProjectSupervisorSegmentList.do"
			data5={
				'page':'1',
				'rows':'9999',
				'projectId':projectid
			}
			yield scrapy.FormRequest(url5,formdata=data5,callback=self.getProjectSupervisorSegmentList)
			# #设计单位信息
			url6="https://glxy.mot.gov.cn/ProjectDesignCompany/getProjectDesignCompanyList.do"
			data6={
				'page':'1',
				'rows':'9999',
				'projectId':projectid
			}
			yield scrapy.FormRequest(url6,formdata=data6,callback=self.getProjectDesignCompanyList)
			# #检测工地实验室
			url7="https://glxy.mot.gov.cn/ProjectLab/getProjectLabList.do"
			data7={
				'page':'1',
				'rows':'9999',
				'projectId':projectid
			}
			yield scrapy.FormRequest(url7,formdata=data7,callback=self.getProjectLabList)
			# #项目分段设计信息
			url8="https://glxy.mot.gov.cn/ProjectDesign/getProjectDesignList.do"
			data8={
				'page':'1',
				'rows':'9999',
				'projectId':projectid,
				'type':'1'
				}
			yield scrapy.FormRequest(url8,formdata=data8,callback=self.getProjectDesignList)
		#获取项目人员信息
		url1="https://glxy.mot.gov.cn/company/getJLEngineerList.do"
		data1={
			'ids':pdata
		}
		yield scrapy.FormRequest(url=url1,formdata=data1,callback=self.getprojectperson)
	#获项目绩人员信息
	def getprojectperson(self,response):
		for key,value in json.loads(response.text).items():
			if value:
				for data in value:
					item=GongluprojectItem()
					item["content"]={
							'collection':'projectperson',
							'data':data
						}
					yield item
	#获取项目详细信息
	def getprojectdetail(self,response):
		data1=json.loads(response.text).get('data')
		item=GongluprojectItem()
		item["content"]={
				'collection':'projectdetail',
				'data':data1
			}
		yield item
		#项目竣工信息
		data2=json.loads(response.text).get('completeObj')
		if data2:
			for data in data2:
				item=GongluprojectItem()
				data['type']='complete'
				item["content"]={
						'collection':'projectfinish',
						'data':data
					}
				yield item
		data3=json.loads(response.text).get('finishObj')
		if data3:
			for data in data3:
				item=GongluprojectItem()
				data['type']='finish'
				item["content"]={
						'collection':'projectfinish',
						'data':data
					}
				yield item
	#项目结构物信息
	def getProjectStructureList(self,response):
		rows=json.loads(response.text).get('rows')
		if rows:
			for data in rows:
				item =GongluprojectItem()
				item["content"]={
						'collection':'projectstructure',
						'data':data
					}
				yield item
	#施工合同段信息
	def getProjectConsSegmentList(self,response):
		rows=json.loads(response.text).get('rows')
		if rows:
			for data in rows:
				item=GongluprojectItem()
				item["content"]={
						'collection':'projectconssegmentlist',
						'data':data
					}
				yield item
	#监理合同段信息
	def getProjectSupervisorSegmentList(self,response):
		rows=json.loads(response.text).get('rows')
		if rows:
			for data in rows:
				item=GongluprojectItem()
				item["content"]={
						'collection':'projectsupervisorsegment',
						'data':data
					}
				yield item
	#设计单位信息
	def getProjectDesignCompanyList(self,response):
		rows=json.loads(response.text).get('rows')
		if rows:
			for data in rows:
				item=GongluprojectItem()
				item["content"]={
						'collection':'projectdesigncompany',
						'data':data
					}
				yield item
	#检测工地实验室
	def getProjectLabList(self,response):
		rows=json.loads(response.text).get('rows')
		if rows:
			for data in rows:
				item = GongluprojectItem()
				item["content"]={
						'collection':'projectlab',
						'data':data
					}
				yield item
	#项目分段设计信息
	def getProjectDesignList(self,response):
		rows=json.loads(response.text).get('rows')
		if rows:
			for data in rows:
				item=GongluprojectItem()
				item["content"]={
						'collection':'projectdesign',
						'data':data
					}
				yield item 
	#业绩信息
	def getprojectinfo(self,response):
		rows=json.loads(response.text).get('rows')
		if len(rows):
			for data in rows:
				item=GongluprojectItem()
				item["content"]={
						'collection':'shigongprojectinfo',
						'data':data
					}	
				yield item
		#print(response.text)
	#良好行为记录
	def getAwardsList(self,response):
		rows=json.loads(response.text).get('rows')
		if len(rows):
			for data in rows:
				item=GongluprojectItem()
				item["content"]={
						'collection':'awards',
						'data':data
					}	
				yield item
		#print(response.text)
	#不良行为记录
	def getPunishmentList(self,response):
		rows=json.loads(response.text).get('rows')
		if len(rows):
			for data in rows:
				item=GongluprojectItem()
				item["content"]={
						'collection':'punishment',
						'data':data
					}	
				yield item
		#print(response.text)
	#在各地信用等级
	def getEvaluate(self,response):
		#print(response.text)
		rows=json.loads(response.text).get('rows')
		if len(rows):
			for data in rows:
				item=GongluprojectItem()
				item["content"]={
						'collection':'evaluate',
						'data':data
					}	
				yield item

	def parsperson(self,response):
		rows=json.loads(response.text).get('rows')
		if rows:
			for data in rows:
				personid=data.get('id')
				#执业资格信息
				url1='https://glxy.mot.gov.cn/person/getPersonPracticeCertList.do'
				data1={
					'page':'1',
					'rows':'9999',
					'perId':personid
				}
				yield FormRequest(url=url1,formdata=data1,callback=self.getPersonPracticeCert)
				#履历信息
				url2='https://glxy.mot.gov.cn/person/getPersonRecordList.do?perId='+personid
				data2={
					'page':'1',
					'rows':'9999'
				}
				yield FormRequest(url=url2,formdata=data2,callback=self.getPersonRecord)
				#业绩信息
				url3='https://glxy.mot.gov.cn/person/getPersonAchieveList.do'
				data3={
					'page':'1',
					'rows':'9999',
					'perId':personid
				}
				yield FormRequest(url=url3,formdata=data3,callback=self.getPersonAchieve)
				if response.meta.get("type")!="1":
					#职称信息
					url4='https://glxy.mot.gov.cn/person/getPersonAcademicList.do?perId='+personid
					data4={
						'page':'1',
						'rows':'9999'
					}
					yield FormRequest(url=url4,formdata=data4,callback=self.getPersonAcademic)
	#执业资格信息
	def getPersonPracticeCert(self,response):
		rows=json.loads(response.text).get('rows')
		if rows:
			for data in rows:
				item=GongluprojectItem()
				item["content"]={
						'collection':'personpracticecert',
						'data':data
					}
				yield item 
	#履历信息
	def getPersonRecord(self,response):
		rows=json.loads(response.text).get('rows')
		if rows:
			for data in rows:
				item=GongluprojectItem()
				item["content"]={
						'collection':'personrecord',
						'data':data
					}
				yield item 
	#业绩信息
	def getPersonAchieve(self,response):
		rows=json.loads(response.text).get('rows')
		if rows:
			for data in rows:
				item=GongluprojectItem()
				item["content"]={
						'collection':'personachieve',
						'data':data
					}
				yield item 
	#职称信息
	def getPersonAcademic(self,response):
		rows=json.loads(response.text).get('rows')
		if rows:
			for data in rows:
				item=GongluprojectItem()
				item["content"]={
						'collection':'personacademic',
						'data':data
					}
				yield item 