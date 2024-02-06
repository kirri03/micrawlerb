from fastapi import FastAPI
import time
import requests
from bs4 import BeautifulSoup
from serpapi import GoogleSearch
from proxyscrape import create_collector
import random

'''params = {
  "engine": "google_scholar",
  "q": "Artificial Intelligence",
  "api_key": "klok1234"
}

search = GoogleSearch(params)
results = search.get_dict()
print(results)
organic_results = results["organic_results"]'''

app = FastAPI(
    title="Servidor de datos",
    description="""Servimos datos de contratos, pero podríamos hacer muchas otras cosas, la la la.""",
    version="0.1.0",
)

# Crear un colector de proxies
collector = create_collector('default', 'http')

# Obtener un proxy de proxyscrape
proxy = collector.get_proxy()

proxies = {
    'http': f'http://{proxy.host}:{proxy.port}',
    'https': f'http://{proxy.host}:{proxy.port}',
}
# 10.1016/j.artmed.2017.06.011
'''def search_crossref_metadata(query):

    # Busqueda por titulo

    base_url = 'https://api.crossref.org/works'
    params = {'query': query}

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()

        data = response.json()
        items = data.get('message', {}).get('items', [])

        for item in items:
            title = item.get('title', [''])[0]
            doi = item.get('DOI', '')
            references = item.get('reference', [])

            print(f'Título: {title}')
            print(f'DOI: {doi}')
            print(f'Referencias: {references}')
            print('---')

    except requests.exceptions.HTTPError as errh:
        print(f"Error HTTP: {errh}")

    except requests.exceptions.RequestException as err:
        print(f"Error general: {err}")

    time.sleep(random.uniform(1,2))'''
'''
def search_crossref_metadata(query):
    base_url = 'https://api.crossref.org/works/'

    try:
        # Intentar determinar si el parámetro es un DOI
        if query.startswith('10.'):
            doi_url = f'{base_url}{query}'
            response = requests.get(doi_url)
        else:
            # Si no parece ser un DOI, realizar una búsqueda por título
            params = {'query': query}
            response = requests.get(base_url, params=params)

        response.raise_for_status()

        data = response.json()
        items = data.get('message', {}).get('items', [])

        for item in items:
            title = item.get('title', [''])[0]
            doi = item.get('DOI', '')
            references = item.get('reference', [])

            print(f'Título: {title}')
            print(f'DOI: {doi}')
            print(f'Referencias: {references}')
            print('---')

        if not items:
            print('No se encontraron resultados para la búsqueda.')

    except requests.exceptions.HTTPError as errh:
        print(f"Error HTTP: {errh}")

    except requests.exceptions.RequestException as err:
        print(f"Error general: {err}")

    time.sleep(random.uniform(1,2))'''

def search_crossref_metadata(query, depth=1):
    base_url = 'https://api.crossref.org/works/'
    esdoi='&from_ui=yes'

    try:
        # Intentar determinar si el parámetro es un DOI
        if query.startswith('10.'):
            '''doi_query = f'{query}{esdoi}'
            params = {'query': doi_query}'''
            url=f'https://api.crossref.org/works/{query}'
            #response = requests.get(base_url, params=params)
            response= requests.get(url)
        else:
            # Si no parece ser un DOI, realizar una búsqueda por título
            params = {'query': query}
            response = requests.get(base_url, params=params)

        response.raise_for_status()

        data = response.json()

        if query.startswith('10.'):
            item=data.get('message',{})
            if item:
                title = item.get('title', [''])[0]
                doi = item.get('DOI', '')
                # Extracción de la fecha de publicación
                published_date = item.get('issued', {}).get('date-parts', [[]])[0]
                published_date_str = '-'.join(map(str, published_date)) if published_date else ''
                references = item.get('reference', [])


                print(f'Título: {title}')
                print(f'DOI: {doi}')
                print(f'Fecha de Publicación: {published_date_str}')
                print(f'Referencias: {references}')
                print('\n\n#########################################\n\n')

                if depth > 1:
                    for ref in references:
                        doi_to_search = ref.get('DOI', '')
                        if doi_to_search:
                            search_crossref_metadata(doi_to_search, depth=depth - 1)
                        else:
                            # Si no hay DOI, intentar buscar por título
                            title_to_search = ref.get('article-title', '')
                            if title_to_search:
                                search_crossref_metadata(title_to_search, depth=depth - 1)
                            else:
                                otraforma=ref.get('unstructured', '')
                                search_crossref_metadata(otraforma,depth=depth - 1)
            else:
                print('No se encontraron resultados para el DOI')

        else:
            items = data.get('message', {}).get('items', [])

            for item in items:
                title = item.get('title', [''])[0]
                doi = item.get('DOI', '')
                # Extracción de la fecha de publicación
                published_date = item.get('issued', {}).get('date-parts', [[]])[0]
                published_date_str = '-'.join(map(str, published_date)) if published_date else ''
                references = item.get('reference', [])

                print(f'Título: {title}')
                print(f'DOI: {doi}')
                print(f'Fecha de Publicación: {published_date_str}')
                print(f'Referencias: {references}')
                print('\n\n#########################################\n\n')

                # Realizar el crawling a una profundidad adicional si es necesario
                if depth > 1:
                    for ref in references:
                        doi_to_search = ref.get('DOI', '')
                        if doi_to_search:
                            search_crossref_metadata(doi_to_search, depth=depth - 1)
                        else:
                            # Si no hay DOI, intentar buscar por título
                            title_to_search = ref.get('article-title', '')
                            if title_to_search:
                                search_crossref_metadata(title_to_search, depth=depth - 1)

            if not items:
                print('No se encontraron resultados para la búsqueda.')

    except requests.exceptions.HTTPError as errh:
        print(f"Error HTTP: {errh}")

    except requests.exceptions.RequestException as err:
        print(f"Error general: {err}")

    time.sleep(random.uniform(1,10))


# Ejemplo de búsqueda por DOI DE PROFUNDIDAD 2 
search_query = '10.1016/j.artmed.2011.04.006'
search_crossref_metadata(search_query,2)

'''# URL de inicio para el web crawler
start_url = 'https://scholar.google.com/scholar?hl=en&as_sdt=0,5&q=%22artificial+intelligence%22'

# Profundidad máxima de búsqueda (ajusta según sea necesario)
max_depth = 2

# Llamar al web crawler con la URL de inicio y la profundidad máxima
web_crawler(start_url, depth=0, max_depth=max_depth)

 # Filtrar por div class para titulos
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
response = requests.get(start_url, headers=headers, proxies=proxies)

response.raise_for_status()  # Lanza una excepción si la solicitud no fue exitosa

# Parsear el HTML de la página
soup = BeautifulSoup(response.text, 'html.parser')
titulos=soup.find_all('div', class_='gs_r gs_or gs_scl')
for titulo in titulos:
    print(f"\nTITULO-->{titulo.text}")'''