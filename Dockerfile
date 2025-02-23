FROM python:3.13-alpine

WORKDIR /app

COPY main.py /app/
COPY requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]
