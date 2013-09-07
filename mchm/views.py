from mchm import app, db, site_config
import json
from mongokit import Document, ObjectId
from werkzeug import exceptions as werkzeug_exceptions
from bson import json_util
from pymongo import errors as pymongo_exceptions
from flask import request, jsonify, abort
from datetime import datetime


@db.register
class Configdata(Document):
    __collection__ = 'configdata'
    __database__ = site_config.MONGO_DB_NAME
    structure = {
        'ttlstart': datetime,
        'meta-data': unicode,
        'user-data': unicode,
    }
    required_fields = {}
    default_values = {}


#Routes
@app.route('/')
def frontdoor():
    return 'Hi this is mchm.'


@app.route('/api/<docid>/')
@app.route('/api/<docid>/<field>')
def get_data(docid=None, field=None):
    try:
        doc = db.Configdata.fetch_one({'_id': ObjectId(docid)})
        if doc is None:
            abort(404)
        elif field is None:
            return json.dumps(doc, default=json_util.default)

        if unicode(field) == 'meta-data':
            return doc['meta-data']
        elif unicode(field) == 'user-data':
            return doc['user-data']
        else:
            abort(404)
    except (pymongo_exceptions.InvalidId, werkzeug_exceptions.NotFound):
        abort(404)
    except Exception as ex:
        app.logger.error(ex)
        abort(500)


@app.route('/api/submit', methods=['POST'])
def post_data():
    if request.headers['Content-Type'] != 'application/json':
        abort(415)

    userdata = request.get_json().get('user-data', None)
    metadata = request.get_json().get('meta-data', None)
    if userdata is None or metadata is None:
        abort(400)

    try:
        ttlstart = datetime.now()
        doc = db.Configdata()
        doc['ttlstart'] = ttlstart
        doc['user-data'] = userdata
        doc['meta-data'] = metadata
        doc.save()
        return jsonify(
            status='200',
            ttlstart=ttlstart.strftime('%c'),
            id=unicode(doc['_id'])
        )
    except Exception as ex:
        app.logger.error(ex)
        abort(500)
