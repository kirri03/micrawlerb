from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import time
import requests
from bs4 import BeautifulSoup
from serpapi import GoogleSearch
#from proxyscrape import create_collector
import random
import sqlite3
from ratelimit import limits, sleep_and_retry
import pandas as pd
import asyncio
import websockets

#params = {
#"engine": "google_scholar",
#"q": "Artificial Intelligence",
#"api_key": "klok1234"
#}

#search = GoogleSearch(params)
#results = search.get_dict()
#print(results)
#organic_results = results["organic_results"]

app = FastAPI(
    title="Servidor de datos",
    description="""Servimos datos de contratos, pero podríamos hacer muchas otras cosas, la la la.""",
    version="0.1.0",
)


'''# Crear un colector de proxies
collector = create_collector('default', 'http')

# Obtener un proxy de proxyscrape
proxy = collector.get_proxy()

proxies = {
    'http': f'http://{proxy.host}:{proxy.port}',
    'https': f'http://{proxy.host}:{proxy.port}',
}'''

# Función para crear la tabla si no existe
def create_tables(conn_str):

    with sqlite3.connect(conn_str) as conn:
        cursor = conn.cursor()

    #cursor = conn.cursor()

    # Crear la tabla de artículos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doi TEXT UNIQUE NOT NULL,
            depth INTEGER,
            title TEXT,
            published_date TEXT,
            citation_count INTEGER,
            num_apariciones INTEGER DEFAULT 1
        )
    ''')

    # Crear la tabla de referencias
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS article_references (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_doi TEXT,
            reference_doi TEXT,
            FOREIGN KEY (article_doi) REFERENCES articles (doi),
            FOREIGN KEY (reference_doi) REFERENCES articles (doi)
        )
    ''')

    conn.commit()

    # Crear la tabla de autores de artículos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS article_authors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id INTEGER,
            title TEXT,
            author TEXT,
            FOREIGN KEY (article_id) REFERENCES articles (id)
        )
    ''')

    conn.commit()

# Función para insertar datos en la base de datos
def insert_data(conn, doi, depth, title, published_date, authors, citation_count):
    cursor = conn.cursor()

    # Verificar si el artículo ya existe por DOI o título
    cursor.execute('SELECT id, num_apariciones FROM articles WHERE doi = ? OR title = ?', (doi, title))
    existing_article = cursor.fetchone()

    if existing_article:
        # Si existe, incrementar num_apariciones y obtener el nuevo valor
        new_num_apariciones = existing_article[1] + 1

        cursor.execute('''
            UPDATE articles SET num_apariciones = ? WHERE id = ?
        ''', (new_num_apariciones, existing_article[0]))

        conn.commit()
        return existing_article[0], new_num_apariciones

    # Insertar el artículo
    cursor.execute('''
        INSERT OR IGNORE INTO articles (doi, title, depth, published_date, citation_count) VALUES (?, ?, ?, ?, ?)
    ''', (doi, title, depth, published_date, citation_count))

    conn.commit()

    # Obtener el ID del artículo insertado
    cursor.execute('SELECT id FROM articles WHERE doi = ?', (doi,))
    article_id = cursor.fetchone()[0]

    # Insertar los autores del artículo
    for author in authors:
        cursor.execute('''
            INSERT OR IGNORE INTO article_authors (article_id, title, author) VALUES (?, ?, ?)
        ''', (article_id, title, author))

    conn.commit()


class WebSocketConnectionManager:
    connections = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.connections.remove(websocket)

#manager = WebSocketConnectionManager()

#@app.websocket("/ws")
#async def websocket_endpoint(websocket: WebSocket):
#    await manager.connect(websocket)
#    try:
#        while True:
#            message = await websocket.receive_text()
#            if message == "disconnect":
#                break
#            await asyncio.sleep(1)
#    except WebSocketDisconnect:
#        manager.disconnect(websocket)

#async def send_update(message, connection):
#    await connection.send_text(message)

# ...

#def send_update(message):
#    for connection in manager.connections:
#        asyncio.ensure_future(send_update(message, connection))

#@sleep_and_retry
#@limits(calls=150, period=1)
#def search_and_store_metadata(conn_str, query, depth=1, parent_doi=None):
#    base_url = 'https://api.crossref.org/works/'
#    esdoi='&from_ui=yes'

#    try:
#        with sqlite3.connect(conn_str) as conn:
#            cursor = conn.cursor()
#        # Intentar determinar si el parámetro es un DOI
#        if query.startswith('10.'):
#            url=f'https://api.crossref.org/works/{query}'
#            response= requests.get(url)
#        else:
#            # Si no parece ser un DOI, realizar una búsqueda por título
#            params = {'query': query}
#            response = requests.get(base_url, params=params)
#
#        response.raise_for_status()

#        data = response.json()

#        if query.startswith('10.'):
#            item=data.get('message',{})
#            if item:
#                title_list = item.get('title', [''])
#                title = title_list[0] if title_list else None
#                doi = item.get('DOI', '')
#                # Obtener el autor
#                authors = [author.get('given', '') + ' ' + author.get('family', '') for author in item.get('author', [])]
#                # Extracción del año de publicación
#                published_date = item.get('issued', {}).get('date-parts', [[]])[0]
#                year = published_date[0] if published_date else None
#                references = item.get('reference', [])
#                citation_count = item.get('is-referenced-by-count', 0)

#                print(f'Título: {title}')
#                print(f'DOI: {doi}')
#                print(f'Autor(es): {authors}')
#                print(f'Año de Publicación: {year}')
#                print(f'Número de Citas: {citation_count}')
#                print(f'Referencias: {references}')
#                print('\n\n#########################################\n\n')

#                insert_data(conn, doi, title, year, authors, citation_count)

#                if parent_doi:
                    # Si hay un DOI padre, relacionar el artículo actual con el padre
 #                   cursor = conn.cursor()
  #                  cursor.execute('''
   #                     INSERT OR IGNORE INTO article_references (article_doi, reference_doi) VALUES (?, ?)
    #                ''', (parent_doi, doi))

