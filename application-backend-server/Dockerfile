# Application Backend Server: Flask API (/hello, /secure, /student, /students-db)
FROM python:3.12-alpine
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py students.json ./
COPY templates/ templates/
RUN adduser -D -u 10001 app
USER app
EXPOSE 8081
CMD ["gunicorn","--bind","0.0.0.0:8081","--workers","2","--access-logfile","-","app:app"]
