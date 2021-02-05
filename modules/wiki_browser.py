import wikipedia

class WikiBrowser:
    '''WikiBrowser object to help us to browse something in wikipedia'''

    def __init__(self, page_name,  lenguage = 'es'):

        self.lenguage = lenguage
        self.page_name = page_name
  
    
   
    def obtain_summary(self):

        try:
             wikipedia.set_lang(self.lenguage)
             page_summary = wikipedia.summary(self.page_name)

             return page_summary

        except wikipedia.exceptions.PageError:

            return 'Page not found :('
        
        except:

            return 'Something went wrong :('

    


