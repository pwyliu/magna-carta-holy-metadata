import os
import sys
import logging
from logging import Formatter
from logging.handlers import RotatingFileHandler


def conf_app(app, conf_file='conf.py'):
    """
    Configure app from file in instance folder
    """
    conf_file = os.path.join(app.instance_path, conf_file)
    try:
        app.config.from_pyfile(conf_file)
    except IOError:
        print 'Error: No configuration file. Create it with:'
        if not os.path.isdir(os.path.dirname(conf_file)):
            print 'mkdir -p {}'.format(os.path.dirname(conf_file))
        print 'cp support/conf.py.example {}'.format(conf_file)
        print '\nConfigure as needed.\n'
        sys.exit(1)


def conf_sekrit(app, secret_file='app.key'):
    """
    http://flask.pocoo.org/snippets/104/
    """
    secret_file = os.path.join(app.instance_path, secret_file)
    try:
        app.config['SECRET_KEY'] = open(secret_file, 'rb').read()
    except IOError:
        print 'Error: No secret key. Create it with:'
        if not os.path.isdir(os.path.dirname(secret_file)):
            print 'mkdir -p {}'.format(os.path.dirname(secret_file))
        print 'head -c 32 /dev/urandom > {}\n'.format(secret_file)
        sys.exit(1)


def conf_logs(app, log_file='app.log', log_size=1048576, log_backups=5,
              loglevel=logging.WARNING):
    log_file = os.path.join(app.instance_path, log_file)
    file_handler = RotatingFileHandler(
        filename=log_file, maxBytes=log_size, backupCount=log_backups
    )
    file_handler.setLevel(loglevel)
    file_handler.setFormatter(Formatter(
        '%(asctime)s %(levelname)s: %(message)s '
        '[in %(pathname)s:%(lineno)d]'
    ))
    app.logger.addHandler(file_handler)
    app.logger.setLevel(loglevel)