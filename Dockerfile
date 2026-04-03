FROM python:3.12-slim

WORKDIR /app

COPY setup.py README.md ./
COPY openage/ ./openage/
RUN pip install -e "." --no-cache-dir

RUN pip install fastapi uvicorn[standard] anthropic python-multipart --no-cache-dir

COPY app/ ./app/

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
