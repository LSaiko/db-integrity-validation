FROM python:3.12-slim
RUN pip install --no-cache-dir flask==3.1.* psycopg2-binary==2.9.*
COPY app.py .
CMD ["python", "app.py"]
