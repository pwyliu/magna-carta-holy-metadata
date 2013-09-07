#!/usr/bin/env python

from mchm import app, site_config

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=site_config.PORT)