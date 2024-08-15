FROM python:3.9-slim-buster

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    texlive \
    texlive-extra-utils \
    ghostscript \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/* /usr/share/doc /usr/share/man /usr/bin/dvisvgm /usr/bin/luajittex /usr/bin/luatex53 /usr/bin/luatex && \
    apt remove -y --no-install-recommends texlive-fonts-recommended && \
    apt remove -y --no-install-recommends openssl

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY static/ static/
COPY templates/ templates/

EXPOSE 5100
CMD ["python", "app.py"]
