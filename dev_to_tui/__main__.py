from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.reactive import reactive
from textual.widgets import Header, Footer, Tabs, Label, ListView, ListItem, Static, Button, Tab, Markdown
from textual.containers import VerticalScroll, Center
from feed import Top, DATE_RANGE, Feed, extract_text_from_url
import webbrowser

TAB_NAMES = ["Week", "Month", "Year", "Infinity"]

class FeedView(Static):

	def __init__(self, feed: Feed):
		super().__init__()
		self.feed = feed
		self.prev_click = reactive("Placeholder")

	def on_button_pressed(self, event):
		button_id = event.button.id


		match button_id:
			case "next":
				self.feed.next()
				self.prev_click = "next"

			case "prev":
				self.feed.prev()
				self.prev_click = "prev"

		self.repopulate_feed()
		
		print(f"Feed time  range:{self.feed.date_range}")
		print(f"Current page :{self.feed.current_page}")

	def compose(self) -> ComposeResult:
		# yield Label(self.prev_click)
		yield ListView(*[ListItem(Label(article)) for article in self.feed.get_current_articles()], id="feedlist")
		yield Button("Next Page", id="next")
		yield Button("Prev Page", id="prev")
	
	def repopulate_feed(self):
		self.query_one("#feedlist").clear()

		for article in self.feed.get_current_articles():
			print(f"Article title: {article.title}")
			self.query_one("#feedlist").append(ListItem(Label(article.title)))

		print(f"Feed time range:{self.feed.date_range}")
		print(f"Current page :{self.feed.current_page}")


class ArticleView(Screen):
	BINDINGS = [("escape", "app.pop_screen", "Back to article list"), ('o', 'open_link_in_browser', "Open the link in browser")]

	def __init__(self, text, url):
		super().__init__()
		self.text = text
		self.url = url
	
	def compose(self):

		with VerticalScroll():
			yield Markdown(self.text)
		yield Footer()
	
	def action_open_link_in_browser(self):
		webbrowser.open(self.url, 2)
	
	async def on_markdown_link_clicked(self, message):
		print('here')
		link = message.href
		webbrowser.open(link, 2)



class DevTUI(App):

	CSS = """
    Tabs {
        dock: top;
    }
    
    Screen {
        align: center middle;

    }

    ListView {
		width: 70%;
        content-align: center middle;
		height: auto;
		margin: 1 1;
	}

	Markdown {
		color: white;
		width: 100%;
		height: auto;
		background: dimgray;
		margin: 1 1;
	}
    """
    
	BINDINGS = [
		#("enter", "open_article", "Open Article")
	]

	def __init__(self):
		super().__init__()
		self.week_feed = Top(DATE_RANGE.Week)
		self.month_feed = Top(DATE_RANGE.Month)
		self.year_feed = Top(DATE_RANGE.Year)
		self.inf_feed = Top(DATE_RANGE.Infinity)
		self.cached_articles = {}


		self.feeds = [self.week_feed, self.month_feed, self.year_feed, self.inf_feed]

		for feed in self.feeds:
			feed.next()

	def compose(self):
		yield Tabs(*[Tab(tab_name, id=tab_name.lower()) for tab_name in TAB_NAMES])

		# yield ArticleView("")
		with Center():
			yield FeedView(self.week_feed)

		yield Header()
		yield Footer()

	def on_mount(self):
		self.query_one(Tabs).focus()

	def on_tabs_tab_activated(self, event: Tabs.TabActivated) -> None:
		"""Handle TabActivated message sent by Tabs."""
		tab_id = event.tab.id
		feed_view = self.query_one(FeedView)

		for feed in self.feeds:
			feed.current_page = 1


		match tab_id:
			case "week":
				feed_view.feed = self.week_feed
			case "month":
				feed_view.feed = self.month_feed
			case "year":
				feed_view.feed = self.year_feed
			case "infinity":
				feed_view.feed = self.inf_feed

		feed_view.repopulate_feed()

	async def on_list_view_selected(self, _):
		article_index = self.query_one(ListView).index
		feed_view = self.query_one(FeedView)
		feed = feed_view.feed

		article = feed.get_current_articles()[article_index]

		article_screen = None
		if article.title in self.cached_articles:
			article_screen = self.cached_articles[article.title]


		else:
			article_url = "https://dev.to" + article.path
			article_markdown = extract_text_from_url(article_url)
			article_screen = ArticleView(article_markdown, article_url)
			self.cached_articles[article.title] = article_screen
			self.install_screen(article_screen, name=article.title)
			
		self.push_screen(article_screen)
		

app = DevTUI()
app.run()