# Youtube AI Briefer #

Transcribe un video de Youtube y lo procesa con IA para obtener un resumen completo del contenido. Para funcionar debes setear `OPENAI_API_KEY` en el Entorno

Construida con Tkinter (multiplataforma)

https://github.com/Ch3my/Youtube-AI-Briefer/assets/35230589/bc8f1b97-958e-41c4-aa74-0a564470f50b

## Googla Colab ##

Se incluye una version de Google Colab `youtube_briefer_colab.py`

## Funcionamiento ##

La aplicacion funciona obteniendo el transcript de un video de youtube y rompiendolo en secciones mas pequeñas analiza cada seccion y toma notas.

Luego toma todas las notas y las condensa en un solo documento que es el que se le muestra al usuario.

Para tomar las notas utiliza GPT-3.5 y para la condensacion GPT-4o. Esto es completamente custumizable en la configuracion.

Aunque se puede pasar el texto completo a GPT-4, es mas caro. Ademas, si el texto es largo aumenta mas los precios debido a la gran cantidad de tokens de entrada.

Si es un texto de un video corto no importaria tanto pero si es un video largo es mejor condensarlo antes de pasarlo a GPT-4. Para el primer paso de condensar la informacion GPT-3.5-turbo es suficientemente inteligente y como es mas barato podemos reducir costos.

Asi solo le entregamos la informacion resumida a GPT-4 y este ejecuta solo el ultimo paso, con menos texto lo que resulta en costos reducidos.

Mezclar los modelos reduce costo porque la cantidad de token que procesa GPT-4 es bastante menor al tener la informacion resumida ya. Estamos hablando de un 70% menos de informacion que procesa GPT-4 por resumirla antes

En caso de no poder obtener la transcripcion de manera gratuita, el sistema intenta utilizar whisper para obtener la transcripcion, esto lo realiza con previa confirmacion del usuario para evitar incurrir en costos ya que Whisper podria salir caro si es muy largo el video

### Whisper
Para poder utilizar Whisper debes tener una API de OpenAI habilitado y tener ffmpeg instalado en la maquina. Para usar whisper no es necesario ffmpeg pero es necesario para cortar el audio si es necesario antes de pasarlo a la API de Whisper

- Download the latest version of FFmpeg from the official website.
- Extract the contents to a folder (e.g., C:\ffmpeg).
- Add the bin directory of the extracted folder to your system’s PATH

### RAG, chat con la transcripcion ###
Al obtener el transcript tambien Genera un RAG del texto, permitiendo al usuario hacer preguntas sobre el video y la AI le responde utilizando el contexto, esto es util en el caso de que quieras mas informacion sobre un tema en el resumen.

Al hacer preguntas al RAG tambien hay un boton que te muestra los extractos del texto que utilizo para generar la respuesta.

Para crear el RAG estamos usando embeddings de manera local, por lo tanto no incurre en gastos, pero depende de la maquina local. Usualmente toma unos 3 segundos de procesamiento para crearlo.

Tambien se configuro un `Hybrid-Search` que utiliza busqueda semantica como de palabras claves, que segun las pruebas mejora el contexto un poco (10%), segun las pruebas mezclar el hybrid-search con `MMR` mejora la respuesta final un poco mas (25%)

#### Filtros por TAGS ####
Por configuracion se puede habilitar los filtros por Tags, si esta habilitado, luego de generar los chunks, por cada chunk genera una lista de tags que incluye dentro de la metada del chunk. 

Al buscar en el la base de datos, toma en cuenta estos tags, primero genera tags relevantes basado en la pregunta del usuario y compara los tags de los chunk con los tags generados por el usuario y filtra aquellos que contienen los tags. Si no coincide ningun tag solo devuelve todo lo que encontro

## Calidad entre una sola tarea (1 paso) y preprocesar (2 pasos) ##

Obviamente el mejor resumen es utilizar GPT-4 para ambos pasos, resumir y procesar al final.

Un solo paso con GPT-4 y, por otro lado, preprocesar con GPT-3.5 y solo organizar con GPT-4 tienen resultados similares. Pero solo usar GPT-4 es mas caro

En Junio 2024, GPT-4 es aproximadamente 10x mas caro que usar GPT-3.5 pero tambien es aproximadamente 10x mas inteligente y logra resultados muchisimo mejores. Por lo tanto, es necesario a la hora de condensar la informacion resumida.

## Ambiente Desarrollo  ##

Se intento usar Poetry (https://python-poetry.org/) para manejar las dependencias de Python, pero finalmente se hizo sin Poetry (se puede completar en el futuro)

Instalar dependencias:

``` 
pip install pyinstaller youtube_transcript_api markdown2 pyperclip tkinterweb langchain-openai langchain langchain-core langchain-anthropic langchain_chroma langchain-huggingface rank_bm25 faiss-cpu pygame yt-dlp
```

Con esto ya se puede desarrollar en VS Code e iniciar el programa haciendo correr `main.py`

NOTA. si error al instalar langchain-huggingface quiza se deba a esto: https://learn.microsoft.com/en-us/windows/win32/fileio/maximum-file-path-limitation?tabs=registry#enable-long-paths-in-windows-10-version-1607-and-later

### Entorno virtual ###

Crear entorno

`python -m venv .venv`

Activar entorno

`.venv\Script\Activate`

Luego instalar paquetes dentro del entorno

## Compilar a Ejecutable ##

Este comando creara un ejecutable en la carpeta `dist/`

```
pyinstaller -n "Youtube AI Briefer" --collect-all tkinterweb --collect-all langchain --collect-all scipy --collect-all sentence_transformers --collect-all transformers --collect-all posthog --collect-all chromadb --noconfirm --windowed --icon=assets/favicon.ico main.py
```

o dependiendo de tu entorno (pyinstaller como modulo |case-sensitive| )

```
python -m PyInstaller -n "Youtube AI Briefer" --collect-all tkinterweb --collect-all langchain --collect-all scipy --collect-all sentence_transformers --collect-all transformers --collect-all posthog --collect-all chromadb --noconfirm --windowed --icon=assets/favicon.ico main.py
```

Nota. Ocurio un error que decia "ModuleNotFoundError: No module named 'bindings'" luego de compilar, aunque durante la compilacion no dio ningun mensaje. Para solucionar hay que incluir `--collect-all tkinterweb` los otros --collect-all son por mesajes similares

https://stackoverflow.com/questions/68027424/python-modulenotfounderror-no-module-named-bindings-error-only-when-i-compi

## Notas ##

### 06-2024 - LLM OpenSource ###
Se hicieron muchas pruebas con LLM opensource, Llama3, Phi, command-r y aya. Todos en general entregan resultados similares a GPT-3.5. Okay en el resumen y bastante deficiente a la hora de condensar la informacion.

En teoria se podria usar un LLM opensource para el paso de resumir, pero eso requeriria tener un servidor o cargar el modelo de forma local, que en maquinas lentas se comeria la performance
