FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc g++ make git \
    libssl-dev libffi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

RUN python -c "import swisseph; print('swisseph READY')"

COPY . .

CMD sh -c "gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120"


RUN python -c "import urllib.request,zipfile,io; \
d=urllib.request.urlopen(urllib.request.Request('https://download.geonames.org/export/dump/cities500.zip',headers={'User-Agent':'magnus/1.0'}),timeout=300).read(); \
zipfile.ZipFile(io.BytesIO(d)).extract('cities500.txt','/app')"
