#!/bin/sh
# Stolen from http://senko.net/en/django-nginx-gunicorn/
set -e

LOGFILE=/var/log/gunicorn/mchm.log
LOGDIR=$(dirname $LOGFILE)

PORT=8000
NUM_WORKERS=2

USER=www-data
GROUP=www-data

cd /opt/magna-carta-holy-metadata
source venv/bin/activate
test -d $LOGDIR || mkdir -p $LOGDIR
exec gunicorn -b 127.0.0.1:$POST -w $NUM_WORKERS --user=$USER --group=$GROUP --log-level=debug --log-file=$LOGFILE 2>>$LOGFILE