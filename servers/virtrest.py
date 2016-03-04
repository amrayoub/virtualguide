#!flask/bin/python
# -*- coding: utf-8 -*-

import gevent
from gevent import monkey
monkey.patch_all()

import hashlib
import mimetypes
import ConfigParser
from time import time
from re import search
from M2Crypto import RSA
from gridfs import GridFS
from ast import literal_eval
from base64 import b64decode
from bson.json_util import dumps
from gevent.wsgi import WSGIServer
from flask.ext.pymongo import PyMongo
from flask import Flask, make_response, abort, request, session
from pymongo import database, MongoClient, ReturnDocument

config = ConfigParser.SafeConfigParser({
    'host': '127.0.0.1',
    'port': 27017,
    'dbname': 'virtualrest',
    'user': None,
    'passwd': None,
    'replicaset': None
})

config.read('./virtrest.cfg')

virtualrest = Flask(__name__)

MONGO_HOST = config.get('MONGODB', 'host')
MONGO_PORT = int(config.get('MONGODB', 'port'))
MONGO_DBNAME = config.get('MONGODB', 'dbname')
MONGO_USER = config.get('MONGODB', 'user')
MONGO_PASSWD = config.get('MONGODB', 'passwd')
MONGO_REPLICA_SET = config.get('MONGODB', 'replicaset')
GRIDFS_HOST = config.get('GRIDFS', 'host')
GRIDFS_PORT = int(config.get('GRIDFS', 'port'))

virtualrest.config['SECRET_KEY'] = 'KKkjhdfg985#@s9865kjghfkjdhABLABS765765765';

virtualrest.config['MONGO_HOST'] = MONGO_HOST
virtualrest.config['MONGO_PORT'] = MONGO_PORT
virtualrest.config['MONGO_DBNAME'] = MONGO_DBNAME
virtualrest.config['MONGO_USERNAME'] = MONGO_USER
virtualrest.config['MONGO_PASSWORD'] = MONGO_PASSWD
virtualrest.config['MONGO_REPLICA_SET'] = MONGO_REPLICA_SET

mongodb = PyMongo(virtualrest)

def lang_parse(isocode):
    if (isocode is not None):
        isocode = isocode.lower().replace('_','-')
    else:
        return None
    lang_regex = search('^([a-z]{2}-[a-z]{2}|[a-z]{2})$',isocode)
    lang = lang_regex.group(0)
    if (lang_regex is None):
        return None
    if (lang in fallback.keys()):
        return fallback[lang]
    search_result = mongodb.db.translations.find({'isocode': lang},{'_id':0,'isocode':1})
    if (search_result.count() < 1):
        if (lang[:2] in fallback.keys()):
            return fallback[lang[:2]]
        else:
            return None
    return lang

def_headers = {
    'Access-Control-Allow-Origin' : '*',
    'Content-Type' : 'application/json; charset=UTF-8',
    'Access-Control-Max-Age': 86400,
    'Access-Control-Allow-Credentials': True,
}

def output_json(obj, code, headers=None):
    resp = make_response(dumps(obj), code)
    resp.headers.extend(headers or {})
    return resp

@virtualrest.route('/colors')
def colors():
    if (not session.get('logged_in')):
        abort(403)
    resp_items = []
    search_result = mongodb.db.configs.find({},{'_id':0,'bgcolor':1,'header_color':1, 'font_color': 1})
    return output_json({'Colors' : search_result}, 200, def_headers)

@virtualrest.route('/languages')
def get_languages():
    if (not session.get('logged_in')):
        abort(403)
    resp_items = []
    search_result = mongodb.db.languages.find({},{'_id':0}).sort([('name',1),('variant',1)])
    for language in search_result:
        resp_items.append(language)
    return output_json({'Languages' : resp_items}, 200, def_headers)

@virtualrest.route('/<rtype>/<isocode>/<filename>')
def get_localized_file(rtype,isocode,filename):
    #if (not session.get('logged_in')):
    #    abort(403)
    if (rtype not in ['audios','videos','flags','images']):
        abort(404)
    pattern = '^\w{2,20}\.(mp3|ogv|wav)$'
    lang = lang_parse(isocode)
    if ((search(pattern,filename) and lang) is not None):
        griddb = database.Database(MongoClient(host=GRIDFS_HOST, port=GRIDFS_PORT),rtype)
        fs = GridFS(griddb)
        if (fs.exists(filename=lang + '-' + filename)):
            file = fs.get_last_version(lang + '-' + filename)
            mime = mimetypes.guess_type(filename)[0]
            response = virtualrest.response_class(file, direct_passthrough=True, mimetype=mime)
            response.headers.set('Content-Length',file.length)
            return response
    abort(404)

