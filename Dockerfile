FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc g++ make git \
    libssl-dev libffi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir flask flask-cors gunicorn geopy timezonefinder pytz requests

# Try all possible swisseph package names
RUN pip install --no-cache-dir pyswisseph \
    && python -c "import swisseph; print('pyswisseph OK as swisseph')" \
    || pip install --no-cache-dir swisseph==2.10.3.2 \
    || pip install --no-cache-dir astropy \
    || echo "trying from github..." \
    && pip install --no-cache-dir git+https://github.com/astrorigin/pyswisseph.git

RUN python -c "import swisseph; print('swisseph READY')"

COPY . .

CMD gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120
