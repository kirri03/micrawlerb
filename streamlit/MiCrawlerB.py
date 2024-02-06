import streamlit as st
import requests
import pandas as pd
import websockets
import asyncio
from streamlit.web import cli as stcli
from streamlit import runtime
import threading
#from streamlit.report_thread import add_report_ctx

st.set_page_config(page_title='MiCrawlerB', layout='wide', page_icon="📈")

st.header("MiCrawlerB")
st.subheader("Introduce your search")

# La función para recibir actualizaciones del servidor
#async def receive_updates():
#    uri = "ws://fastapi:8000/ws"  # Asegúrate de actualizar con la dirección correcta del servidor
#    async with websockets.connect(uri) as websocket:
#        while True:
#            message = await websocket.recv()
#            st.info(message)

#def background_thread():
#    loop = asyncio.new_event_loop()
#    asyncio.set_event_loop(loop)
#    loop.run_until_complete(receive_updates())

# Modificar para que Streamlit ejecute la función en un hilo de fondo
#if __name__ == '__main__':
#    if runtime.exists():
#        thread = threading.Thread(target=background_thread)
#        thread.start()

def submit_query(query: str, depth: int):
    data = {"query": query, "depth": depth}
    respuesta = requests.post("http://fastapi:8000/submit_query", json=data)
    return respuesta.json()

query = st.text_input("Query")
depth = int(st.number_input("Depth", value=1, step=1))

if st.button("Search"):
    if query and depth:
        response = submit_query(query, depth>=0)
        st.success(response["message"])

        #st.markdown("The depth is better the higher because in this case the higher the depth the more previosly the article was found")

        # Realizar una solicitud al backend para obtener los datos
        response = requests.get(f"http://fastapi:8000/get_database_data")

       #if response.status_code == 200:
        #    if __name__ == '__main__':
         #       if runtime.exists():
          #          loop = asyncio.new_event_loop()
           #         asyncio.set_event_loop(loop)
            #        loop.run_until_complete(receive_updates())
            #data = response.json()
            #df = pd.DataFrame(data)

        data = response.json()
        df = pd.DataFrame(data)

        # Mostrar los datos en Streamlit
        st.write("Contenido de la tabla 'articles':")
        st.write(df)
        #else:
            #st.error(f"Error al obtener datos del backend. Detalles: {response.text}")
    else:
        st.warning("You must introduce a query and a depth")
