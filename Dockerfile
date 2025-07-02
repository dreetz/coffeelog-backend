FROM python:3.12-alpine
LABEL authors="dennis"

WORKDIR /app
COPY . /app

RUN pip install uv
RUN uv sync
RUN chmod +x ./start.sh

CMD ["/bin/sh", "./start.sh"]