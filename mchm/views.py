from mchm import app, db, site_config
import json
from mongokit import Document, ObjectId
from werkzeug import exceptions as werkzeug_exceptions
from bson import json_util
from pymongo import errors as pymongo_exceptions
from flask import request, jsonify, abort, render_template, url_for, Response
from datetime import datetime


@db.register
class Configdata(Document):
    __collection__ = 'configdata'
    __database__ = site_config.MONGO_DB_NAME
    structure = {
        'ttlstart': datetime,
        'meta-data': unicode,
        'user-data': unicode,
        'network-interfaces': unicode,
    }
    required_fields = {}
    default_values = {}


#Routes
@app.route('/')
def frontdoor():
    return Response(
        render_template('frontdoor.jinja2'),
        mimetype='text/plain'
    )


@app.route('/api/<docid>/')
@app.route('/api/<docid>/<field>')
def get_data(docid=None, field=None):
    try:
        doc = db.Configdata.fetch_one({'_id': ObjectId(docid)})
        if doc is None:
            abort(404)
        elif field is None:
            url = "http://{0}{1}".format(
                site_config.HOSTNAME, url_for('get_data', docid=docid)
            )
            return Response(
                render_template(
                    'base.jinja2', url=url, nw=doc['network-interfaces']
                ),
                mimetype='text/plain'
            )

        if unicode(field) == 'meta-data':
            return Response(
                render_template('data.jinja2', data=doc['meta-data']),
                mimetype='text/plain'
            )
        elif unicode(field) == 'user-data.jinja2':
            return Response(
                render_template('data.jinja2', data=doc['user-data']),
                mimetype='text/plain'
            )
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
    nwinterfaces = request.get_json().get('network-interfaces', '')

    if userdata is None or metadata is None:
        abort(400)

    try:
        ttlstart = datetime.utcnow()
        doc = db.Configdata()
        doc['ttlstart'] = ttlstart
        doc['user-data'] = userdata
        doc['meta-data'] = metadata
        doc['network-interfaces'] = nwinterfaces
        doc.save()
        url = "http://{0}{1}".format(
            site_config.ZEROCONF_IP, url_for('get_data', docid=doc['_id'])
        )
        outside_url = "http://{0}{1}".format(
            site_config.HOSTNAME, url_for('get_data', docid=doc['_id'])
        )
        return jsonify(
            status=200,
            ttltime=site_config.DOC_LIFETIME,
            ttlstart=ttlstart.strftime('%c'),
            id=unicode(doc['_id']),
            inside_url=url,
            outside_url=outside_url,
        )
    except Exception as ex:
        app.logger.error(ex)
        abort(500)
