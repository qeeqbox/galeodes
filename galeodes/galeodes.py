from requests import get
from zipfile import ZipFile
from contextlib import suppress
from os import path, remove, chmod, stat
from tarfile import open as taropen
from pathlib import Path
from shutil import rmtree
from base64 import b64encode
from itertools import repeat, islice
from concurrent.futures import ThreadPoolExecutor, as_completed, wait, ALL_COMPLETED, TimeoutError, wait
from PIL import Image
from io import BytesIO
from logging import getLogger, DEBUG, basicConfig
from stat import ST_MODE
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as chromeservice
from selenium.webdriver.chrome.options import Options as chromeoptions
from selenium.webdriver.firefox.service import Service as firefoxservice
from selenium.webdriver.firefox.options import Options as firefoxoptions

class Galeodes():
	def __init__(self,**kwargs):
		self.browser = kwargs.get('browser', None)
		self.location = kwargs.get('location', None) or path.join(path.dirname(path.realpath(__file__)),"drivers")
		self.full_path = {}
		self.arguments = kwargs.get('arguments', None)
		self.options = kwargs.get('options', None)
		self.implicit_wait = kwargs.get('implicit_wait', 1)
		self.verbose = kwargs.get('verbose', None)
		basicConfig()
		self.log = getLogger('galeodes')
		self.log.setLevel(DEBUG)
		Path(self.location).mkdir(parents=True, exist_ok=True)
		temp_chrome = path.join(path.dirname(path.realpath(__file__)),"drivers","chromedriver")
		temp_firefox = path.join(path.dirname(path.realpath(__file__)),"drivers","geckodriver")
		if path.exists(temp_chrome):
			self.verbose and self.log.info("chromedriver exists! {}".format(temp_chrome))
			if str(oct(stat(temp_chrome)[ST_MODE])[-3:]) == '755':
				self.full_path["chromedriver"] = temp_chrome
				self.verbose and self.log.info("chromedriver permissions are good!")
			else:
				self.verbose and self.log.info("chromedriver permissions are wrong!")
		if path.exists(temp_firefox):
			self.verbose and self.log.info("geckodriver exists! {}".format(temp_firefox))
			if str(oct(stat(temp_firefox)[ST_MODE])[-3:]) == '755':
				self.full_path["geckodriver"] = temp_firefox
				self.verbose and self.log.info("geckodriver permissions are good!")
			else:
				self.verbose and self.log.info("geckodriver permissions are wrong!")
		self.get_driver()

	def get_driver(self, force=False):
		if self.browser == "chrome" and "chromedriver" in self.full_path:
			return self.full_path["chromedriver"]
		elif self.browser == "firefox" and "geckodriver" in self.full_path:
			return self.full_path["geckodriver"]
		if force:
			self.verbose and self.log.info("Removing {}".format(self.location))
			rmtree(self.location)
		if self.browser == "chrome":
			return self.get_chrome_driver()
		elif self.browser == "firefox":
			return self.get_firefox_driver()
		return {}

	def get_chrome_driver(self):
		location = {}
		self.verbose and self.log.info("Downloading chrome driver")
		with suppress(Exception):
			latest_release = get("https://chromedriver.storage.googleapis.com/LATEST_RELEASE", allow_redirects=True).text
			file = get("https://chromedriver.storage.googleapis.com/{}/chromedriver_linux64.zip".format(latest_release), allow_redirects=True)
			with open("chromedriver_linux64.zip", 'wb') as f:
				f.write(file.content)
			with ZipFile("chromedriver_linux64.zip","r") as zf:
				zf.extractall(self.location)
				for name in zf.namelist():
					location[name] = path.join(self.location,name)
					self.full_path.update({name:path.join(self.location,name)})
					if name == "chromedriver":
						self.verbose and self.log.info("Changing chromedriver permissions to 0755")
						chmod(path.join(self.location,name), 0o755)
						self.verbose and self.log.info("Chrome driver looks good")
			remove("chromedriver_linux64.zip")
		return location

	def get_firefox_driver(self):
		location = {}
		self.verbose and self.log.info("Downloading firefox driver")
		with suppress(Exception):
			latest_release = get("https://api.github.com/repos/mozilla/geckodriver/releases/latest", allow_redirects=True).json()["tag_name"]
			file = get("https://github.com/mozilla/geckodriver/releases/download/{}/geckodriver-{}-linux64.tar.gz".format(latest_release,latest_release), allow_redirects=True)
			with open("geckodriver-linux64.tar.gz", 'wb') as f:
				f.write(file.content)
			with taropen("geckodriver-linux64.tar.gz","r") as tar:
				tar.extractall(path=self.location)
				for file in tar.getmembers():
					location[file.name] = path.join(self.location,file.name)
					self.full_path.update({file.name:path.join(self.location,file.name)})
					if file.name == "geckodriver":
						self.verbose and self.log.info("Changing geckodriver permissions to 0755")
						chmod(path.join(self.location,file.name), 0o755)
						self.verbose and self.log.info("Firefox driver looks good")
			remove("geckodriver-linux64.tar.gz")
		return location

	def setup_driver(self):
		driver = None
		with suppress(Exception):
			if self.browser != None and self.full_path:
				if self.browser == "chrome" and "chromedriver" in self.full_path:
					web_options= chromeoptions()
					if self.arguments:
						for argument in self.arguments:
							web_options.add_argument(argument)
					service = chromeservice(self.full_path["chromedriver"])
					driver = webdriver.Chrome(service=service, options=web_options)
			if self.browser != None and self.full_path:
				if self.browser == "firefox" and "geckodriver" in self.full_path:
					web_options= firefoxoptions()
					if self.options:
						for option in self.options:
							web_options.set_preference(option[0],option[1])
					if self.arguments:
						for argument in self.arguments:
							web_options.add_argument(argument)
					service = firefoxservice(self.full_path["geckodriver"])
					driver = webdriver.Firefox(service=service, options=web_options)
		return driver

	def get_page(self,driver,urls,kwargs):
		ret = []
		page_source = ""
		page_image = ""
		for url in urls:
			temp_item = {'url':url,'source':None, 'image':None}
			with suppress(Exception):
				driver.get(url)
				temp_item['source'] = driver.page_source
				if kwargs.get('screenshots', None):
					if kwargs.get('format', None) == "png":
						if kwargs.get('base64', None):
							temp_item['image'] = b"data:image/png;base64,"+b64encode(driver.get_screenshot_as_png())
						else:
							temp_item['image'] = driver.get_screenshot_as_png()
					elif kwargs.get('format', None) == "jpeg":
						im = Image.open(BytesIO(driver.get_screenshot_as_png()))
						byte_io = BytesIO()
						rgb_im = im.convert('RGB')
						rgb_im.save(byte_io, quality=50, optimize=True, format="jpeg")
						byte_io.seek(0)
						if kwargs.get('base64', None):
							temp_item['image'] = b"data:image/jpeg;base64,"+b64encode(byte_io.read())
						else:
							temp_item['image'] = byte_io.read()
			ret.append(temp_item)
		return ret

	def get_pages(self,**kwargs):
		futures = []
		with suppress(Exception):
			if kwargs.get('number_of_workers', 1) > 1:
				kwargs['urls'] = [kwargs['urls'][i:i + kwargs.get('number_of_workers', 1)] for i in range(0, len(kwargs['urls']), kwargs.get('number_of_workers', 1))]
			drivers = [self.setup_driver() for _ in range(len(kwargs['urls']))]
			with ThreadPoolExecutor(max_workers=kwargs.get('number_of_workers', 1)) as executor:
				with suppress(Exception):
					future_fetch_url =[]
					results = []
					#executor.map(self.get_page,kwargs['urls'],drivers,repeat(kwargs))
					for _ in range(len(kwargs['urls'])):
						if drivers[_] != None:
							future_fetch_url.append(executor.submit(self.get_page,drivers[_],kwargs['urls'][_],kwargs))
						future_fetch_url, _ = wait(future_fetch_url,timeout=60)
					for future in future_fetch_url:
						results.extend(future.result())
			for driver in drivers:
				with suppress(Exception):
					driver.close()
					driver.quit()
		return results
