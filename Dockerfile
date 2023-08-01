# Utilizar una imagen base con Python 3.10
FROM python:3.10

# Configurar el directorio de trabajo en el contenedor
WORKDIR /usr/src/app

# Copiar el archivo de requerimientos e instalar las dependencias
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copiar los archivos de la aplicación
COPY server.py wsgi.py ./

# Exponer el puerto en el que se ejecutará la aplicación
EXPOSE 8000

# Comando para ejecutar la aplicación con Gunicorn
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "wsgi:app"]

