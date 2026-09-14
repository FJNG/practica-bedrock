
# CASO 3 - APLICACIÓN CON AMAZON BEDROCK

## DESCRIPCIÓN


Se ha desarrollado una aplicación web con Python y Streamlit que utiliza diferentes modelos disponibles en Amazon Bedrock.

El objetivo es crear una herramienta de apoyo para un equipo de marketing y publicidad que permita generar imágenes, mejorar contenidos escritos y utilizar información propia de la empresa mediante técnicas de IA generativa.

1. PROBLEMA Y USUARIOS

---

La aplicación está pensada principalmente para diseñadores y redactores.

Historias de usuario:

* Como diseñador, quiero generar imágenes a partir de una descripción para crear propuestas visuales de forma rápida.

* Como redactor, quiero resumir, corregir o mejorar un texto para obtener contenidos más claros y adecuados.

* Como usuario de la aplicación, quiero consultar información contenida en documentos propios para que las respuestas generadas tengan en cuenta información interna.

2. ARQUITECTURA

---

La aplicación utiliza una arquitectura sencilla:

Usuario
|
Streamlit
|
app.py
|
Amazon Bedrock
|
+-- Claude -> generación y edición de texto
|
+-- Stable Diffusion -> generación de imágenes
|
+-- Titan Embeddings -> generación de embeddings para RAG
|
SQLite / documentos / información de la aplicación

Streamlit actúa como interfaz de usuario.

El código de la aplicación funciona como wrapper entre el usuario y Amazon Bedrock. Recibe la petición, prepara las instrucciones, llama al modelo correspondiente y procesa la respuesta antes de mostrarla.

Se ha elegido Amazon Bedrock porque permite utilizar diferentes modelos mediante una API gestionada, sin necesidad de instalar ni mantener los modelos en servidores propios.

Esto simplifica el desarrollo de la aplicación y permite utilizar los recursos bajo demanda.

3. MODELOS Y PARÁMETROS

---

CLAUDE

Se utiliza para las operaciones relacionadas con texto.

Para tareas como corregir o resumir se utilizan valores bajos de temperatura, ya que se busca una respuesta más precisa y estable.

Para tareas creativas se puede aumentar la temperatura para obtener respuestas más variadas.

STABLE DIFFUSION 3.5 LARGE

Se utiliza para generar imágenes a partir de las descripciones introducidas por el usuario.

El prompt contiene la descripción de la imagen y las características visuales solicitadas.

AMAZON TITAN EMBEDDINGS

Se utiliza para transformar los documentos en vectores numéricos.

Estos vectores permiten realizar búsquedas semánticas dentro del sistema RAG y localizar los fragmentos de información más relacionados con la consulta del usuario.

4. SYSTEM PROMPT

---

Claude recibe unas instrucciones generales que definen su comportamiento.

El objetivo es que actúe como asistente de creación y edición de contenidos.

Las principales reglas utilizadas son:

* Mantener el idioma utilizado por el usuario.
* No inventar datos que no estén disponibles.
* Responder de forma clara y útil.
* Respetar la tarea solicitada: resumir, corregir, mejorar o generar contenido.
* Si se utiliza información recuperada mediante RAG, basar la respuesta en ese contexto.

5. RAG Y MEMORIA

---

La aplicación utiliza RAG para poder responder utilizando información procedente de documentos propios.

El proceso básico es:

1. Se divide el documento en fragmentos.
2. Titan Embeddings transforma los fragmentos en vectores.
3. Se transforma también la pregunta del usuario en un vector.
4. Se buscan los fragmentos más similares.
5. Los fragmentos recuperados se proporcionan a Claude como contexto.
6. Claude genera la respuesta utilizando esa información.

De esta forma podemos poner instrucciones especificas por proyecto para enriquecer el contenido y guiar la generación.

RAG se utiliza para aportar conocimiento externo, mientras que la memoria serviría para conservar el contexto de una conversación.

6. ÉTICA Y SEGURIDAD

---

Se han tenido en cuenta diferentes aspectos de seguridad.

MODERACIÓN

Se controlan posibles respuestas bloqueadas por los mecanismos de seguridad de Amazon Bedrock y se gestionan los errores antes de mostrar el resultado al usuario.

PROMPT INJECTION

Las instrucciones del sistema se mantienen separadas del contenido introducido por el usuario para reducir el riesgo de que una entrada pueda modificar el comportamiento principal del modelo.

SESGO

