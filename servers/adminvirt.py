#!flask/bin/python
# -*- coding: utf-8 -*-
'''
Author: Allan GooD
'''

import gevent
from gevent import monkey
monkey.patch_all()

import pyqrcode
import mimetypes
import ConfigParser
from PIL import Image
from time import time
from re import search
from gridfs import GridFS
from StringIO import StringIO
from colorthief import ColorThief
from bson.errors import InvalidId
from gevent.wsgi import WSGIServer
from bson.json_util import dumps, ObjectId
from flask.ext.pymongo import PyMongo
from flask import Flask, abort, request, session, \
    redirect, url_for, render_template, flash
from pymongo import database, MongoClient, ReturnDocument

config = ConfigParser.SafeConfigParser({
    'host': '127.0.0.1',
    'port': 27017,
    'dbname': 'virtualrest',
    'user': None,
    'passwd': None,
    'replicaset': None,
    'debug': False,
})

config.read('./virtrest.cfg')

mediatypes = {'thumb': {'db': 'thumbs', 'ext': '.png'}, 'video': {'db': 'videos', 'ext': '.ogv'}, 'audio': {'db': 'audios', 'ext': '.mp3'}}

virtualrest = Flask(__name__)

virtualrest.config['SECRET_KEY'] = 'KKH887687very*&&$$#@secret___)(*)(*8098___keyBLABLABS765765765';

MONGO_HOST = config.get('MONGODB', 'host')
MONGO_PORT = config.getint('MONGODB', 'port')
MONGO_DBNAME = config.get('MONGODB', 'dbname')
MONGO_USER = config.get('MONGODB', 'user')
MONGO_PASSWD = config.get('MONGODB', 'passwd')
MONGO_REPLICA_SET = config.get('MONGODB', 'replicaset')
GRIDFS_HOST = config.get('GRIDFS', 'host')
GRIDFS_PORT = config.getint('GRIDFS', 'port')

virtualrest.config['CONNECT'] = False
virtualrest.config['MONGO_HOST'] = MONGO_HOST
virtualrest.config['MONGO_PORT'] = MONGO_PORT
virtualrest.config['MONGO_DBNAME'] = MONGO_DBNAME
virtualrest.config['MONGO_USERNAME'] = MONGO_USER
virtualrest.config['MONGO_PASSWORD'] = MONGO_PASSWD
virtualrest.config['MONGO_REPLICA_SET'] = MONGO_REPLICA_SET

virtualrest.jinja_env.trim_blocks = True
virtualrest.jinja_env.lstrip_blocks = True

mongodb = PyMongo(virtualrest)

# Code is Language Code - ISO 639-1 (EN, FR, ES, PT,  etc)
# Locale is Counyry Code - ISO 3166-1 (US,CA, AR, etc)
# Code + Locale = en-us / en-ca / en-uk / pt-br / etc
Language_JSON = { "name": "", "code": "", "locale": "", "variant": "" }
Object_JSON = {
    "id": "",
    "views": 0,
    "votes": 0,
    "audio": False,
    "video": False,
    "translations": []
}

Translation_JSON = {
    "isocode": "",
    "START_TAB": {
        "TAB_TITLE": "Tab Start",
        "TITLE": "Tab Start Title",
        "AVATAR_HEADER": "Avatar header",
        "AVATAR_BODY": "Avatar Body",
        "TEXT_HEADER": "Text Header",
        "TEXT_BODY": "Text Body"
    },
    "SCAN_TAB" : {
        "TAB_TITLE": "Tab Scan Title",
        "TITLE": "Scan Title",
        "BODY": "Body Text",
        "BUTTON_SCAN": "Button text",
        "UNKNOW_CODE": "Unknow code",
        "TRY_AGAIN": "Please, try again",
        "SEARCH": "Search"
    },
    "SEARCH_RESULT": {
        "TITLE": "Object Result",
        "VIEWS": "Views",
        "VOTES": "Votes"
    },
    "SUGGESTION_TAB" : {
        "TAB_TITLE": "Suggestions Tab Title",
        "TITLE": "Suggestions Title"
    },
    "HISTORY_TAB" : {
        "TAB_TITLE": "History Tab Title",
        "TITLE": "History Title"
    },
    "ABOUT_TAB" : {
        "TAB_TITLE": "About Tab Title",
        "TITLE": "About Title",
        "BODY": "Body text accept HTML tags like <a href='#'>links</a>"
    },
    "LANGUAGE_TAB" : {
        "TAB_TITLE": "Lanuguage Tab Title",
        "TITLE": "Language Title",
        "LANGUAGE": "Language",
        "VARIANT": "Variant"
    },
    "MAIN" : {
        "SERVER_DETECTED": "Server detected",
        "NAVIGATION": "Navigation",
        "CONFIGURATIONS": "Configurations",
        "SETUP": "Setup",
        "MENU": "Menu",
        "PULL_TO_REFRESH": "Pull to refresh",
        "CONFIRM": "Confirm",
        "CANCEL": "Cancel",
        "OK": "Ok",
        "EXIT": "Exit"
    }
}

