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
        index = db.configdata.ensure_index(
            'ttlstart',
            pymongo.DESCENDING,
            expireAfterSeconds=site_config.LIFETIME
        )

        if index is not None:
            print "{0} successfully created".format(index)
            sys.exit(0)
        else:
            print "No new indexes created."
            sys.exit(0)
    except Exception as ex:
        print "Error: {0}".format(unicode(ex))
        sys.exit(1)