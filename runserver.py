#!/usr/bin/env python

from mchm import app, site_config

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=site_config.PORT)
