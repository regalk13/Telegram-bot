from bs4 import BeautifulSoup
import requests

class WeatherScraper:

	def __init__(self, place):

		self.place = place
		self._url = 'https://www.google.com/search?q=weather ' + self.place

	def get_tempetarure_and_weather(self):

		try:
			request = requests.get(self._url)
			html_text = request.text

			soup = BeautifulSoup(html_text, 'html.parser')

			temperature = soup.find('div', {'class' : 'BNeawe'}).get_text()

			weather = soup.find('div', {'class' : 'tAd8D'}).get_text().split('\n')

			return f'{temperature}, {weather[1]}'
		
		except:

			return 'Something went wrong!'





