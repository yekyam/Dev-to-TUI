import requests
from abc import ABC, abstractmethod
from enum import Enum, auto
from dataclasses import dataclass
from bs4 import BeautifulSoup
from markdownify import markdownify as md


class DevAPIError(Exception):
	pass

class DATE_RANGE(Enum):
	Week = auto()
	Month = auto() 
	Year = auto() 
	Infinity = auto() 

@dataclass(frozen=True)
class Article:
	user: str
	path: str
	title: str
	tag_list: list[str]

	def __rich__(self) -> str:
		return self.title

def extract_text_from_url(url):
	r = requests.get(url)

	if r.status_code != 200:
		return None

	soup = BeautifulSoup(r.text, 'html.parser')
	article_body = soup.find("div", class_="crayons-article__body")

	if article_body is None:
		return None
	# return article_body.text
	article_title = soup.find('h1').text.strip()
	article_title = "# " + article_title + '\n'
	return article_title + md(repr(article_body))

	



class Feed(ABC):
	url = ''
	total_pages_cached = 0
	current_page = 0
	
	def __init__(self, num_articles_per_page) -> None:
		self.num_articles_per_page = num_articles_per_page
		self.articles = []


	def next(self):
		if self.current_page < self.total_pages_cached:
			self.current_page += 1
			return
		self.total_pages_cached += 1
		self.current_page += 1

		r = requests.get(self.url + f"page={self.total_pages_cached}")

		if r.status_code != 200:
			raise DevAPIError()


		for article_data in r.json():
			user = article_data['user']['username']
			title = article_data['title']
			path = article_data['path']
			tag_list = article_data['tag_list']

			article = Article(user, path, title, tag_list)

			self.articles.append(article)
	
	def prev(self):
		self.current_page = max(1, self.current_page - 1)
	
	def get_current_articles(self) -> list[Article]:
		first_current_article_index = (self.current_page - 1) * self.num_articles_per_page # home feed has 25 per "page" by deafult

		return self.articles[first_current_article_index : first_current_article_index + self.num_articles_per_page]

	
	

class Home(Feed):

	def __init__(self) -> None:
		super().__init__(25) # home feed has 25 articles per page
		self.url = 'https://dev.to/stories/feed/?'
	

class Top(Feed):
	def __init__(self, date_range: DATE_RANGE = DATE_RANGE.Week) -> None:
		super().__init__(50) # top feed has 50 per page
		url = ''
		match date_range:
			case DATE_RANGE.Week:
				url = 'https://dev.to/stories/feed/week?'
			case DATE_RANGE.Month:
				url = 'https://dev.to/stories/feed/month?'
			case DATE_RANGE.Year:
				url = 'https://dev.to/stories/feed/year?'
			case DATE_RANGE.Infinity:
				url = 'https://dev.to/stories/feed/infinity?'
		self.date_range = date_range
	
		self.url = url
		