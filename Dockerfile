FROM python:3.11-slim

WORKDIR /ctf

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .

RUN python init_db.py

EXPOSE 5000

CMD ["python", "app.py"]
