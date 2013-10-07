from mchm import app, db, site_config
from mongokit import Document, ObjectId, MultipleResultsFound
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
        'ci_phonehome': (datetime, bool, dict),
        'metadata': unicode,
        'userdata': unicode,
    }
    required_fields = ['iid', 'created_at', 'metadata', 'userdata']
    default_values = {
        'ci_phonehome': (None, False, None),
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
@app.route('/api/<iid>/<field>', methods=['GET', 'POST'])
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
                doc['ci_phonehome'] = (
                    datetime.utcnow(), True, request.form.to_dict()
                )
                doc.save()
            return jsonify(
                status=200,
                phonehome_timestamp=doc['ci_phonehome'][0],
                phonehome_status=doc['ci_phonehome'][1],
                phonehome_data=doc['ci_phonehome'][2]
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

    iid = unicode(request.get_json().get('iid', None))
    userdata = unicode(request.get_json().get('user-data', None))
    metadata = unicode(request.get_json().get('meta-data', None))

    if userdata is None or metadata is None or iid is None:
        abort(400)
    try:
        created_at = datetime.utcnow()
        doc = db.Configdata()
        doc['created_at'] = created_at
        doc['iid'] = iid
        doc['userdata'] = userdata
        doc['metadata'] = metadata
        doc.save()
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
            status=200,
            ttl=site_config.DOC_LIFETIME,
            created_at=created_at.strftime('%c'),
            iid=iid,
            zeroconf_url=zeroconf_url,
            ipv4_url=ipv4_url,
        )
    except Exception as ex:
        app.logger.error(ex)
        abort(500)