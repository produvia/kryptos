FROM kryptos-deps

WORKDIR /app
RUN pip install -e .


ENV UWSGI_INI /app/kryptos/uwsgi.ini

ENV STATIC_URL /static
ENV STATIC_PATH /app/kryptos/app/static
ENV STATIC_INDEX 1

# COPY ./nginx.conf /etc/nginx/conf.d/

EXPOSE 80




