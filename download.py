import os, glob, requests, re, logging
from urllib.parse import urljoin
from pathlib import Path
from bs4 import BeautifulSoup
from requests.exceptions import ConnectionError


def log_info(message, path):
	filename = ''
	if path.split('\\')[-1] != '':
		filename = os.path.join(path, path.split('\\')[-1])
	else:
		filename = os.path.join(path, path.split('\\')[-2])
	logging.basicConfig(filename=f"{filename}.txt", level=logging.INFO, format="%(asctime)s %(message)s")
	logging.info(message)



class BaseDownloader:
	''' 
		base_url : 
		album_url : 
		album_url_list : 
		image_url_list : 
		save_to : Specify path to save the album images. Default is current running folder.
		unique : If True will save image with a unique number if already exist. Default is False
		headers : Specify headers to get request to blocking websites.
	'''
	hash = ''
	base_url = None
	album_url = None
	album_url_list = list()
	image_url_list = list()
	save_to = None
	unique = True
	headers = {
		"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36",
		'Accept-Encoding': '*',
		'Accept': '*/*',
		'Connection': 'keep-alive'
	}

	def __init__(self, link, path=None, headers=None):

		self._update_urls(link)
		if path:
			self.save_to = os.path.normpath(path)
		else:
			self.save_to = os.getcwd()
		if headers:
			self.headers = headers
		

	def info(self):
		print("base_url:", self.base_url)
		print("album_url:", self.album_url)
		print("album_url_list:", self.album_url_list)
		print("image_url_list:", self.image_url_list)
		print("save_to:", self.save_to)
		log_info("base_url:" + self.base_url, self.save_to)
		log_info("album_url:" + self.album_url, self.save_to)
		log_info("album_url_list:" + self.album_url_list, self.save_to)
		log_info("image_url_list:" + self.image_url_list, self.save_to)
		log_info("save_to:" + self.save_to, self.save_to)

	def url_type(self, url):
		try:
			r = requests.head(url, headers=self.headers)
			if r.headers["content-type"] in ("text/html; charset=utf-8"):
				return "html"
			if r.headers["content-type"] in ("image/png", "image/jpeg", "image/jpg"):
				return "image"
			return None
		except ConnectionError:
			return self.url_type(url)

	def _update_urls(self, link):
		if isinstance(link, list):
			for url in link:
				self.album_url_list.append(url)
		elif self.url_type(link) == "image":
			self.image_url_list.append(link)
		elif self.url_type(link) == "html":
			self.album_url = link
		else:
			raise TypeError("{} type is not allowed".format(link))

	def get_hash(self, value):
		return ''

	def get_album_images(self):
		""" Implemented must be return a list datatype. """
		raise NotImplementedError(
			'{} is missing the implementation of the get() method.'.format(self.__class__.__name__)
		)

	def uniquify(self, filename):
		''' return the name filename with extension or 
			also if name exist then return with count '''
		path = Path(self.save_to)
		search_current = path.glob(filename + '*')
		exist_len = len(list(search_current)) 
		filename = filename.replace('.', f'({exist_len}).')
		return filename

	def _save(self, url, count=None, hash=None):
		''' Save a single image from a url '''
		name = url.split("/")[-1]
		name, ext = os.path.splitext(name)
		filename = name + hash + ext
		filepath = os.path.join(self.save_to, filename)
		if os.path.exists(filepath) and self.unique:
			filename = self.uniquify(filename.split(".")[0])
			filepath = os.path.join(self.save_to, filename)
		
		if not os.path.exists(filepath):
			content = requests.get(url, headers=self.headers).content
			with open(filepath, "wb") as file:
				file.write(content)
				if count:
					log_info("Saved: {}) {}".format(count, filename), self.save_to)
					print("Saved: {}) {}".format(count, filename))
				else:
					log_info("Single image is Saved", self.save_to)
					print("Single image is Saved")
		else:
			log_info("Already image is Saved", self.save_to)
			print("Already image is Saved")

	def _save_bulk(self, urls, hash=None):
		''' It download the list of images in urls '''
		count = 0
		for i, link in enumerate(urls):
			count = i + 1
			self._save(link, count, hash)
		log_info("Successfully completed" + str(count) + "files.", self.save_to)
		print("Successfully completed", str(count), "files.")

	def download(self, link=None):
		if link is not None:
			self._update_urls(link)

		if self.album_url:
			hash = self.get_hash(self.album_url)
			log_info('Getting album url data from url "{}"'.format(self.album_url), self.save_to)
			print('Getting album url data from url "{}"'.format(self.album_url))
			image_urls_list = set(self.get_album_images(self.album_url))
			self._save_bulk(image_urls_list, hash)
		
		for i, album_url in enumerate(self.album_url_list):
			count = i + 1
			hash = self.get_hash(album_url)
			log_info('{}) Getting album url data from url "{}"'.format(count, album_url), self.save_to)
			print('{}) Getting album url data from url "{}"'.format(count, album_url))
			image_urls_list = set(self.get_album_images(album_url))
			self._save_bulk(image_urls_list, hash)