#                    conn.commit()

#                if depth > 1:
                    # Realizar búsquedas recursivas para las referencias
#                    for ref in references:
#                        doi_to_search = ref.get('DOI', '')
#                        if doi_to_search:
#                            search_and_store_metadata(conn_str, doi_to_search, depth=depth - 1, parent_doi=doi)
#                        else:
#                            title_to_search = ref.get('article-title', '')
#                            if title_to_search:
#                                search_and_store_metadata(conn_str, title_to_search, depth=depth - 1, parent_doi=doi)
#                            else:
#                                otraforma=ref.get('unstructured', '')
#                                search_and_store_metadata(conn_str,otraforma,depth=depth - 1, parent_doi=doi)
                
#                else:
#                    return None
                
                #else:
                    #send_update("Búsqueda completada para: " + query)

#            else:
#                print('No se encontraron resultados para el DOI')
        
#        else:
#            items = data.get('message', {}).get('items', [])

#            for item in items:
#                title_list = item.get('title', [''])
#                title = title_list[0] if title_list else None
#                doi = item.get('DOI', '')
                # Obtener el autor
#                authors = [author.get('given', '') + ' ' + author.get('family', '') for author in item.get('author', [])]
                # Extracción del año de publicación
#                published_date = item.get('issued', {}).get('date-parts', [[]])[0]
 #               year = published_date[0] if published_date else None
#                references = item.get('reference', [])
#                citation_count = item.get('is-referenced-by-count', 0)

#                insert_data(conn, doi, title, year, authors, citation_count)

#                print(f'Título: {title}')
#                print(f'DOI: {doi}')
#                print(f'Autor(es): {authors}')
#                print(f'Año de Publicación: {year}')
#                print(f'Número de Citas: {citation_count}')
#                print(f'Referencias: {references}')
#                print('\n\n#########################################\n\n')

#                if parent_doi:
                    # Si hay un DOI padre, relacionar el artículo actual con el padre
#                    cursor = conn.cursor()
#                    cursor.execute('''
#                        INSERT OR IGNORE INTO article_references (article_doi, reference_doi) VALUES (?, ?)
#                    ''', (parent_doi, doi))
#                    conn.commit()

                # Realizar el crawling a una profundidad adicional si es necesario
#                if depth > 1:
#                    for ref in references:
#                        doi_to_search = ref.get('DOI', '')
#                        if doi_to_search:
#                            search_and_store_metadata(conn, doi_to_search, depth=depth - 1, parent_doi=doi)
#                        else:
                            # Si no hay DOI, intentar buscar por título
