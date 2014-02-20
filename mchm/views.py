import os
from datetime import datetime
from mongokit import Document, ObjectId
from werkzeug import exceptions as werkzeug_exceptions
from pymongo import errors as pymongo_exceptions
from flask import (request, jsonify, abort, render_template, url_for,
                   Response, Markup)
import markdown
from mchm import app, db, site_config


@db.register
class Configdata(Document):
    __collection__ = 'configdata'
    __database__ = site_config.MONGO_DB_NAME
    structure = {
        'created_at': datetime,
        'installtype': basestring,
        'metadata': unicode,
        'userdata': unicode,
        'ksdata': unicode,
        'phonehome_status': bool,
        'phonehome_time': datetime,
        'phonehome_data': dict,
    }
    required_fields = [
        'created_at', 'installtype', 'phonehome_status'
    ]
    default_values = {
        'metadata': u'',
        'userdata': u'',
        'ksdata': u'',
    }


#Routes
@app.route('/')
def frontdoor():
    rootdir = (os.path.join(os.path.dirname(__file__))).rpartition('/mchm')
    with open('{}/README.md'.format(rootdir[0]), 'r') as f:
        md = f.read()
    resp = markdown.markdown(md, ['fenced_code'])
    return Response(Markup(resp))


@app.route('/api/<objectid>/')
@app.route('/api/<objectid>/<field>/')
def get_data(objectid=None, field=None):
    try:
        # url is generated based on request so we can handle zeroconf and ipv4
        url = "{0}://{1}{2}".format(
            site_config.URL_SCHEME,
            request.headers['host'],
            url_for('get_data', objectid=objectid)
        )

        # Get doc
        doc = db.Configdata.fetch_one({'_id': ObjectId(objectid)})
        if doc is None:
            raise werkzeug_exceptions.NotFound

        # sanity checks
        if doc['installtype'] not in ['cloud-init', 'kickstart']:
            raise werkzeug_exceptions.InternalServerError
        if field is not None and doc['installtype'] == 'kickstart':
            raise werkzeug_exceptions.NotFound

        # return cloud-init data
        if doc['installtype'] == 'cloud-init':
            if field is None:
                resp = render_template('base.jinja2', url=url)
            elif field == 'meta-data':
                resp = render_template('data.jinja2', data=doc['metadata'])
            elif field == 'user-data':
                resp = render_template('data.jinja2', data=doc['userdata'])
            else:
                raise werkzeug_exceptions.NotFound
            return Response(resp, mimetype='text/plain')

        # return kickstart data
        if doc['installtype'] == 'kickstart':
            resp = render_template('data.jinja2', data=doc['ksdata'])
            return Response(resp, mimetype='text/plain')

    except (pymongo_exceptions.InvalidId, werkzeug_exceptions.NotFound):
        abort(404)
    except Exception as ex:
        app.logger.error(ex)
        abort(500)


@app.route('/api/submit/', methods=['POST'])
def post_data():
    # JSON or GTFO
    if request.headers['Content-Type'] != 'application/json':
        abort(406)

    # Get vars
    # objectid is the unique url we are storing data on, mapping to Mongo's
    # default _id. If objectid was not specified MCHM creates a new document
    # and returns the url it can be requested on in the response. If objectid
    # already exists the data is overwritten. If the objectid doesn't exist
    # MCHM returns an error.
    objectid = request.get_json().get('id', None)
    installtype = request.get_json().get('install-type', None)
    ksdata = request.get_json().get('ks-data', None)
    userdata = request.get_json().get('user-data', None)
    metadata = request.get_json().get('meta-data', None)

    # Create new document
    if objectid is None:
        if installtype not in ['cloud-init', 'kickstart']:
            abort(400)
        new = True
        doc = db.Configdata()
        doc['created_at'] = datetime.utcnow()
        doc['installtype'] = installtype
        doc['phonehome_status'] = False
    # Existing document
    else:
        doc = db.Configdata.fetch_one({'_id': ObjectId(objectid)})
        new = False
        if doc is None:
            abort(404)

    # Create or update document.
    try:
        if ksdata is not None:
            doc['ksdata'] = unicode(ksdata)
        if userdata is not None:
            doc['userdata'] = unicode(userdata)
        if metadata is not None:
            doc['metadata'] = unicode(metadata)
        doc.save()
    except Exception as ex:
        app.logger.error(ex)
        abort(500)

    zeroconf_url = "{0}://{1}{2}".format(
        site_config.URL_SCHEME,
        site_config.ZEROCONF_IP,
        url_for('get_data', objectid=str(doc['_id']))
    )
    ipv4_url = "{0}://{1}{2}".format(
        site_config.URL_SCHEME,
        site_config.HOSTNAME,
        url_for('get_data', objectid=str(doc['_id']))
    )

    if new:
        status = 'ok'
    else:
        status = 'updated'

    # response contains lookup url
    return jsonify(
        id=str(doc['_id']),
        created_at=doc['created_at'].strftime('%c'),
        installtype=doc['installtype'],
        ipv4_url=ipv4_url,
        zeroconf_url=zeroconf_url,
        ttl=site_config.DOC_LIFETIME,
        status=status,
        phonehome_status=doc['phonehome_status']
    )


@app.route('/api/phonehome/<objectid>/', methods=['GET', 'POST'])
def phone_home(objectid=None):
    try:
        doc = db.Configdata.fetch_one({'_id': ObjectId(objectid)})
        if doc is None:
            raise werkzeug_exceptions.NotFound

        if request.method == 'POST':
            doc['phonehome_time'] = datetime.utcnow()
            doc['phonehome_status'] = True
            doc['phonehome_data'] = request.form.to_dict()
            doc.save()

        return jsonify(
            phonehome_time=doc['phonehome_time'],
            phonehome_status=doc['phonehome_status'],
            phonehome_data=doc['phonehome_data'],
        )
    except (pymongo_exceptions.InvalidId, werkzeug_exceptions.NotFound):
        abort(404)
    except Exception as ex:
        app.logger.error(ex)
        abort(500)