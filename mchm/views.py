from mchm import app, db, site_config
from mongokit import Document
from werkzeug import exceptions as werkzeug_exceptions
from pymongo import errors as pymongo_exceptions
from flask import request, jsonify, abort, render_template, url_for, Response
from datetime import datetime
import uuid


@db.register
class Configdata(Document):
    __collection__ = 'configdata'
    __database__ = site_config.MONGO_DB_NAME
    structure = {
        'created_at': datetime,
        'iid': unicode,
        'installtype': unicode,
        'metadata': unicode,
        'userdata': unicode,
        'ksdata': unicode,
        'phonehome_status': bool,
        'phonehome_time': datetime,
        'phonehome_data': dict,
    }
    required_fields = ['iid', 'created_at']
    default_values = {
        'phonehome_status': False,
        'phonehome_time': None,
        'phonehome_data': None,
        'metadata': None,
        'userdata': None,
        'ksdata': None,
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
            raise werkzeug_exceptions.NotFound
        if field is not None:
            field = unicode(field)

        # cloud-init install type
        if doc['installtype'] == 'cloud-init':
            if field is None:
                return Response(
                    render_template('base.jinja2', url=url),
                    mimetype='text/plain'
                )
            elif field == 'meta-data':
                resp = render_template('data.jinja2', data=doc['metadata'])
                return Response(resp, mimetype='text/plain')
            elif field == 'user-data':
                resp = render_template('data.jinja2', data=doc['userdata'])
                return Response(resp, mimetype='text/plain')
            elif field == 'phonehome':
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
            else:
                raise werkzeug_exceptions.BadRequest

        # kickstart install type
        elif doc['installtype'] == 'kickstart':
            if field is None:
                resp = render_template('data.jinja2', data=doc['ksdata'])
                return Response(resp, mimetype='text/plain')
            elif field == 'phonehome':
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
            else:
                raise werkzeug_exceptions.BadRequest

        # unknown install type
        else:
            raise

    except (pymongo_exceptions.InvalidId, werkzeug_exceptions.NotFound):
        abort(404)
    except (werkzeug_exceptions.BadRequest, pymongo_exceptions.DuplicateKeyError):
        abort(400)
    except Exception as ex:
        app.logger.error(ex)
        abort(500)


@app.route('/api/submit/', methods=['POST'])
def post_data():
    # Either JSON or GETOUT-SON
    if request.headers['Content-Type'] != 'application/json':
        abort(400)

    # get vars
    hostname = request.get_json().get('hostname', None)
    installtype = request.get_json().get('install-type', None)
    ksdata = request.get_json().get('ks-data', None)
    userdata = request.get_json().get('user-data', None)
    metadata = request.get_json().get('meta-data', None)

    # sanity check request
    if hostname is None or installtype not in ['cloud-init', 'kickstart']:
        abort(400)
    if installtype == 'kickstart' and ksdata is None:
        abort(400)
    if installtype == 'cloud-init' and (userdata is None or metadata is None):
        abort(400)

    # iid.hex is being used as a slug that can be predetermined by the client
    # before upload. This is a security risk sort of, but it's necessary so
    # that the uploaded data can contain the retrieval url and so we can do
    # this all in a single req->resp.
    iid = uuid.uuid5(uuid.NAMESPACE_DNS, str(hostname))
    iid = unicode(iid.hex)

    # Save data. If the entry already exists then overwrite it
    try:
        doc = db.Configdata.fetch_one({'iid': iid})
        if doc is None:
            doc = db.Configdata()

        doc['created_at'] = datetime.utcnow()
        doc['iid'] = iid
        doc['installtype'] = unicode(installtype)
        if installtype == 'kickstart':
            doc['ksdata'] = unicode(ksdata)
        elif installtype == 'cloud-init':
            doc['userdata'] = unicode(userdata)
            doc['metadata'] = unicode(metadata)
        doc.save()

        # generate urls and timestamp
        created_at = datetime.utcnow()
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
            created_at=doc['created_at'].strftime('%c'),
            iid=iid,
            zeroconf_url=zeroconf_url,
            ipv4_url=ipv4_url,
        )
    except Exception as ex:
        app.logger.error(ex)
        abort(500)