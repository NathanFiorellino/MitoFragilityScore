FROM python:3.11-slim-bullseye
RUN apt-get update && apt-get install -y \
    gcc \
    build-essential \
    libpq-dev \
    && apt-get clean

RUN pip install --no-cache-dir pandas\
&& pip install --no-cache-dir bio

WORKDIR /src

RUN pip install --no-cache-dir ViennaRNA

WORKDIR /src
CMD python MitoFragilityScore.py