#                            title_to_search = ref.get('article-title', '')
#                            if title_to_search:
#                                search_and_store_metadata(conn, title_to_search, depth=depth - 1, parent_doi=doi)
#                            else:
#                                otraforma=ref.get('unstructured', '')
#                                search_and_store_metadata(conn,otraforma,depth=depth - 1, parent_doi=doi)
                            
#                else:
#                    return None
#            if not items:
#                print('No se encontraron resultados para la búsqueda.')

#    except requests.exceptions.HTTPError as errh:
#        print(f"Error HTTP: {errh}")
#
#    except requests.exceptions.RequestException as err:
#        print(f"Error general: {err}")


@sleep_and_retry
@limits(calls=150, period=1)
def search_and_store_metadata(conn_str, query, depth=1, parent_doi=None):
    current_depth=0
    base_url = 'https://api.crossref.org/works/'
    esdoi='&from_ui=yes'

    with sqlite3.connect(conn_str) as conn:
                cursor = conn.cursor()

    stack = [(query, depth, parent_doi)]
    while stack:
        current_query, current_depth, current_parent_doi = stack.pop()
        try:
            # Intentar determinar si el parámetro es un DOI
            if current_query.startswith('10.'):
                url=f'https://api.crossref.org/works/{current_query}'
                response= requests.get(url)
            else:
                # Si no parece ser un DOI, realizar una búsqueda por título
                params = {'query': current_query}
                response = requests.get(base_url, params=params)

            response.raise_for_status()

            data = response.json()

            if current_query.startswith('10.'):
                item=data.get('message',{})
                if item:
                    title_list = item.get('title', [''])
                    title = title_list[0] if title_list else None
                    doi = item.get('DOI', '')
                    # Obtener el autor
                    authors = [author.get('given', '') + ' ' + author.get('family', '') for author in item.get('author', [])]
                    # Extracción del año de publicación
                    published_date = item.get('issued', {}).get('date-parts', [[]])[0]
                    year = published_date[0] if published_date else None
                    references = item.get('reference', [])
                    citation_count = item.get('is-referenced-by-count', 0)

                    print(f'Título: {title}')
                    print(f'DOI: {doi}')
                    print(f'Autor(es): {authors}')
                    print(f'Año de Publicación: {year}')
                    print(f'Número de Citas: {citation_count}')
                    print(f'Referencias: {references}')
                    print('\n\n#########################################\n\n')

                    insert_data(conn, doi, current_depth, title, year, authors, citation_count)

                    if current_parent_doi:
                        # Si hay un DOI padre, relacionar el artículo actual con el padre
                        cursor = conn.cursor()
                        cursor.execute('''
                            INSERT OR IGNORE INTO article_references (article_doi, reference_doi) VALUES (?, ?)
                        ''', (current_parent_doi, doi))

                        conn.commit()

                    if current_depth <= depth:
                        # Realizar búsquedas recursivas para las referencias
                        for ref in references:
                            doi_to_search = ref.get('DOI', '')
                            if doi_to_search:
                                stack.append((doi_to_search, current_depth + 1, current_query))
                            else:
                                title_to_search = ref.get('article-title', '')
                                if title_to_search:
                                    stack.append((title_to_search, current_depth + 1, current_query))
                                else:
                                    otraforma=ref.get('unstructured', '')
                                    stack.append((otraforma, current_depth + 1, current_query))
                    
                    #else:
                        #send_update("Búsqueda completada para: " + query)

                else:
                    print('No se encontraron resultados para el DOI')
            
            else:
                items = data.get('message', {}).get('items', [])

                for item in items:
                    title_list = item.get('title', [''])
                    title = title_list[0] if title_list else None
                    doi = item.get('DOI', '')
                    # Obtener el autor
                    authors = [author.get('given', '') + ' ' + author.get('family', '') for author in item.get('author', [])]
                    # Extracción del año de publicación
                    published_date = item.get('issued', {}).get('date-parts', [[]])[0]
                    year = published_date[0] if published_date else None
                    references = item.get('reference', [])
                    citation_count = item.get('is-referenced-by-count', 0)

                    insert_data(conn, doi, current_depth, title, year, authors, citation_count)

                    print(f'Título: {title}')
                    print(f'DOI: {doi}')
                    print(f'Autor(es): {authors}')
                    print(f'Año de Publicación: {year}')
                    print(f'Número de Citas: {citation_count}')
                    print(f'Referencias: {references}')
                    print('\n\n#########################################\n\n')

                    if current_parent_doi:
                        # Si hay un DOI padre, relacionar el artículo actual con el padre
                        cursor = conn.cursor()
                        cursor.execute('''
                            INSERT OR IGNORE INTO article_references (article_doi, reference_doi) VALUES (?, ?)
                        ''', (current_parent_doi, doi))
                        conn.commit()

                    # Realizar el crawling a una profundidad adicional si es necesario
                    if current_depth <= depth:
                        for ref in references:
                            doi_to_search = ref.get('DOI', '')
                            if doi_to_search:
                                stack.append((doi_to_search, current_depth + 1, current_query))
                            else:
                                # Si no hay DOI, intentar buscar por título
                                title_to_search = ref.get('article-title', '')
                                if title_to_search:
                                    stack.append((title_to_search, current_depth + 1, current_query))
                                else:
                                    otraforma=ref.get('unstructured', '')
                                    stack.append((otraforma, current_depth + 1, current_query))
                if not items:
                    print('No se encontraron resultados para la búsqueda.')

        except requests.exceptions.HTTPError as errh:
            print(f"Error HTTP: {errh}")

        except requests.exceptions.RequestException as err:
            print(f"Error general: {err}")

    return True
    #time.sleep(random.uniform(0,0.7))