@virtualrest.route('/<rtype>/<filename>')
def get_file(rtype,filename):
    if (not session.get('logged_in')):
        abort(403)
    if (rtype not in ['audios','videos','flags','images', 'thumbs']):
        abort(404)
    griddb = database.Database(MongoClient(host=GRIDFS_HOST, port=GRIDFS_PORT),rtype)
    fs = GridFS(griddb)
    if (fs.exists(filename=filename)):
        file = fs.get_last_version(filename)
        mime = mimetypes.guess_type(filename)[0]
        response = virtualrest.response_class(file, direct_passthrough=True, mimetype=mime)
        response.headers.set('Content-Length',file.length)
        return response
    abort(404)

@virtualrest.route('/translation')
def get_translation():
    resp_items = []
    isocode = lang_parse(request.args.get('lang'))
    if (isocode is None):
        abort(404)
    search_result = mongodb.db.translations.find({'isocode': isocode},{'_id':0})
    for translation in search_result:
        resp_items.append(translation)
    return output_json(resp_items, 200, def_headers)

@virtualrest.route('/object')
def get_object():
    if (not session.get('logged_in')):
        abort(403)
    type = request.args.get('type')
    objid = request.args.get('id')
    dev_uuid = request.args.get('uuid')
    isocode = lang_parse(request.args.get('lang'))
    if (type is not None):
        type = type.lower()
    if (objid and isocode) is None:
        abort(404)
    objid = objid.lower()
    obj_regex = search('^(\w{2,10})$',objid)
    resp_items = []
    ### {id:'000000003'},{'translations':{'$elemMatch':{'isocode': 'pt-br'} },'views':1,'votes':1,'id':1,'_id':0}
    if (type == 'search'):
        search_result = mongodb.db.objects.find(
            {
              'translations.title': { '$regex': objid, '$options': 'i' },
              'translations.isocode': isocode
            },
            {
              'translations':{'$elemMatch':{'isocode': isocode} },
              'views':0,
              'votes':0,
              'audio':0,
              'video':0,
              'id':1,
              '_id':0
            }
        )
        if (search_result.count() == 1 and dev_uuid is not None):
            objid = search_result[0]['id']
            mongodb.db.objects.update_one({'id': objid}, {'$inc': {'views': 1}})
            update_result = mongodb.db.history.update_one({'uuid': dev_uuid}, {'$push' : {'history': objid}}, upsert=True)
        for object in search_result:
            item = {}
            item['id'] = object['id']
            item['text'] = object['translations'][0]['text']
            item['title'] = object['translations'][0]['title']
            #item['votes'] = object['votes']
            #item['views'] = object['views']
            resp_items.append(item)
    else:
        ### {id:'000000003'},{'translations':{'$elemMatch':{'isocode': 'pt-br'} },'views':1,'votes':1,'id':1,'_id':0}
        search_result = mongodb.db.objects.find_one_and_update(
            { 'id': objid, 'translations.isocode': isocode },
            { '$inc': {'views': 1} },
            projection = {
                'translations': {'$elemMatch': {'isocode': isocode} },
                'views': 1,
                'votes': 1,
                'audio': 1,
                'video': 1,
                'id': 1,
                '_id': 0
            },
            return_document = ReturnDocument.AFTER
        )
        if (search_result is not None):
            item = {}
            item['text'] = search_result['translations'][0]['text']
            item['title'] = search_result['translations'][0]['title']
            item['id'] = search_result['id']
            item['votes'] = search_result['votes']
            item['views'] = search_result['views']
            item['audio'] = search_result['translations'][0]['audio']
            item['video'] = search_result['translations'][0]['video']
            resp_items.append(item)
            if (dev_uuid is not None):
                update_result = mongodb.db.history.update_one({'uuid': dev_uuid}, {'$push' : {'history': objid}}, upsert=True)
    return output_json({'Object': resp_items}, 200, def_headers)


@virtualrest.route('/vote')
def set_vote():
    if (not session.get('logged_in')):
        abort(403)
    objid = request.args.get('id')
    votetype = request.args.get('type')
    if ((objid and votetype) is None):
        abort(403)
    objid = objid.lower()
    if (votetype.lower() == 'plus'):
        result = mongodb.db.objects.update_one({'id': objid}, {'$inc': {'votes': 1}})
    elif (votetype.lower() == 'minus'):
        result = mongodb.db.objects.update_one({'id': objid}, {'$inc': {'votes': -1}})
    if (result.matched_count == 1):
        return output_json({'result': 'ok'}, 200, def_headers)
    else:
        return output_json({'result': 'error'}, 200, def_headers)

