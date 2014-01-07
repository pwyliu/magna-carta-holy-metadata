from mchm import app, db, site_config
from mongokit import Document
from werkzeug import exceptions as werkzeug_exceptions
from pymongo import errors as pymongo_exceptions
from flask import request, jsonify, abort, render_template, url_for, Response
from datetime import datetime


@db.register
class Configdata(Document):
    __collection__ = 'configdata'
    __database__ = site_config.MONGO_DB_NAME
    structure = {
        'iid': unicode,
        'created_at': datetime,
        'phonehome_status': bool,
        'phonehome_time': datetime,
        'phonehome_data': dict,
        'metadata': unicode,
        'userdata': unicode,
    }
    required_fields = ['iid', 'created_at', 'metadata', 'userdata']
    default_values = {
        'phonehome_status': False,
        'phonehome_time': None,
        'phonehome_data': None,
    }


#Routes
@app.route('/')
def frontdoor():
    url = "{0}://{1}".format(site_config.URL_SCHEME, request.headers['host'])
    return Response(
        render_template('frontdoor.jinja2', url=url),
        mimetype='text/plain'
    )


@app.route('/api/<iid>/')
@app.route('/api/<iid>/<field>/', methods=['GET', 'POST'])
def get_data(iid=None, field=None):
    try:
        doc = db.Configdata.fetch_one({'iid': iid})
        url = "{0}://{1}{2}".format(
            site_config.URL_SCHEME,
            request.headers['host'],
            url_for('get_data', iid=iid)
        )
        if doc is None:
            abort(404)

        # base
        if field is None:
            return Response(
                render_template('base.jinja2', url=url),
                mimetype='text/plain'
            )
        # userdata or metadata
        if unicode(field) == 'meta-data':
            return Response(
                render_template('data.jinja2', data=doc['metadata']),
                mimetype='text/plain'
            )
        elif unicode(field) == 'user-data':
            return Response(
                render_template('data.jinja2', data=doc['userdata']),
                mimetype='text/plain'
            )
        # cloud-init phonehome module
        elif unicode(field) == 'phonehome':
            if request.method == 'POST':
                doc['phonehome_time'] = datetime.utcnow()
                doc['phonehome_status'] = True
                doc['phonehome_data'] = request.form.to_dict()
                doc.save()
            return jsonify(
                status='ok',
                phonehome_time=doc['phonehome_time'],
                phonehome_status=doc['phonehome_status'],
                phonehome_data=doc['phonehome_data'],
            )
        else:
            abort(404)
    except (pymongo_exceptions.InvalidId, werkzeug_exceptions.NotFound):
        abort(404)
    except pymongo_exceptions.DuplicateKeyError:
        abort(400)
    except Exception as ex:
        app.logger.error(ex)
        abort(500)


@app.route('/api/submit/', methods=['POST'])
def post_data():
    # basic sanity checks
    iid = request.get_json().get('iid', None)
    userdata = request.get_json().get('user-data', None)
    metadata = request.get_json().get('meta-data', None)
    if request.headers['Content-Type'] != 'application/json':
        abort(415)
    if userdata is None or metadata is None or iid is None:
        abort(400)

    try:
        created_at = datetime.utcnow()

        # if the iid already exists then overwrite it
        doc = db.Configdata.fetch_one({'iid': iid})
        if doc is None:
            doc = db.Configdata()
        doc['created_at'] = created_at
        doc['iid'] = unicode(iid)
        doc['userdata'] = unicode(userdata)
        doc['metadata'] = unicode(metadata)
        doc.save()

        # generate urls
        zeroconf_url = "{0}://{1}{2}".format(
            site_config.URL_SCHEME,
            site_config.ZEROCONF_IP,
            url_for('get_data', iid=doc['iid'])
        )
        ipv4_url = "{0}://{1}{2}".format(
            site_config.URL_SCHEME,
            site_config.HOSTNAME,
            url_for('get_data', iid=doc['iid'])
        )
        return jsonify(
            status='ok',
            ttl=site_config.DOC_LIFETIME,
            created_at=created_at.strftime('%c'),
            iid=iid,
            zeroconf_url=zeroconf_url,
            ipv4_url=ipv4_url,
        )
    except Exception as ex:
        app.logger.error(ex)
        abort(500)