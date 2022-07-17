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







# return ValueError("Operation terminated no url found.")
# if len(self.get_images()) == 1:
# 	self.image_url_list.append()
# print("Successfully completed", filename, "files.")
# raise ValueError("Operation terminated no url found.")
# raise ValueError("Operation terminated no urls list found.")


# # if "pornpics" in url.split("."):
# # 	self.get_img_links()

# get_actress_album_ragalahari(a_r)
# download_actress_albums_ragalahari(links, path)











links = [
"https://www.pornpics.com/galleries/black-haired-latina-teen-karmen-bella-rubs-her-swollen-twat-on-a-chair-24502267/",
"https://www.pornpics.com/galleries/young-and-busty-latina-pornstar-karmen-bella-taking-cumshot-on-pretty-face-95970298/",
"https://www.pornpics.com/galleries/exotic-teen-karmen-bella-flaunts-her-plump-tits-spreads-her-shaved-pussy-11968178/",
"https://www.pornpics.com/galleries/black-haired-latina-karmen-bella-shows-her-swollen-pussy-lips-and-round-butt-44959163/",
"https://www.pornpics.com/galleries/slender-exotic-girl-with-sexy-black-nails-and-hot-pussy-lips-karmen-bella-46905952/",
"https://www.pornpics.com/galleries/latina-pornstar-karmen-bella-hooks-up-with-the-pool-boys-big-black-dick-66093636/",
"https://www.pornpics.com/galleries/latina-babe-in-a-pink-dress-shows-her-gorgeous-big-tits-and-stretches-pussy-54887409/",
"https://www.pornpics.com/galleries/hot-latina-karmen-bella-touches-her-meaty-pussy-and-hot-ass-cheeks-14499359/",
"https://www.pornpics.com/galleries/latinamerican-chick-karmen-bella-releases-her-meaty-labia-lips-from-bikini-62999500/",
"https://www.pornpics.com/galleries/skinny-latina-karmen-bella-shows-her-ass-and-swollen-pussy-after-stripping-18306490/",
"http://hosted.foxes.com/p/G500CMBUFI/2594047",
"https://www.pornpics.com/galleries/sexy-brunette-teenager-karmen-bella-giving-long-cock-a-blowjob-85276937/",
"https://www.pornpics.com/galleries/solo-girl-with-black-hair-karmen-bella-stretches-her-gaped-pussy-21346818/",
"https://www.pornpics.com/galleries/atk-exotics-karmen-bella-83597904/",
"https://www.pornpics.com/galleries/american-with-thin-body-karmen-bella-strips-and-presents-her-swollen-cunt-36315705/",
"https://www.pornpics.com/galleries/exotic-lady-karmen-bella-strips-nude-and-teases-with-her-delicious-cunt-36009159/",
"https://www.pornpics.com/galleries/sultry-latina-teen-karmen-bella-gives-a-lovely-bj-before-riding-a-bbc-in-pov-58185319/",
"https://www.pornpics.com/galleries/adorable-latina-karmen-bella-displays-her-perfect-feet-and-meaty-pussy-lips-58657093/",
"https://www.pornpics.com/galleries/sexy-latina-teen-karmen-bella-humps-a-strangers-rock-hard-dick-on-the-bus-12141052/",
"https://www.pornpics.com/galleries/naturally-busty-latina-karmen-bella-shows-a-hot-closeup-of-her-meaty-pussy-58942879/",
"https://www.pornpics.com/galleries/stunning-latina-karmen-bella-flaunting-her-sexy-ass-and-big-clitoris-48601664/",
"https://www.pornpics.com/galleries/slim-girl-with-black-hair-karmen-bella-plays-with-her-meat-curtains-62642472/",
"https://www.pornpics.com/galleries/cock-loving-ebony-babe-karmen-bella-sucks-a-monster-white-dick-81853318/",
"https://www.pornpics.com/galleries/exotic-latina-beauty-karmen-bella-giving-exciting-closeups-of-her-spread-pussy-64245065/",
"https://www.pornpics.com/galleries/sexy-latina-karmen-bella-takes-off-her-hot-dress-exposes-her-big-clitoris-29344513/",
"https://www.pornpics.com/galleries/sultry-brunette-karmen-bella-gets-cum-on-face-after-fucking-a-long-penis-13031036/",
"https://www.pornpics.com/galleries/sexy-indian-babe-karmen-bell-spreads-her-teen-cunt-after-stripping-63375245/",
"https://www.pornpics.com/galleries/exotic-teen-babe-karmen-bella-on-all-fours-spreading-her-tight-ass-cheeks-56183058/",
"https://www.pornpics.com/galleries/pretty-latina-model-karmen-bella-releasing-firm-boobs-and-bald-cunt-from-dress-32447328/",
"https://www.pornpics.com/galleries/latina-babe-in-black-lingerie-karmen-bella-shows-natural-tits-and-her-pistol-60963016/",
"https://www.pornpics.com/galleries/college-girl-karmen-bella-ditches-her-tights-prior-to-a-hardcore-fuck-40212695/",
"https://www.pornpics.com/galleries/darkhaired-indian-teen-karmen-bella-partakes-in-hardcore-sex-pov-style-37461041/",
"https://www.pornpics.com/galleries/large-breasted-exotic-looking-babe-karmen-bella-fondling-own-boobs-67690738/",
"https://www.pornpics.com/galleries/latina-brunette-karmen-bella-gets-her-bald-pussy-fucked-gets-a-huge-facial-51205759/",
"https://www.pornpics.com/galleries/busty-latina-teenager-karmen-bella-gets-on-her-knees-to-deliver-blowjob-51848387/",
"https://www.pornpics.com/galleries/cute-latina-karmen-bella-displays-her-lovely-tits-and-stretches-her-twat-lips-10984620/",
"https://www.pornpics.com/galleries/fit-latina-teen-karmen-bella-strips-off-and-teases-with-natural-tits-12329015/",
"https://www.pornpics.com/galleries/beautiful-sexy-latina-teen-gets-her-smooth-pussy-banged-closeup-sucks-pov-72095447/",
"https://www.pornpics.com/galleries/provocative-karmen-bella-takes-off-her-sexy-red-lingerie-and-clothes-47573618/",
"https://www.pornpics.com/galleries/big-tit-babe-karmen-bella-posing-in-high-heels-and-frilly-skirt-65324641/",
"https://www.pornpics.com/galleries/beautiful-brunette-latina-karmen-bella-on-her-knees-catching-a-massive-facial-67965465/",
"https://www.pornpics.com/galleries/big-titted-latina-teen-reveals-her-soft-smooth-body-spreads-pussy-lips-94168073/",
"https://www.pornpics.com/galleries/latina-teen-in-white-stockings-karmen-bella-gets-her-mouth-filled-with-cum-84155834/",
"https://www.pornpics.com/galleries/naked-latina-teen-karmen-bella-having-bald-twat-fingered-and-fucked-62861829/",
"https://www.pornpics.com/galleries/attractive-latina-karmen-bella-spreads-her-legs-to-show-her-tasty-vagina-11832062/",
"https://www.pornpics.com/galleries/latina-pornstar-karmen-bella-jerking-and-sucking-a-massive-cock-32527496/",
"https://www.pornpics.com/galleries/busty-babe-karmen-bella-spreading-her-shaved-pussy-and-asshole-75522693/",
"https://www.pornpics.com/galleries/latina-slut-karmen-bella-on-knees-to-give-massive-black-penis-a-blowjob-81282927/",
"https://www.pornpics.com/galleries/smashing-brunette-shows-off-pussy-and-her-big-boobs-in-outdoor-natural-scenes-15963894/",
"https://www.pornpics.com/galleries/flexible-teen-karmen-bella-does-exercise-while-stripping-and-spreads-her-pussy-48719283/",
"https://www.pornpics.com/galleries/exotic-karmen-bella-licking-balls-with-tongue-and-takes-facial-cumshot-50876119/",
"https://www.pornpics.com/galleries/latina-karmen-bella-fellates-her-guy-in-hot-69-kneels-for-open-mouth-facial-82968943/",
"https://www.pornpics.com/galleries/latina-chick-gets-juiced-up-on-coco-frio-and-fucks-her-new-man-friend-64802049/",
"http://hosted.foxes.com/p/FKXFR63JR2/2594047",
"https://www.pornpics.com/galleries/hot-latina-karmen-bella-giving-a-deepthroat-blowjob-and-banging-hardcore-77160837/",
"https://www.pornpics.com/galleries/brunette-hottie-karmen-bella-getting-fucked-doggystyle-on-public-bus-85842655/",
"https://www.pornpics.com/galleries/beautiful-latina-pornstar-karmen-bella-plants-shaved-pussy-on-long-cock-51403935/",
"https://www.pornpics.com/galleries/busty-latina-karmen-bella-bent-over-for-big-black-doggystyle-dick-78477065/",
"https://www.pornpics.com/galleries/sexy-babe-model-karmen-bella-showing-off-her-hard-muscled-body-45042357/",
"https://www.pornpics.com/galleries/brunette-karmen-bella-with-big-nipples-gets-cum-on-face-after-hot-blowjob-48353139/",
"https://www.pornpics.com/galleries/latina-hottie-karmen-bella-gets-pussy-face-fucked-a-drippy-cum-facial-59254076/",
"https://www.pornpics.com/galleries/lolly-sporting-teen-karmen-bella-gets-herself-naked-to-spread-hot-ass-cheeks-70075258/",
"https://www.pornpics.com/galleries/hot-teen-latina-model-karmen-bella-spreading-ass-cheeks-for-butt-fuck-16651554/",
"https://www.pornpics.com/galleries/latina-teen-karmen-bela-gets-juicy-pussy-licked-and-anal-penetration-92308100/",
"https://www.pornpics.com/galleries/exotic-looking-girlfriend-karmen-bella-spreads-her-pink-pussy-lips-86959055/",
"https://www.pornpics.com/galleries/sporty-latina-babe-karmen-bella-showing-off-phat-thong-covered-teen-ass-16847415/",
"https://www.pornpics.com/galleries/naughty-latina-karmen-bella-strips-her-veil-and-rides-ryan-madisons-dick-99754575/",
"https://www.pornpics.com/galleries/stunning-teenage-latina-karmen-bella-touches-her-muff-after-showing-her-boobs-60044787/",
"https://www.pornpics.com/galleries/dark-haired-girl-karmen-bella-touts-her-tight-ass-after-removing-bra-panties-56396012/",
"https://www.pornpics.com/galleries/busty-brunette-latina-karmen-bella-getting-banged-by-long-dick-91409851/",
"https://www.pornpics.com/galleries/latina-teenager-karmen-bella-modeling-in-red-dress-before-stripping-naked-79564325/",
"https://www.pornpics.com/galleries/slender-teen-karmen-bella-has-her-pretty-face-medium-tits-sprayed-with-cum-62251984/",
"https://www.pornpics.com/galleries/latina-pornstar-karmen-bella-taking-cumshot-on-face-and-tongue-57998855/",
"https://www.pornpics.com/galleries/american-latina-with-a-skinny-body-karmen-bellagets-fucked-in-pov-24852632/",
"https://www.pornpics.com/galleries/indian-teenager-karmen-bella-sucks-cock-pov-and-takes-hardcore-anal-81611636/",
"https://www.pornpics.com/galleries/dick-loving-latina-karmen-bella-giving-great-head-and-getting-a-facial-20266494/",
"https://www.pornpics.com/galleries/black-haired-amateur-karmen-bella-deepthroats-big-dick-with-pov-cumshot-on-ass-39705702/",
"https://www.pornpics.com/galleries/beautiful-young-brunette-gets-nice-big-tits-and-chin-covered-in-dripping-cum-76334386/",
"https://www.pornpics.com/galleries/hardcore-cunt-lapping-of-stunning-brunette-model-karmen-bells-52377799/",
"https://www.pornpics.com/galleries/brunette-latina-karmen-bella-taking-mouthful-of-cum-after-blowing-long-cock-48272393/",
"https://www.pornpics.com/galleries/busty-teen-karmen-bella-riding-cock-during-hardcore-fuck-session-37969585/",
"https://www.pornpics.com/galleries/latina-teen-karmen-bella-takes-cum-on-face-in-long-socks-after-hardcore-sex-76532467/",
"https://www.pornpics.com/galleries/sweet-latina-in-red-undies-karmen-bella-stripping-and-revealing-slender-body-61761271/",
"https://www.pornpics.com/galleries/latina-teenager-karmen-bella-ride-dick-after-receiving-cunnilingus-76489215/",
"https://www.pornpics.com/galleries/hot-all-natural-babe-karmen-bella-striking-sexy-topless-poses-94347326/",
"https://www.pornpics.com/galleries/latina-solo-girl-karmen-bella-showing-off-hanging-labia-lips-in-long-socks-99953202/",
"https://www.pornpics.com/galleries/natural-tit-brunette-babe-karmen-bella-showing-off-her-shaved-cunt-69885858/",
"https://www.pornpics.com/galleries/karmen-bella-enjoys-a-big-white-cock-in-her-mouth-and-tiny-pussy-70486040/",
"https://www.pornpics.com/galleries/hot-girlfriend-karmen-bella-looking-fit-and-toned-in-workout-clothes-53358664/",
"https://www.pornpics.com/galleries/hot-gf-karmen-bella-flashes-her-all-natural-tits-and-shaved-pussy-76623085/",
"https://www.pornpics.com/galleries/coed-adrian-maya-and-girlfriends-flashing-bald-cunts-in-dorm-room-76441891/",
"https://www.pornpics.com/galleries/indian-babe-karmen-bells-shows-off-her-spicy-rack-and-vagina-42798527/",
"https://www.pornpics.com/galleries/hot-babe-karmen-bella-has-puffy-pussy-licked-and-finger-fucked-64357177/",
"https://www.pornpics.com/galleries/dark-haired-latina-karmen-bella-delivering-ball-sac-licking-blowjob-68714831/",
"https://www.pornpics.com/galleries/hot-girl-karmen-bella-sucks-balls-and-cock-before-swallowing-cum-shot-24886517/",
"https://www.pornpics.com/galleries/sexy-latina-teener-karmen-bella-jerking-and-sucking-off-a-massive-penis-51303926/",
"https://www.pornpics.com/galleries/beautiful-latina-with-fantastic-natural-tits-karmen-bella-gets-nailed-hard-42072559/",
"https://www.pornpics.com/galleries/top-rated-babe-model-karmen-bella-flashing-her-perfect-all-natural-tits-18735659/",
"https://www.pornpics.com/galleries/gorgeous-brunette-teenager-karmen-bella-delivering-a-sloppy-blowjob-24947201/",
"https://www.pornpics.com/galleries/petite-pornstar-karmen-bella-shows-her-hot-body-and-plays-with-a-vibrator-26791977/",
"https://www.pornpics.com/galleries/big-tit-brunette-karmen-bella-showing-off-and-spreading-her-shaved-cunt-78325943/",
"https://www.pornpics.com/galleries/hot-brunette-babe-karmen-bella-spreading-puffy-shaved-pussy-lips-75286105/",
"https://www.pornpics.com/galleries/petite-pornstar-karmen-bella-modelling-solo-in-matching-bra-and-panty-set-59044089/",
"https://www.pornpics.com/galleries/latina-beauty-karmen-bella-fucking-big-dick-with-cumshot-in-mouth-finale-42147944/",
"https://www.pornpics.com/galleries/brunette-teen-with-natural-tits-sucks-a-mean-pecker-and-gets-rammed-in-the-bed-21211837/",
"https://www.pornpics.com/galleries/adorable-latina-girlfriend-karmen-bella-getting-fingered-and-boned-20925183/",
"https://www.pornpics.com/galleries/beautiful-latina-karmen-bella-gets-her-teenage-pussy-lips-stretched-out-93488687/",
"https://www.pornpics.com/galleries/pretty-latina-pornstar-karmen-bella-having-her-shaved-pussy-licked-out-54391261/",
"https://www.pornpics.com/galleries/dark-haired-latina-karmen-bella-showing-off-mouthful-of-sperm-19447147/",
"https://www.pornpics.com/galleries/brunette-latina-karmen-bella-taking-cumshot-in-mouth-from-large-cock-66199360/",
"https://www.pornpics.com/galleries/slutty-brunette-girlfriend-karmen-bella-giving-her-man-a-hot-blowjob-41484338/",
"https://www.pornpics.com/galleries/dreamy-gf-karmen-bella-sucking-on-a-cock-for-nice-cumshot-on-tongue-22968533/",
"https://www.pornpics.com/galleries/exotic-girlfriend-karmen-bella-letting-her-all-natural-tits-loose-68615848/",
"https://www.pornpics.com/galleries/horny-young-brunette-karmen-bella-getting-fingered-and-jizzed-on-83064079/",
"https://www.pornpics.com/galleries/skinny-latina-karmen-bellashows-her-natural-tits-and-her-lovely-butt-45372348/",
"https://www.pornpics.com/galleries/beautiful-brunette-girlfriend-karmen-bella-spreading-her-perfect-pussy-56324355/",
"https://www.pornpics.com/galleries/naturally-busty-karmen-bella-getting-her-pussy-licked-and-fingered-62594933/",
"https://www.pornpics.com/galleries/brunette-teen-karmen-bella-taking-jizz-on-face-after-blowing-big-cock-83756478/",
"https://www.pornpics.com/galleries/beautiful-girlfriend-karmen-bella-gets-shaved-pussy-lapped-before-anal-fuck-92088546/",
"https://www.pornpics.com/galleries/gorgeous-lady-karmen-bella-having-shaved-pussy-fingered-and-licked-78255605/",
"https://www.pornpics.com/galleries/beautiful-girlfriend-karmen-bella-has-anus-tongued-before-ass-fucking-31498673/",
"https://www.pornpics.com/galleries/stunning-dark-haired-beauty-karmen-bella-spreading-her-juicy-pussy-19986137/",
"https://www.pornpics.com/galleries/teen-babe-karmen-bella-revealing-big-tits-and-hanging-mud-flaps-15024943/",
"https://www.pornpics.com/galleries/beautiful-busty-babe-karmen-bella-taking-hardcore-fuck-doggystyle-56270841/",
"https://www.pornpics.com/galleries/latina-teen-karmen-bella-having-labia-lips-sucked-while-giving-bj-in-69-sex-60040154/",
"https://go.xxxijmp.com?userId=353e4188d9a9c1a093c1c9f0924ec9ad933d0e4dc993217fdd17e56b5ac764bd&amp;showModal=signup&amp;path=/DarlingKari55",
"https://www.pornpics.com/galleries/natural-brunette-tramp-karmen-bella-getting-her-pussy-licked-13395966/",
"https://www.pornpics.com/galleries/indian-teen-beauty-karmen-bella-sucking-dick-and-licking-balls-pov-65010884/",
"https://www.pornpics.com/galleries/sexy-brunette-karmen-bella-licking-balls-and-sucking-big-cock-31910009/",
"https://www.pornpics.com/galleries/skinny-brunette-teen-karmen-bella-modelling-sexy-bra-and-panty-set-77857248/",
"https://www.pornpics.com/galleries/erotic-latina-teen-karmen-bella-has-her-hot-pussy-pounded-medium-tits-jizzed-61647033/",
"https://www.pornpics.com/galleries/gorgeous-brunette-babe-karmen-bella-passionately-sucking-dick-60564928/",
"https://www.pornpics.com/galleries/charming-latina-babe-karmen-bella-showing-off-her-ass-and-shaved-pussy-90263800/",
"https://www.pornpics.com/galleries/brunette-latina-karmen-bella-giving-ball-sucking-bj-and-receiving-jizz-facial-67041803/",
"https://www.pornpics.com/galleries/hot-model-babe-karmen-bella-has-her-beautiful-shaved-pussy-licked-48969929/",
"https://www.pornpics.com/galleries/doggystyle-loving-latina-karmen-bella-enjoying-a-big-cock-up-her-twat-85095224/",
"https://www.pornpics.com/galleries/hot-gf-karmen-bella-giving-sexy-pov-blowjob-and-swallowing-cum-99201523"
]







