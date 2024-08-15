FROM python:3.9-slim-buster

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    texlive \
    texlive-extra-utils \
    ghostscript \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY static/ static/
COPY templates/ templates/

EXPOSE 5100
CMD ["python", "app.py"]