Las respuestas generadas por los modelos deben considerarse propuestas que pueden necesitar revisión humana antes de su utilización definitiva.

PRIVACIDAD

La aplicación no debe enviar información sensible o confidencial a los modelos sin las medidas de protección necesarias.

COPYRIGHT

En la generación de imágenes y textos se debe evitar solicitar copias exactas de contenidos protegidos, marcas o trabajos de terceros.

7. FUNCIONALIDADES

---

La aplicación permite:

* Generar imágenes mediante Stable Diffusion.
* Resumir textos con Claude.
* Corregir textos.
* Mejorar contenidos.
* Generar variaciones de un texto.
* Utilizar documentos propios mediante RAG.
* Generar embeddings con Amazon Titan.
* Realizar búsquedas semánticas.
* Gestionar errores y respuestas bloqueadas.

8. TECNOLOGÍAS UTILIZADAS

---

* Python
* Streamlit
* Amazon Bedrock
* Claude
* Stable Diffusion 3.5 Large
* Amazon Titan Embeddings
* Boto3
* SQLite

9. REQUISITOS

---

Es necesario disponer de:

* Python instalado.
* Una cuenta de AWS.
* Acceso habilitado a Amazon Bedrock.
* Acceso a los modelos utilizados por la aplicación.
* Credenciales de AWS correctamente configuradas.

10. INSTALACIÓN

---

Instalar las dependencias:

pip install -r requirements.txt

11. EJECUCIÓN

---

Desde la carpeta del proyecto ejecutar:

streamlit run app.py

Streamlit iniciará la aplicación y abrirá la interfaz web en el navegador.

12. ESTRUCTURA DEL PROYECTO

---

La mayor parte de la lógica se encuentra actualmente en app.py.

Esta estructura se ha mantenido sencilla al tratarse de una práctica académica y de un producto mínimo viable.

En una aplicación de producción sería recomendable separar la aplicación en diferentes módulos:

* Interfaz de usuario.
* Acceso a Amazon Bedrock.
* Generación de imágenes.
* Procesamiento de texto.
* Sistema RAG.
* Persistencia.
* Seguridad y validaciones.

13. OBJETIVO DE LA PRÁCTICA

---

El objetivo principal del proyecto es experimentar de forma práctica con diferentes capacidades de Amazon Bedrock y comprobar cómo distintos modelos pueden colaborar dentro de una misma aplicación.

Claude se utiliza para lenguaje natural, Stable Diffusion para generación de imágenes y Titan Embeddings para búsqueda semántica.

De esta manera se demuestra un flujo completo de una aplicación de IA generativa conectada realmente con Amazon Bedrock.

## JUSTIFICACIÓN DE LOS MODELOS UTILIZADOS

Se han utilizado diferentes modelos porque cada uno está especializado en un tipo de tarea.

CLAUDE

Claude se utiliza para las tareas relacionadas con texto, como resumir, corregir, mejorar o generar variaciones.

Se ha elegido porque es un modelo de lenguaje orientado a la comprensión y generación de texto, y se adapta bien a tareas donde es necesario mantener el contexto, seguir instrucciones y producir respuestas claras.
El modelo haiku 4.5 se ha elegido por compatibilidad con mi tipo de cuenta 

STABLE DIFFUSION 3.5 LARGE

Stable Diffusion 3.5 Large se utiliza para la generación de imágenes a partir de texto.

Se ha elegido porque está especializado en generación visual y permite transformar una descripción escrita en una imagen.


AMAZON TITAN EMBEDDINGS

Amazon Titan Embeddings se utiliza dentro del sistema RAG.

Su función es convertir los textos y documentos en vectores numéricos que representan su significado.

Se ha elegido porque permite realizar búsquedas semánticas, es decir, localizar fragmentos relacionados por su significado 
y no únicamente por coincidencia exacta de palabras.

Esto permite recuperar información relevante de los documentos y proporcionársela posteriormente a Claude como contexto.

AMAZON BEDROCK

Los modelos se consumen a través de Amazon Bedrock.

Se ha elegido Bedrock porque permite acceder a diferentes modelos mediante una API gestionada sin tener que desplegar y mantener los modelos en servidores propios.

Además, permite utilizar distintos modelos especializados dentro de una misma aplicación y pagar únicamente por el uso realizado.


## ENLACE A VIDEO EXPLICATIVO YOUTUBE
https://youtu.be/HKKby_IKGWo

## URL REPOSITORIO
https://github.com/FJNG/practica-bedrock