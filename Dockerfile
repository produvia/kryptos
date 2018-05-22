FROM gcr.io/kryptos-204204/krpytos-deps:latest

COPY . /app

WORKDIR /app
RUN pip install -e .


ENV UWSGI_INI /app/kryptos/uwsgi.ini

ENV STATIC_URL /static
ENV STATIC_PATH /app/kryptos/app/static
ENV STATIC_INDEX 1
ENV REDIS_HOST REDIS


# VOLUME ['~/.catalyst']


# COPY ./nginx.conf /etc/nginx/conf.d/

EXPOSE 80




