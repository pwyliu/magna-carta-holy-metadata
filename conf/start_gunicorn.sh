#!/bin/bash
# Stolen from http://senko.net/en/django-nginx-gunicorn/
set -e


APPPATH=/opt/magna-carta-holy-metadata
LOGFILE=$APPPATH/gunicorn.log

PORT=8000
NUM_WORKERS=2

USER=www-data
GROUP=www-data
VENV=venv/bin/activate

cd $APPPATH
source $VENV
python mchm/build_index.py
exec gunicorn -b 127.0.0.1:$PORT -w $NUM_WORKERS --user=$USER --group=$GROUP --log-level=debug --log-file=$LOGFILE 2>>$LOGFILE runserver:app