# url = links[0]
folder_path = "F:/Important/Foreign/Karmen Bella/"

# for url in links[40:55]:
# 	if "pornpics" in url.split("."):
# 		a = PornPics(url, folder_path)
# 		a.download()
# 
# links = RaghalaHari.get_actress_album_link2("https://www.ragalahari.com/stars/profile/96504/aishwarya-rajesh.aspx")
# print(links)
# Next 55:60






def save_ar():
	links = ['https://www.ragalahari.com/actress/164947/aishwarya-rajesh-hd-photos-at-creative-commercials-production-no-46-muhurat.aspx', 'https://www.ragalahari.com/actress/166708/aishwarya-rajesh-at-kousalya-krishnamurthy-pre-release-event.aspx', 'https://www.ragalahari.com/actress/170163/aishwarya-rajesh-at-republic-movie-pre-release-event-hd-photo-gallery.aspx', 'https://www.ragalahari.com/actress/164765/aishwarya-rajesh-photo-gallery.aspx', 'https://www.ragalahari.com/actress/166726/aishwarya-rajesh-at-kousalya-krishnamurthy-success-meet-hd-photos.aspx', 'https://www.ragalahari.com/actress/166861/aishwarya-rajesh-stills-at-siima-2019-exclusive-high-definition-photos.aspx', 'https://www.ragalahari.com/actress/167889/aishwarya-rajesh-at-world-famous-lover-interview-hd.aspx', 'https://www.ragalahari.com/actress/166762/aishwarya-rajesh-at-kousalya-krishnamurthy-interview.aspx', 'https://www.ragalahari.com/actress/170117/aishwarya-rajesh-at-siima-awards-2021-day-2-hd-photo-gallery.aspx', 'https://www.ragalahari.com/actress/166370/aishwarya-rajesh-poses-during-kousalya-krishnamurthy-audio-release.aspx', 'https://www.ragalahari.com/actress/167988/aishwarya-rajesh-at-world-famous-lover-pre-release-event.aspx', 'https://www.ragalahari.com/actress/170165/1/aishwarya-rajesh-at-republic-movie-interview-hd-photo-gallery.aspx', 'https://www.ragalahari.com/actress/166371/aishwarya-rajesh-at-mis-s-match-movie-press-meet.aspx', 'https://www.ragalahari.com/actress/167889/1/aishwarya-rajesh-at-world-famous-lover-interview-hd.aspx', 'https://www.ragalahari.com/actress/167454/aishwarya-rajesh-at-miss-match-movie-pre-release.aspx', 'https://www.ragalahari.com/actress/170165/aishwarya-rajesh-at-republic-movie-interview-hd-photo-gallery.aspx']
	path = "F:\Important\Ragalahari\Aishwriya Rajesh"
	a = RaghalaHari("https://www.ragalahari.com/actress/164765/aishwarya-rajesh-photo-gallery.aspx", path)
	# a = RaghalaHari(links, path)
	a.download()

save_ar()