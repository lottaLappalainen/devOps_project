# slim photo for efficency
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 8199
ENV PYTHONUNBUFFERED=1

# run with gunicorn to be production-ish
CMD ["gunicorn", "--bind", "0.0.0.0:8199", "app:app"]
