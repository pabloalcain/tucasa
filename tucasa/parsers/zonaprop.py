import math
import warnings
from typing import List

import bs4
import requests

RESULTADOS_POR_PAGINA = 20


class Propiedad(object):
    """
    Parser de propiedades de ZonaProp
    """

    def __init__(self, url: str, local=False):
        if not local:
            response = requests.get(url).text
        else:
            response = open(url).read()
        self.url = url
        self.soup = bs4.BeautifulSoup(response, 'html.parser')
        if not self._es_propiedad:
            warnings.warn(f"{url} no parece ser una propiedad.", UserWarning)

        def quitar_m2(entrada: str) -> int:
            indice = entrada.find("m²")
            valor = entrada[:indice]
            valor = int(valor)
            return valor

        def antiguedad(entrada: str) -> int:
            if entrada == "A estrenar":
                anios = 0
            else:
                anios = int(entrada)
            return anios

        self._procesar_valor_conocidas = {}
        self._procesar_valor_conocidas['Ambientes'] = lambda x: int(x)
        self._procesar_valor_conocidas['Baños'] = lambda x: int(x)
        self._procesar_valor_conocidas['Dormitorios'] = lambda x: int(x)
        self._procesar_valor_conocidas['Superficie total'] = quitar_m2
        self._procesar_valor_conocidas['Superficie cubierta'] = quitar_m2
        self._procesar_valor_conocidas['Antigüedad'] = antiguedad

        self._procesar_clave_conocidas = {}
        self._procesar_clave_conocidas['Baño'] = lambda x: x + "s"
        self._procesar_clave_conocidas['Ambiente'] = lambda x: x + "s"
        self._procesar_clave_conocidas['Dormitorio'] = lambda x: x + "s"

        self._informacion = {}

    @property
    def _es_propiedad(self) -> bool:
        es_propiedad = self.soup.body['id'].upper() == 'PROPERTY'
        return es_propiedad

    @property
    def informacion(self) -> dict:
        datos = self.soup.findAll('li', {'class': 'icon-feature'})
        _informacion = {}
        for dato in datos:
            clave = dato.span.text
            clave = self._procesar_clave(clave)(clave)
            valor = self._procesar_valor(clave)(dato.b.text)
            _informacion[clave] = valor
        alquiler = self._alquiler()
        _informacion["Alquiler"] = alquiler
        expensas = self._expensas()
        _informacion["Expensas"] = expensas
        titulo = self.soup.find('h2', {'class': 'title-location'})
        direccion_limpia = ' '.join(titulo.b.text.split())
        # Quitar la información del barrio que a veces viene duplicada
        direccion_limpia = direccion_limpia.split(',')[0]
        sin_direccion = titulo.text.split(',')[1:]
        sin_espacios = [_.strip() for _ in sin_direccion]
        ubicacion = ', '.join(sin_espacios)
        _informacion["URL"] = self.url
        _informacion["Direccion"] = direccion_limpia
        _informacion['Ubicacion'] = ubicacion
        descripcion = self.soup.find('div', {'id': 'verDatosDescripcion'})
        _informacion["Descripcion"] = descripcion.text
        caracteristicas = {}
        general_section = self.soup.findAll('section', {'class': 'general-section article-section'})
        for sec in general_section:
            clave = sec.div.text.strip()
            esta_lista = sec.findAll('li')
            estas_caracteristicas = tuple(_.text.strip() for _ in esta_lista)
            caracteristicas[clave] = estas_caracteristicas
        _informacion["Caracteristicas"] = caracteristicas
        return _informacion

    def _expensas(self):
        expensas = self.soup.find('div', {'class': 'block-expensas block-row'})
        if expensas is not None:
            expensas = expensas.span.text
            if '$' in expensas:
                expensas = expensas.replace(".", "")
                expensas = expensas.replace("$", "")
                expensas = int(expensas)
        return expensas

    def _alquiler(self):
        precios = self.soup.findAll("div", {"class": "block-price block-row"})
        alquiler = None
        for p in precios:
            texto = p.find("div", {"class": "price-operation"}).text
            if texto.upper() == 'ALQUILER':
                alquiler = p.find('div', {'class': 'price-items'}).span.text
                # TODO: Analizar caso de múltiple moneda. Por ahora sólo
                # obtenemos los que están en $
                if "$" in alquiler:
                    alquiler = alquiler.replace("$", "")
                    alquiler = alquiler.replace(".", "")
                    alquiler = int(alquiler)
                else:
                    alquiler = None
        return alquiler

    @property
    def ambientes(self) -> int:
        return self.informacion["Ambientes"]

    @property
    def antiguedad(self) -> int:
        return self.informacion["Antigüedad"]

    @property
    def superficie_total(self) -> int:
        return self.informacion["Superficie total"]

    @property
    def superficie_cubierta(self) -> int:
        return self.informacion["Superficie cubierta"]

    @property
    def banios(self) -> int:
        return self.informacion["Baños"]

    @property
    def dormitorios(self) -> int:
        return self.informacion["Dormitorios"]

    @property
    def disposicion(self) -> int:
        return self.informacion["Disposición"]

    @property
    def orientacion(self) -> int:
        return self.informacion["Orientación"]

    @property
    def estado(self) -> int:
        return self.informacion["Estado del inmueble"]

    @property
    def luminosidad(self) -> int:
        return self.informacion["Luminosidad"]

    @property
    def alquiler(self) -> int:
        return self.informacion["Alquiler"]

    @property
    def expensas(self) -> int:
        return self.informacion["Expensas"]

    @property
    def direccion(self) -> str:
        return self.informacion["Direccion"]

    @property
    def ubicacion(self) -> str:
        return self.informacion["Ubicacion"]

    @property
    def descripcion(self) -> str:
        return self.informacion["Descripcion"]

    @property
    def contacto(self):
        # TODO: Extraer contacto (necesita cargar JS seguramente)
        raise NotImplementedError

    @property
    def caracteristicas(self):
        return self.informacion["Caracteristicas"]

    @property
    def ubicacion_mapa(self):
        # TODO: Extraer ubicación desde el mapa
        raise NotImplementedError

    def _procesar_valor(self, clave):
        try:
            funcion = self._procesar_valor_conocidas[clave]
        except KeyError:
            funcion = lambda x: x
        return funcion

    def _procesar_clave(self, clave):
        try:
            funcion = self._procesar_clave_conocidas[clave]
        except KeyError:
            funcion = lambda x: x
        return funcion


