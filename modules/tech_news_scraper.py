from lxml import html
import requests

#Xpath expressions
HOME = 'https://news.mit.edu'
X_TITTLES = '//div[@class="page--section front-page--featured-news"]/div/div/div/div/article/div[@class="front-page--news-article--teaser--descr"]/h3/a/span/text()'
X_LINKS = '//div[@class="page--section front-page--featured-news"]/div/div/div/div/article/div[@class="front-page--news-article--teaser--descr"]/h3/a/@href'

def scrape_news_and_links():
    
    news_tittles = []
    news_links = []

    try: 
        request = requests.get(HOME)
    except:
         pass

    home_html = request.content.decode('utf-8')
    parse = html.fromstring(home_html)
    tittles = parse.xpath(X_TITTLES)
    links = parse.xpath(X_LINKS)
    
    for i in range(len(tittles)): #Notice that tittles and links have the same len
        news_tittles.append(f'{tittles[i]}: ')
        news_links.append(HOME + links[i]) #We concatenate this because if we dont do that the link wont work 
    
    news_tittles.append('All of this articles were taken from: ')
    news_links.append(HOME)

    return news_tittles, news_links



if __name__ == '__main__':
    
    tittle, link = scrape_news_and_links()
    for i in range( len(link)):
        print(tittle[i], link[i])


