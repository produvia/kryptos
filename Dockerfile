FROM kryptos-base

WORKDIR /app
RUN pip install -e .


ENV UWSGI_INI /app/kryptos/uwsgi.ini
# COPY ./nginx.conf /etc/nginx/conf.d/

EXPOSE 80