# Ejemplo de búsqueda por DOI DE PROFUNDIDAD 2 
#search_query = '10.1016/j.artmed.2011.04.006'
#search_and_store_metadata(conn, search_query, depth=3)

class QueryModel(BaseModel):
    query: str
    depth: int

# Modificación en el backend (FastAPI)
class QueryResponseModel(BaseModel):
    message: str
    data: list[dict]

#async def background_search_and_store_metadata(
#    conn_str, query, depth=1, parent_doi=None
#):
#    loop = asyncio.get_event_loop()
#    await loop.run_in_executor(None, search_and_store_metadata, conn_str, query, depth, parent_doi)


#@app.post("/submit_query")
#async def submit_query(
#    query: QueryModel, background_tasks: BackgroundTasks
#):

@app.post("/submit_query")
def submit_query(query: QueryModel):

    # Conectar a la base de datos SQLite
    #conn = sqlite3.connect('///./micrawlerb.db')
    conn_str="///./micrawlerb.db"

    try:
        # Crear las tablas si no existen
        create_tables(conn_str)

        #background_search_and_store_metadata, conn_str, query.query, query.depth
        search_and_store_metadata(conn_str,query.query,query.depth)

        return JSONResponse(content={"message": "Operación finalizada"}, status_code=200)
    except Exception as e:
        # Manejar errores y devolver una respuesta adecuada
        raise HTTPException(detail=str(e), status_code=500)
    finally:


        # No cerrar la conexión a la base de datos aquí, ya que se ejecuta en segundo plano
        pass


def get_database_data():
    # Conectar a la base de datos SQLite
    conn = sqlite3.connect('///./micrawlerb.db')

    # Realizar una consulta para obtener los datos
    query ='''SELECT
    articles.doi,
    articles.title,
    articles.depth,
    articles.published_date,
    articles.citation_count,
    articles.num_apariciones,
    GROUP_CONCAT(article_authors.author) AS all_authors
FROM
    articles
JOIN
    article_authors ON articles.id = article_authors.article_id
GROUP BY
    articles.doi,
    articles.title,
    articles.published_date,
    articles.citation_count,
    articles.num_apariciones
ORDER BY
    articles.num_apariciones DESC,
    depth ASC,
    articles.published_date DESC,
    articles.citation_count DESC,
    all_authors DESC;
'''
    df = pd.read_sql_query(query, conn)

    # Cerrar la conexión a la base de datos
    conn.close()

    df.to_csv("resultados.csv", index=False, encoding="utf-8")
    return df

@app.get("/get_database_data")
def get_data():
    try:
        # Obtener los datos de la base de datos
        data = get_database_data().to_dict(orient="records")
        return JSONResponse(content=data, status_code=200)
    except Exception as e:
        # Manejar errores y devolver una respuesta adecuada
        raise HTTPException(detail=str(e), status_code=500)