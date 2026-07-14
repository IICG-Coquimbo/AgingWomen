# Usamos una imagen oficial de Python ligera
FROM python:3.11-slim

# Evita que Python escriba archivos .pyc en el disco
ENV PYTHONDONTWRITEBYTECODE=1
# Evita que Python guarde en el búfer los flujos de salida y error
ENV PYTHONUNBUFFERED=1

# Establece el directorio de trabajo
WORKDIR /app

# Instala las dependencias del sistema necesarias para psycopg2 y herramientas básicas
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia e instala los requerimientos
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del código del proyecto
COPY ./src /app/

# Exponemos el puerto por defecto de Django / Gunicorn
EXPOSE 8000