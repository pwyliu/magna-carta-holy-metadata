#!/usr/bin/env python
import site_config
import pymongo
import sys

if __name__ == '__main__':
    try:
        client = pymongo.MongoClient(site_config.MONGO_URI)
        db = client[site_config.MONGO_DB_NAME]
        #Drop and recreate indexes
        db.configdata.drop_indexes()
        ttl_index = db.configdata.ensure_index(
            'created_at',
            pymongo.DESCENDING,
            expireAfterSeconds=site_config.DOC_LIFETIME
        )
        print "Indexes successfully created"
        sys.exit(0)
    except Exception as ex:
        print "Error: {0}".format(unicode(ex))
        sys.exit(1)