@virtualrest.route('/suggestions')
def get_suggestions():
    if (not session.get('logged_in')):
        abort(403)
    isocode = lang_parse(request.args.get('lang'))
    if (isocode is None):
        abort(404)
    resp_items = []
    result = mongodb.db.objects.find({},
        {
            'id':1,
            'votes':1,
            'views':1,
            'translations':{'$elemMatch':{'isocode': isocode} },
            '_id':0
        },
        limit = int(result_limit),
        sort = [('votes',-1)]
    )
    for i in result:
        item = {}
        item['id'] = i['id']
        item['votes'] = i['votes']
        item['views'] = i['views']
        try:
            item['title'] = i['translations'][0]['title']
        except KeyError:
            item['title'] = 'No translation available.'
        resp_items.append(item)
    return output_json({'Suggestions': resp_items}, 200, def_headers)

@virtualrest.route('/history')
def get_history():
    if (not session.get('logged_in')):
        abort(403)
    dev_uuid = request.args.get('uuid')
    resp_items = []
    result = mongodb.db.history.find_one({'uuid':dev_uuid},projection={'history':1,'_id':0})
    if (result is None):
        return output_json({'History' : []}, 200, def_headers)
    resp_items = list(reversed(result['history']))[:10]
    return output_json({'History' : resp_items}, 200, def_headers)

@virtualrest.route('/setup')
def set_setup():
    dev_uuid = request.args.get('uuid')
    code = request.args.get('code')
    salt = request.args.get('salt')
    if ((dev_uuid and code and salt) is None):
        abort(403)
    griddb = database.Database(MongoClient(host=GRIDFS_HOST, port=GRIDFS_PORT),'certs')
    fs = GridFS(griddb)
    if (fs.find_one({'filename': 'rsa_1024_priv.pem'})):
        key_string = fs.get_last_version('rsa_1024_priv.pem').read()
        priv = RSA.load_key_string(key_string)
    try:
        ctxt = b64decode(code.replace(' ','+'))
        decrypted_text = priv.private_decrypt(ctxt, RSA.pkcs1_padding)
        hash = hashlib.md5('%s:%s:%s' % (dev_uuid,decrypted_text,salt)).hexdigest()
    except TypeError as e:
        return output_json({'Result' : 'Error: %s' % e}, 200, def_headers)
    find_result = mongodb.db.trusts.find_one({'uuid': dev_uuid},{'_id':0,'timestamp':1})
    if (find_result is not None):
        # Timeout after 600 seconds (10 minutes)
        # After timeout, users are able to setup trustee again
        if (int(find_result['timestamp']) + 600 <= time()):
            update_result = mongodb.db.trusts.update_one(
                {'uuid': dev_uuid},
                {'$set': {'secret': decrypted_text, 'timestamp': int(time())} },
                upsert=True
            )
        else:
            return output_json({'Result' : 'Too early'}, 403, def_headers)
    else:
        update_result = mongodb.db.trusts.update_one(
            {'uuid': dev_uuid},
            {'$set': {'secret': decrypted_text, 'timestamp': int(time())} },
            upsert=True
        )
    session['logged_in'] = True
    return output_json({'Result' : hash}, 200, def_headers)

@virtualrest.route('/verify')
def do_verify():
    dev_uuid = request.args.get('uuid')
    salt = request.args.get('salt')
    if ((dev_uuid and salt) is None):
        abort(403)
    griddb = database.Database(MongoClient(host=GRIDFS_HOST, port=GRIDFS_PORT),'certs')
    fs = GridFS(griddb)
    find_result = mongodb.db.trusts.find_one({'uuid': dev_uuid},{'_id':0,'secret':1})
    if (find_result is None):
        abort(403)
    else:
        hash = hashlib.md5('%s:%s:%s' % (dev_uuid,find_result['secret'],salt)).hexdigest()
        mongodb.db.trusts.update_one(
            {'uuid': dev_uuid},
            {'$set': { 'timestamp': int(time()) } },
            upsert=False
        )
    session['logged_in'] = True
    return output_json({'Result' : hash}, 200, def_headers)

@virtualrest.route('/')
def default_page():
    abort(404)

if __name__ == '__main__':
    with virtualrest.app_context():
        fallback = literal_eval(mongodb.db.configs.find({},{'_id':0,'fallbacks':1})[0]['fallbacks'])
        result_limit = mongodb.db.configs.find({},{'_id':0,'result_limit':1})[0]['result_limit']
    localport = config.getint('MAIN', 'rest_local_port')
    localaddress = config.get('MAIN', 'local_address')
    insecure_session = False
    #virtualrest.run(host=localaddress,port=localport, debug=True)
    http_server = WSGIServer((localaddress, localport), virtualrest)
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        http_server.stop()