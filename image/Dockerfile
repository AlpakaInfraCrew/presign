FROM python:3.9-alpine
RUN apk add --no-cache poetry cargo g++ libffi-dev npm
RUN npm install -g typescript

RUN mkdir /app
COPY poetry.lock pyproject.toml /app/

WORKDIR /app

RUN poetry export -f requirements.txt -o requirements.txt 
RUN pip install --verbose -r requirements.txt

COPY . /app

RUN chmod +x /app/image/run.sh

ENTRYPOINT /app/image/run.sh
