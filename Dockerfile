FROM python:3.11-slim

WORKDIR /ctf

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .

EXPOSE 5000

# init_db runs inside app.py at startup so it picks up env vars from docker-compose
CMD ["python", "app.py"]