def to_dict(dictionary):
    resp = {}
    for i in dictionary:
        resp[i] = dictionary[i]
    return resp

def genkeypair():
    from M2Crypto import RSA, BIO
    new_key = RSA.gen_key(1024,65537)
    memory = BIO.MemoryBuffer()
    new_key.save_key_bio(memory, cipher=None)
    private_key = memory.getvalue()
    new_key.save_pub_key_bio(memory)
    pub_key = memory.getvalue()
    certs = {'privkey': private_key, 'pubkey': pub_key}
    return certs

@virtualrest.route('/')
def index():
    if (not session.get('logged_in')):
        return redirect(url_for('login'))
    return render_template('layout.html')

@virtualrest.route('/login', methods=['GET','POST'])
def login():
    error = None
    if (request.method == 'POST'):
        if (request.form['username'].lower() == 'admin' and request.form['passwd'] == 'admin'):
            session['logged_in'] = True
            session['username'] = request.form['username'].lower()
            flash('Logged in')
            return redirect(url_for('index'))
        else:
            flash('Username or password incorrect.')
    return render_template('login.html')

@virtualrest.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    flash('Logged out')
    return redirect(url_for('login'))

@virtualrest.route('/languages')
def languages():
    if (not session.get('logged_in')):
        return redirect(url_for('login'))
    search_result = mongodb.db.languages.find({},sort=([('name',1),('variant',1)]))
    return render_template('languages.html',entries=search_result)

@virtualrest.route('/change_languages',methods=['POST'])
def change_language():
    if (not session.get('logged_in')):
        return redirect(url_for('login'))
    if (request.form['action'] == 'delete'):
        result = mongodb.db.languages.delete_one({'_id': ObjectId(request.form['id'])})
        flash('Language deleted!')
    elif (request.form['action'] == 'change'):
        changes = to_dict(request.form)
        del(changes['id'])
        del(changes['action'])
        result = mongodb.db.languages.update_one (
                { '_id': ObjectId(request.form['id'])},
                { '$set': changes }
            )
        flash('Changes saved!')
    return redirect(url_for('languages'))

@virtualrest.route('/add_language', methods=['POST'])
def add_language():
    if (not session.get('logged_in')):
        return redirect(url_for('login'))
    result = to_dict(request.form)
    mongodb.db.languages.insert_one(result)
    flash('Language added!')
    return redirect(url_for('languages'))

@virtualrest.route('/translations/<code>-<locale>')
def translations(code,locale):
    if (not session.get('logged_in')):
        return redirect(url_for('login'))
    search_result = mongodb.db.translations.find_one({'isocode': code + '-' + locale},{'_id': 0});
    if (search_result is None):
        Translation_JSON['isocode'] = code + '-' + locale
        mongodb.db.translations.insert_one(Translation_JSON)
        return redirect(url_for('translations', code=code,locale=locale))
    return render_template('show_translations.html',translations=search_result)

@virtualrest.route('/change_translation/<isocode>/<tab>',methods=['POST'])
def change_translation(isocode,tab):
    if (not session.get('logged_in')):
        return redirect(url_for('login'))
    changes = to_dict(request.form)
    result = mongodb.db.translations.update_one(
        { 'isocode': isocode},
        { '$set': { tab: changes } }
    )
    flash('Changes saved!')
    return redirect(url_for('translations',_anchor='tab-'+tab, code=isocode[:2],locale=isocode[3:]))

