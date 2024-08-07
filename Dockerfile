FROM python:3.9-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    texlive \
    texlive-extra-utils \
    texlive-latex-extra \
    ghostscript \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5100

CMD ["python", "app.py"]
