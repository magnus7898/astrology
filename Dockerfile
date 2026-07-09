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
