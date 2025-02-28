FROM python:3.11-alpine
LABEL authors="dennis"

WORKDIR /app
COPY . /app

RUN pip install -r requirements.txt

CMD ["fastapi", "run"]