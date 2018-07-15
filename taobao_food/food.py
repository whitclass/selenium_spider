import re
import pymongo
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pyquery import PyQuery as pq
from urllib.parse import quote
from config import *




opt = webdriver.ChromeOptions()
opt.set_headless()
browser = webdriver.Chrome(options=opt)

# browser = webdriver.Chrome()
wait = WebDriverWait(browser, 10)
client = pymongo.MongoClient(MONGO_URL)
db = client[MONGO_DB]


def search():
	print('开始爬取第 1 页')
	try:
		url = 'https://s.taobao.com/search?q=' + quote(keyword)
		browser.get(url)
		wait.until(
			EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-itemlist .items .item')))
		get_products()
	except TimeoutException:
		return search()

def next_page(page):
	print('正在爬取第',page,'页')
	try:
		Input = wait.until(
		        EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.form > input')))
		Input.clear()
		Input.send_keys(str(page) + Keys.RETURN)
		wait.until(
			EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#mainsrp-pager > div > div > div > ul > li.item.active > span'),str(page)))
		get_products()
	except TimeoutException:
		return next_page(page)

def get_products():
	"""
	提取商品数据
	"""
	wait.until(
		EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-itemlist .items .item')))
	html = browser.page_source
	doc = pq(html)
	items = doc('#mainsrp-itemlist .items .item').items()
	for item in items:
		product = {
		'image':item.find('.pic .img').attr('src'),
		'price':re.compile(r'\n+').sub('',item.find('.price').text()),
		'deal':item.find('.deal-cnt').text(),
		'title':re.compile(r'\n+').sub('',item.find('.title').text()),
		'shop':item.find('.shop').text(),
		'location':item.find('.location').text()
		}
		print(product)
		save_Mongo(product)


def save_Mongo(result):
	"""
	保存至MongoDB
	:param result: 结果
	"""
	try:
		if db[MONGO_COLLECTION].insert(result):
			print('已存储MongoDB')
	except:
		print('存储失败')

def main():
	"""
	遍历每一页
	"""
	search()
	for i in range(2,max_page + 1):
		next_page(i)
	browser.close()

if __name__ == '__main__':
	main()