class RaghalaHari(BaseDownloader):
	def __init__(self, url, path=None, headers=None):
		self.base_url = "https://www.ragalahari.com/"
		self.unique = False
		super().__init__(url, path, headers)

	def get_hash(self, value):
		return "-" + str(int(value.split("/")[4]))

	def get_album_images(self, album_link):
		list_link = list()
		try:
			r = requests.get(album_link, headers=self.headers).text
			soup1 = BeautifulSoup(r, 'lxml')
			div1 = soup1.select('#galdiv a')
			for href in div1:
				url = urljoin(self.base_url, href.get('href'))
				r = requests.get(url, headers=self.headers).text
				soup2 = BeautifulSoup(r, 'lxml')
				div2 = soup2.select('#galimgview img')
				for e in div2:
					list_link.append(e.get('src'))
		except ConnectionError:
			return self.get_album_images()
		else:
			log_info("Found images: {}".format(len(list_link)), self.save_to)
			print("Found images: {}".format(len(list_link)))
			return list_link

	def print_album_link(self):
		list_link = list()
		try:
			r = requests.get(self.album_url, headers=self.headers).text
			soup = BeautifulSoup(r, 'lxml')
			div = soup.select("#galleries_panel .galimg")
			for element in div:
				url = urljoin(self.base_url, element.get('href'))
				list_link.append(url)
		except ConnectionError:
			return self.print_album_link(self.album_url)
		else:
			log_info("Found album link: {}".format(len(list_link)), self.save_to)
			print("Found album link: {}".format(len(list_link)))
			return list_link

	@staticmethod
	def get_actress_album_link2(profile_url):
		base_url = "https://www.ragalahari.com/"
		list_link = list()
		headers = {
			"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36",
			'Accept-Encoding': '*',
			'Accept': '*/*',
			'Connection': 'keep-alive'
		}
		try:
			r = requests.get(profile_url, headers=headers).text
			soup1 = BeautifulSoup(r, 'lxml')
			div1 = soup1.select("#galleries_panel .galimg")
			for element1 in div1:
				url1 = urljoin(base_url, element1.get('href'))
				r2 = requests.get(url1, headers=headers).text
				soup2 = BeautifulSoup(r2, 'lxml')
				div2 = soup2.select("#pagingCell a")
				if div2:
					for element2 in div2:
						url2 = urljoin(base_url, element2.get('href'))
						list_link.append(url2)

				list_link.append(url1)
		except ConnectionError:
			return get_actress_album_link(profile_url)
		else:
			print("Found images: {}".format(len(list_link)))
			return set(list_link)


class PornPics(BaseDownloader):
	def __init__(self, url, path=None, headers=None):
		self.base_url = "https://www.pornpics.com/"
		self.unique = False
		super().__init__(url, path, headers)

	def get_album_images(self, album_link):
		list_link = list()
		try:
			r = requests.get(album_link, timeout=30*100, headers=self.headers).text
			soup = BeautifulSoup(r, 'lxml')
			image_links = soup.find_all(class_="rel-link", href=True)
			list_link = [image['href'] for image in image_links]
		except ConnectionError:
			return self.get_album_images(album_link)
		else:
			log_info("Found images: {}".format(len(list_link)), self.save_to)
			print("Found images: {}".format(len(list_link)))
			return set(list_link)




folder_path = "F:/Important/Foreign/Karmen Bella/"

# for url in links[40:55]:
# 	if "pornpics" in url.split("."):
# 		a = PornPics(url, folder_path)
# 		a.download()







def save_ar():
	links = ['https://www.ragalahari.com/actress/164947/aishwarya-rajesh-hd-photos-at-creative-commercials-production-no-46-muhurat.aspx', 'https://www.ragalahari.com/actress/166708/aishwarya-rajesh-at-kousalya-krishnamurthy-pre-release-event.aspx', 'https://www.ragalahari.com/actress/170163/aishwarya-rajesh-at-republic-movie-pre-release-event-hd-photo-gallery.aspx', 'https://www.ragalahari.com/actress/164765/aishwarya-rajesh-photo-gallery.aspx', 'https://www.ragalahari.com/actress/166726/aishwarya-rajesh-at-kousalya-krishnamurthy-success-meet-hd-photos.aspx', 'https://www.ragalahari.com/actress/166861/aishwarya-rajesh-stills-at-siima-2019-exclusive-high-definition-photos.aspx', 'https://www.ragalahari.com/actress/167889/aishwarya-rajesh-at-world-famous-lover-interview-hd.aspx', 'https://www.ragalahari.com/actress/166762/aishwarya-rajesh-at-kousalya-krishnamurthy-interview.aspx', 'https://www.ragalahari.com/actress/170117/aishwarya-rajesh-at-siima-awards-2021-day-2-hd-photo-gallery.aspx', 'https://www.ragalahari.com/actress/166370/aishwarya-rajesh-poses-during-kousalya-krishnamurthy-audio-release.aspx', 'https://www.ragalahari.com/actress/167988/aishwarya-rajesh-at-world-famous-lover-pre-release-event.aspx', 'https://www.ragalahari.com/actress/170165/1/aishwarya-rajesh-at-republic-movie-interview-hd-photo-gallery.aspx', 'https://www.ragalahari.com/actress/166371/aishwarya-rajesh-at-mis-s-match-movie-press-meet.aspx', 'https://www.ragalahari.com/actress/167889/1/aishwarya-rajesh-at-world-famous-lover-interview-hd.aspx', 'https://www.ragalahari.com/actress/167454/aishwarya-rajesh-at-miss-match-movie-pre-release.aspx', 'https://www.ragalahari.com/actress/170165/aishwarya-rajesh-at-republic-movie-interview-hd-photo-gallery.aspx']
	path = "F:\Important\Ragalahari\Aishwriya Rajesh"
	a = RaghalaHari("https://www.ragalahari.com/actress/164765/aishwarya-rajesh-photo-gallery.aspx", path)
	a.download()

save_ar()