@virtualrest.route('/main_config', methods=['GET','POST'])
def main_config():
    filenames = {'pubkey': 'rsa_1024_pub.pem', 'privkey': 'rsa_1024_priv.pem'}
    certs = None
    if (not session.get('logged_in')):
        return redirect(url_for('login'))
    if request.method == "POST":
        changes = to_dict(request.form)
        if (changes['action'] == 'configurations'):
            del(changes['action'])
            mongodb.db.configs.update_one({'name': changes['name']}, {'$set': changes})
        elif (changes['action'] == 'genkeys'):
            certs = genkeypair()
            gridfsdb = database.Database(MongoClient(host=GRIDFS_HOST, port=GRIDFS_PORT),'certs')
            fs = GridFS(gridfsdb)
            for key in ['privkey', 'pubkey']:
                oldfile = fs.find_one({'filename': filenames[key]})
                if (oldfile is not None):
                    fs.delete(oldfile._id)
                fs.put(certs[key].copy(), content_type="text/plain", filename=filenames[key])
                print('Gravado chave: %s' % key)
                print(certs[key])

    result = mongodb.db.configs.find({},{'_id':0})
    gridfsdb = database.Database(MongoClient(host=GRIDFS_HOST, port=GRIDFS_PORT),'images')
    fs = GridFS(gridfsdb)
    avatar = fs.exists(filename='avatar.png')
    background = fs.exists(filename='background.png')
    logo = fs.exists(filename='logo.png')
    imgresult = {'avatar': avatar, 'background': background, 'logo': logo}

    if (certs is None):
        gridfsdb = database.Database(MongoClient(host=GRIDFS_HOST, port=GRIDFS_PORT),'certs')
        fs = GridFS(gridfsdb)
        if (fs.exists(filename=filenames['pubkey'])):
            file = fs.get_last_version(filenames['pubkey'])
            pubkey = file.read()
            certs = {'pubkey': pubkey}

    return render_template('main_config.html',images=imgresult,configs=result,certs=certs)

@virtualrest.route('/upload_file/<filename>', methods=['POST'])
def upload_file(filename):
    if (not session.get('logged_in')):
        return redirect(url_for('login'))
    if (filename not in ['avatar','background','logo']):
        abort(403)
    sizes = {'avatar': (64,64), 'background': (400,300), 'logo': (320,240)}
    gridfsdb = database.Database(MongoClient(host=GRIDFS_HOST, port=GRIDFS_PORT),'images')
    fs = GridFS(gridfsdb)
    output = StringIO()
    file = request.files['file']
    im = Image.open(file)
    if (filename == 'background'):
        color_thief = ColorThief(file)
        pallete = color_thief.get_palette(color_count=2)
        result_color, parcial_color = '',''
        for t in pallete:
            for c in t:
                parcial_color += hex(c).lstrip('0x')
            result_color += '#' + parcial_color + ','
            parcial_color = ''
        mongodb.db.configs.update({},{'$set': {'bgcolor': result_color[:-1]}})
    im.thumbnail(sizes[filename], Image.ANTIALIAS)
    im.save(output, format="PNG")
    contents = output.getvalue()
    output.close()
    oldfile = fs.find_one({'filename': filename + '.png'})
    if (oldfile is not None):
        fs.delete(oldfile._id)
    oid = fs.put(contents, content_type=file.content_type, filename=filename + '.png')
    del(contents)
    flash('File Uploaded!')
    return redirect(url_for('main_config', _anchor='tab-images'))

@virtualrest.route('/setupcode')
def setupcore():
    if (not session.get('logged_in')):
        return redirect(url_for('login'))
    gridfsdb = database.Database(MongoClient(host=GRIDFS_HOST, port=GRIDFS_PORT),'certs')
    fs = GridFS(gridfsdb)
    filename = 'rsa_1024_pub.pem'
    if (fs.exists(filename=filename)):
        file = fs.get_last_version(filename)
        pubkey = file.read().replace('\n','').replace('-----BEGIN PUBLIC KEY-----','').replace('-----END PUBLIC KEY-----','')
    server_address = mongodb.db.configs.find_one({},{'_id':0,'server_address':1})['server_address']
    qrdata = pyqrcode.create(server_address + '|' + pubkey, mode='binary')
    output = StringIO()
    qrdata.svg(output, scale=6)
    contents = output.getvalue()
    output.close();
    response = virtualrest.response_class(contents, direct_passthrough=True, mimetype='image/svg+xml')
    response.headers.set('Content-Length',len(contents))
    return response

