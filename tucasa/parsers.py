import bs4
import requests


class ZonaProp(object):
  """
  Parser para la información que surge de ZonaProp
  """
  def __init__(self, url: str):
    response = requests.get(url)
    self.soup = bs4.BeautifulSoup(response.text, 'html.parser')

  def es_propiedad(self) -> bool:
    es_propiedad = self.soup.body['id'].upper() == 'PROPERTY'
    return es_propiedad
