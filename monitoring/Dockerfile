FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 8400
CMD ["gunicorn", "--bind", "0.0.0.0:8400", "app:app"]
