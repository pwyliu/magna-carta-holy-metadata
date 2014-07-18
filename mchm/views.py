import os
from datetime import datetime
from mongokit import Document, ObjectId
from werkzeug import exceptions as werkzeug_exceptions
from pymongo import errors as pymongo_exceptions
from flask import (request, jsonify, abort, render_template, url_for,
                   Response, Markup)
import markdown
from mchm import app, db


@db.register
class Configdata(Document):
    __collection__ = app.config['MONGO_COLLECTION_NAME']
    __database__ = app.config['MONGO_DB_NAME']
    structure = {
        'created_at': datetime,
        'install_type': unicode,
        'metadata': unicode,
        'userdata': unicode,
        'ksdata': unicode,
        'phonehome_status': bool,
        'phonehome_time': datetime,
        'phonehome_data': dict,
    }
    required_fields = ['created_at', 'install_type', 'phonehome_status']
    default_values = {'metadata': u'', 'userdata': u'', 'ksdata': u''}


#Routes
@app.route('/')
def frontdoor():
    project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    with open('{}/README.md'.format(project_dir)) as f:
        md = f.read()
    resp = markdown.markdown(md, ['fenced_code'])
    return Response(Markup(resp))


@app.route('/api/lookup/<objectid>/')
@app.route('/api/lookup/<objectid>/<field>/')
def get_data(objectid=None, field=None):
    try:
        # Get doc
        try:
            doc = db.Configdata.fetch_one({'_id': ObjectId(objectid)})
            if doc is None:
                abort(404)
        except pymongo_exceptions.InvalidId:
            doc = None
            abort(404)

        # url is based on the request so we can handle zeroconf and ipv4
        url = "{}://{}{}".format(
            app.config['URL_SCHEME'], request.headers['host'],
            url_for('get_data', objectid=str(doc['_id']))
        )

        # cloud-init
        resp = None
        if doc['install_type'] == u'cloud-init':
            if field is None:
                resp = render_template('base.jinja2', url=url)
            elif field == u'meta-data':
                resp = render_template('data.jinja2', data=doc['metadata'])
            elif field == u'user-data':
                resp = render_template('data.jinja2', data=doc['userdata'])
            else:
                abort(404)
            return Response(resp, mimetype='text/plain')

        # kickstart
        elif doc['install_type'] == u'kickstart':
            resp = render_template('data.jinja2', data=doc['ksdata'])
            return Response(resp, mimetype='text/plain')

        else:
            abort(500)

    except werkzeug_exceptions.HTTPException as ex:
        raise ex  # keep raising
    except Exception as ex:
        app.logger.error(ex)
        abort(500)


@app.route('/api/submit', methods=['POST'])
def post_data():
    # JSON or GTFO
    if request.headers['Content-Type'] != 'application/json':
        abort(406)

    objectid = request.get_json().get('id', None)
    install_type = request.get_json().get('install-type', None)
    ksdata = request.get_json().get('ks-data', None)
    userdata = request.get_json().get('user-data', None)
    metadata = request.get_json().get('meta-data', None)

    if (install_type is not None
            and install_type not in [u'cloud-init', u'kickstart']):
        abort(400)

    # Create new document if None
    if objectid is None:
        status = u'ok'
        doc = db.Configdata()
        doc['created_at'] = datetime.utcnow()
        doc['install_type'] = install_type
        doc['phonehome_status'] = False
    else:
        status = u'updated'
        try:
            doc = db.Configdata.fetch_one({'_id': ObjectId(objectid)})
            if doc is None:
                abort(404)
        except pymongo_exceptions.InvalidId:
            doc = None
            abort(404)

    try:
        if ksdata is not None:
            doc['ksdata'] = unicode(ksdata)
        if userdata is not None:
            doc['userdata'] = unicode(userdata)
        if metadata is not None:
            doc['metadata'] = unicode(metadata)
        doc.save()
    except Exception as ex:
        app.logger.error("Couldn't save document: {}".format(ex))
        abort(500)

    docid = unicode(doc['_id'])
    zeroconf_url = "{}://{}{}".format(
        app.config['URL_SCHEME'], app.config['ZEROCONF_IP'],
        url_for('get_data', objectid=docid)
    )
    ipv4_url = "{}://{}{}".format(
        app.config['URL_SCHEME'], app.config['HOSTNAME'],
        url_for('get_data', objectid=docid)
    )

    return jsonify(
        id=docid,
        created_at=doc['created_at'].strftime('%c'),
        install_type=doc['install_type'],
        ipv4_url=ipv4_url,
        zeroconf_url=zeroconf_url,
        ttl=app.config['DOC_LIFETIME'],
        status=status,
        phonehome_status=doc['phonehome_status']
    )


@app.route('/api/phonehome/<objectid>', methods=['GET', 'POST'])
def phone_home(objectid=None):
    try:
        try:
            doc = db.Configdata.fetch_one({'_id': ObjectId(objectid)})
            if doc is None:
                abort(404)
        except pymongo_exceptions.InvalidId:
            doc = None
            abort(404)

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
    except werkzeug_exceptions.HTTPException as ex:
        raise ex  # keep raising
    except Exception as ex:
        app.logger.error(ex)
        abort(500)