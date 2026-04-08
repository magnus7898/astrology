FROM python:3.11-slim
 
WORKDIR /app
 
RUN apt-get update && apt-get install -y gcc g++ make && rm -rf /var/lib/apt/lists/*
 
COPY requirements.txt .
 
RUN pip install --no-cache-dir flask flask-cors gunicorn geopy timezonefinder pytz requests
 
RUN pip install --no-cache-dir swisseph || pip install --no-cache-dir pyswisseph || echo "swisseph install failed"
 
RUN python -c "import swisseph; print('swisseph OK')" || python -c "import pyswisseph; print('pyswisseph OK')" || echo "WARNING: no swisseph!"
 
COPY . .
 
CMD gunicorn app:app --bind 0.0.0.0:${PORT:-8080} --workers 1 --timeout 120
