#!/usr/bin/env python

from flask.ext.script import Manager
from mchm import app, __VERSION__
import pymongo
import pymongo.collection
import sys

manager = Manager(app)


@manager.command
def hello():
    print __VERSION__


@manager.command
def build_indexes():
    # get collection
    client = pymongo.MongoClient(app.config['MONGO_URI'])
    db = client[app.config['MONGO_DB_NAME']]
    coll = db[app.config['MONGO_COLLECTION_NAME']]

    #Drop and recreate indexes
    print 'Dropping indexes...'
    coll.drop_indexes()
    print 'Creating indexes...'
    coll.ensure_index(
        'created_at', pymongo.DESCENDING,
        expireAfterSeconds=app.config['DOC_LIFETIME'])
    print "Done"
    sys.exit(0)


if __name__ == "__main__":
    manager.run()