@virtualrest.route('/qrcode/<data>')
def qrcode(data):
    if (not session.get('logged_in')):
        return redirect(url_for('login'))
    qrdata = pyqrcode.create(data[:-4], )
    output = StringIO()
    qrdata.svg(output, scale=4)
    contents = output.getvalue()
    output.close();
    response = virtualrest.response_class(contents, direct_passthrough=True, mimetype='image/svg+xml')
    response.headers.set('Content-Length',len(contents))
    return response

@virtualrest.route('/objects')
def objects():
    if (not session.get('logged_in')):
        return redirect(url_for('login'))
    ### {id:'000000003'},{'translations':{'$elemMatch':{'isocode': 'pt-br'} },'views':1,'votes':1,'id':1,'_id':0}
    search_result = mongodb.db.objects.find({},{
        '_id': 1,
        'id': 1,
        'translations.title': 1,
        'translations.audio': 1,
        'translations.video': 1,
        'translations.isocode': 1
        },
        sort = [ ('id',1) ]
    )
    objects = []
    for t in search_result:
        objects.append(t)
    return render_template('objects.html', objects=objects)

@virtualrest.route('/get_object/<id>')
def get_object(id):
    if (not session.get('logged_in')):
        return redirect(url_for('login'))
    ### {id:'000000003'},{'translations':{'$elemMatch':{'isocode': 'pt-br'} },'views':1,'votes':1,'id':1,'_id':0}
    search_result = mongodb.db.objects.find_one({'id': id},{'_id':1,'id':1,'translations':1})
    if (search_result is None):
        abort(404)
    search_langs = mongodb.db.languages.find(
        {},
        projection = {
            'name': 1,
            'variant': 1,
            'code': 1,
            'locale': 1,
            '_id': 0
        },
        sort = ( [('code',1), ('locale',1)] )
    )
    langs = []
    for t in search_langs:
        langs.append(t)
    return render_template('object_detail.html', object=search_result, langs=langs)

@virtualrest.route('/change_object', methods=['POST'])
def change_object():
    if (not session.get('logged_in')):
        return redirect(url_for('login'))

    if (request.form['action'] == 'del_translation'):
        flash('Translation deleted!')
        result = mongodb.db.objects.find_one_and_update(
            { '_id': ObjectId(request.form['_id']) },
            { '$pull': {'translations': {'isocode': request.form['isocode']} } },
            projection = {'id': 1}
        )
        id = result['id']

    elif (request.form['action'] == 'add_translation'):
        flash('Translation Added!')
        result = mongodb.db.objects.find_one_and_update(
            { '_id': ObjectId(request.form['_id']) },
            { '$addToSet': {'translations': {
                'isocode': request.form['isocode'],
                'title': request.form['title'],
                'text': request.form['text'],
                'audio': False,
                'video': False
                }
            } },
            projection = {'id': 1},
            upsert = True
        )
        id = result['id']

    elif (request.form['action'] == 'change_translation'):
        flash('Translation Changed!')
        result = mongodb.db.objects.find_one_and_update(
            {
                '_id': ObjectId(request.form['_id']),
                'translations': { '$elemMatch': {'isocode': request.form['isocode'] } }
            },{
                '$set': {
                    'translations.$.isocode': request.form['isocode'],
                    'translations.$.title': request.form['title'],
                    'translations.$.text': request.form['text'],
                }
            },
            projection = {'id': 1},
            upsert = False
        )
        id = result['id']

    elif (request.form['action'] == 'del_object'):
        result = mongodb.db.objects.find_one_and_delete({ '_id': ObjectId(request.form['_id']) }, projection={'_id':1, 'id':1})
        if (result is not None):
            for rtype in mediatypes.keys():
                gridfsdb = database.Database(MongoClient(host=GRIDFS_HOST, port=GRIDFS_PORT), mediatypes[rtype]['db'])
                fs = GridFS(gridfsdb)
                for objfile in fs.find({'filename': result['id'] + mediatypes[rtype]['ext']}):
                    print('delete: %s in %s' % (objfile.filename,mediatypes[rtype]['db']))
                    fs.delete(objfile._id)
            flash('Object deleted!')
        return redirect(url_for('objects'))

    elif (request.form['action'] == 'add_object'):
        Object_JSON['id'] = request.form['id']
        mongodb.db.objects.insert_one(Object_JSON.copy())
        flash('Object added!')
        return redirect(url_for('objects'))

    return redirect(url_for('get_object',id=id))

