#!/bin/bash
# Stolen from http://senko.net/en/django-nginx-gunicorn/
set -e

LOGFILE=/var/log/gunicorn/mchm.log
LOGDIR=$(dirname $LOGFILE)

PORT=8000
NUM_WORKERS=2

USER=www-data
GROUP=www-data
APPPATH=/opt/magna-carta-holy-metadata
VENV=venv/bin/activate

cd $APPPATH
source $VENV
python mchm/build_index.py
test -d $LOGDIR || mkdir -p $LOGDIR
exec gunicorn -b 127.0.0.1:$PORT -w $NUM_WORKERS --user=$USER --group=$GROUP --log-level=debug --log-file=$LOGFILE 2>>$LOGFILE runserver:app