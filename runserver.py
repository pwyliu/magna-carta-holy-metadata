#!/usr/bin/env python

from mchm import app, site_config

if __name__ == '__main__':
    app.run(port=site_config.PORT)