@virtualrest.route('/upload_obj_img/<filename>', methods=['POST'])
def upload_obj_img(filename):
    if (not session.get('logged_in')):
        return redirect(url_for('login'))
    if (search('\d{5,10}', filename) is None):
        abort(403)
    sizes = {'images': (320,240), 'thumbs': (64,64)}
    for filetype in sizes.keys():
        gridfsdb = database.Database(MongoClient(host=GRIDFS_HOST, port=GRIDFS_PORT), filetype)
        fs = GridFS(gridfsdb)
        output = StringIO()
        file = request.files['file']
        im = Image.open(file)
        im.thumbnail(sizes[filetype], Image.ANTIALIAS)
        im.save(output, format="PNG")
        contents = output.getvalue()
        output.close()
        oldfile = fs.find_one({'filename': filename + '.png'})
        if (oldfile is not None):
            fs.delete(oldfile._id)
        fs.put(contents, content_type=file.content_type, filename=filename + '.png')
        del(contents)
    flash('File Uploaded!')
    return redirect(url_for('objects'))

@virtualrest.route('/upload_obj_media/<mediatype>/<filename>', methods=['POST'])
def upload_obj_media(mediatype,filename):
    if (not session.get('logged_in')):
        return redirect(url_for('login'))
    file = request.files['file']
    if (file.filename[-4:] not in ['.mp3','.ogv']):
        flash('Filetype not allowed')
        return redirect(url_for('objects'))
    if (mediatype not in ['audio','video']):
        abort(404)
    isocode = request.form['isocode']
    mongodb.db.objects.update_one(
        { 'id': filename, 'translations.isocode': isocode },
        { '$set': { 'translations.$.' + mediatype: True } }
    )
    gridfsdb = database.Database(MongoClient(host=GRIDFS_HOST, port=GRIDFS_PORT),mediatypes[mediatype]['db'])
    fs = GridFS(gridfsdb)
    oldfile = fs.find_one({'filename': isocode + '-' + filename + mediatypes[mediatype]['ext']})
    if (oldfile is not None):
        fs.delete(oldfile._id)
    oid = fs.put(file, content_type=file.content_type, filename=isocode + '-' + filename + mediatypes[mediatype]['ext'])
    file.close()
    del(file)
    return redirect(url_for('objects'))

@virtualrest.route('/remove_media/<mediatype>/<isocode>/<id>')
def remove_media(mediatype,isocode,id):
    if (not session.get('logged_in')):
        return redirect(url_for('login'))

    mongodb.db.objects.update_one(
        { 'id': id, 'translations.isocode': isocode },
        { '$set': { 'translations.$.' + mediatype: False } }
    )
    gridfsdb = database.Database(MongoClient(host=GRIDFS_HOST, port=GRIDFS_PORT),mediatypes[mediatype]['db'])
    fs = GridFS(gridfsdb)
    file = fs.find_one({'filename': isocode + '-' + id + mediatypes[mediatype]['ext']})
    if (file is not None):
        fs.delete(file._id)
    return redirect(url_for('get_object',id=id))

@virtualrest.route('/<rtype>/<path:filename>')
def get_file(rtype,filename):
    if (not session.get('logged_in')):
        return redirect(url_for('login'))
    if (rtype not in ['audios','videos','flags','images','thumbs']):
        abort(404)
    gridfsdb = database.Database(MongoClient(host=GRIDFS_HOST, port=GRIDFS_PORT),rtype)
    fs = GridFS(gridfsdb)
    if (fs.exists(filename=filename)):
        file = fs.get_last_version(filename)
        mime = mimetypes.guess_type(filename)[0]
        response = virtualrest.response_class(file, direct_passthrough=True, mimetype=mime)
        response.headers.set('Content-Length',file.length)
        response.headers.set('Cache-Control', 'no-cache, no-store, must-revalidate')
        response.headers.set('Pragma', 'no-cache')
        response.headers.set('Expires', '0')
        return response
    abort(404)

if __name__ == '__main__':
    localport = config.getint('MAIN', 'admin_local_port')
    localaddress = config.get('MAIN', 'local_address')
    #virtualrest.run(host=localaddress,port=localport, debug=True)
    http_server = WSGIServer((localaddress, localport), virtualrest)
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        http_server.stop()