class Listado(object):
    """
    Parser de listado de propiedades de ZonaProp
    """

    def __init__(self, url: str, local=False):
        if not local:
            response = requests.get(url).text
        else:
            response = open(url).read()
        self.soup = bs4.BeautifulSoup(response, 'html.parser')
        if not self._es_listado:
            warnings.warn(f"{url} no parece ser un listado.", UserWarning)

    @property
    def _es_listado(self) -> bool:
        es_listado = self.soup.body['id'].upper() == 'BODY-LISTADO'
        return es_listado

    @property
    def _propiedades_div(self) -> list:
        # TODO: Manejar de alguna manera los emprendimientos. Los estamos ignorando.
        container = self.soup.find('div', {'class': 'list-card-container'})
        prop = container.findAll('div', {'data-posting-type': 'PROPERTY'})
        return prop

    @staticmethod
    def _propiedad_desde_div(div) -> Propiedad:
        url = 'http://www.zonaprop.com.ar' + div['data-to-posting']
        prop = Propiedad(url)
        return prop

    @property
    def propiedades_url(self) -> List[str]:
        lista_url = []
        for div in self._propiedades_div:
            url = 'http://www.zonaprop.com.ar' + div['data-to-posting']
            lista_url.append(url)
        return lista_url

class ResultadoBusqueda(object):
    def __init__(self, url: str, local=False):
        self.url = url
        if not local:
            response = requests.get(url).text
        else:
            warnings.warn("No están habilitadas todas las opciones para búsquedas descargadas")
            response = open(url).read()
        self.soup = bs4.BeautifulSoup(response, 'html.parser')
        if not self._es_busqueda:
            warnings.warn(f"{url} no parece ser una búsqueda.", UserWarning)

    @property
    def _es_busqueda(self):
        es_busqueda = self.soup.body['id'].upper() == 'BODY-LISTADO'
        return es_busqueda

    @property
    def cantidad_de_resultados(self) -> int:
        titulo = self.soup.find('h1', {'class': 'list-result-title'})
        cantidad = titulo.b.text.replace('.', '')
        cantidad = int(cantidad)
        return cantidad

    def listado_pagina(self, n: int) -> str:
        """
        A partir de la url de la búsqueda, genera el listado de la página `n`.
        """
        url_pagina = self.url.replace('.html', f'-pagina-{n}.html')
        return url_pagina

    @property
    def cantidad_de_paginas(self) -> int:
        numero_de_paginas = math.ceil(self.cantidad_de_resultados / RESULTADOS_POR_PAGINA)
        return numero_de_paginas
