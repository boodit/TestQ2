FROM python:3.10.6

RUN mkdir /fastapi_app

WORKDIR /fastapi_app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

RUN chmod a+x docker/*.sh

#CMD ["gunicorn", "src.main:app", "--workers 1", "--worker-class uvicorn.workers.UvicornWorker", "--bind=0.0.0.0:8000"]
#CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
#CMD ["gunicorn", "src.main:app", "--workers", "1", "--worker-class", "uvicorn.workers.UvicornH11Worker", "--bind", "0.0.0.0:8000"]
