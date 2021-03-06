#!pypy/bin/python
# -*- coding: utf-8 -*-

import gevent
from gevent import monkey
monkey.patch_all()

import hashlib
import pyqrcode
import mimetypes
import ConfigParser
from PIL import Image
from time import time
from re import search
from os import urandom
from gridfs import GridFS
from StringIO import StringIO
from colorthief import ColorThief
from bson.errors import InvalidId
from gevent.wsgi import WSGIServer
from bson.json_util import dumps, ObjectId
from flask.ext.pymongo import PyMongo
from flask import Flask, abort, request, session, \
    redirect, url_for, render_template, flash, send_from_directory
from pymongo import database, MongoClient, ReturnDocument

config = ConfigParser.SafeConfigParser({
    'host': '127.0.0.1',
    'port': 27017,
    'dbname': 'virtualrest',
    'user': None,
    'passwd': None,
    'replicaset': None,
    'debug': False,
    'local_address': '0.0.0.0',
    'local_port': 8080
})

config.read('./adminvirt.cfg')

mediatypes = {
    'images': {'db': 'images', 'ext': '.png'},
    'thumbs': {'db': 'thumbs', 'ext': '.png'},
    'videos': {'db': 'videos', 'ext': '.mp4'},
    'audios': {'db': 'audios', 'ext': '.mp3'}
}

virtualrest = Flask(__name__)

virtualrest.config['SECRET_KEY'] = urandom(64)

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

# Users rights
rights = ['all', 'main_config', 'translations', 'languages', 'objects']

# Code is Language Code - ISO 639-1 (EN, FR, ES, PT,  etc)
# Locale is Counyry Code - ISO 3166-1 (US,CA, AR, etc)
# Code + Locale = en-us / en-ca / en-uk / pt-br / etc
Language_JSON = { "name": "", "code": "", "locale": "", "variant": "" }
Object_JSON = {
    "id": "",
    "views": 0,
    "votes": 0,
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

# To Dict
def to_dict(dictionary):
    resp = {}
    for i in dictionary:
        resp[i] = dictionary[i]
    return resp

def copy_cursor(cursor):
    resp = []
    for i in cursor:
        resp.append(i)
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

def auth_user(username, password):
    return_auth = False
    password = hashlib.md5(password).hexdigest()
    user_credentials = mongodb.db.users.find_one({'username': username.lower()}, projection={'_id': 0})
    rights = {}
    if (user_credentials is not None and password == user_credentials['password']):
        for r in mongodb.db.roles.find({'rolename': {'$in': user_credentials['roles']}}, projection={'_id':0, 'rights':1}):
            rights.update(r['rights'])
        return_auth = {'username': username.lower(), 'fullname': user_credentials['fullname'], 'rights': rights}
    else:
        return False
    return return_auth

def check_access(location):
    rights = session.get('rights')
    if ('all' in rights.keys()):
        return 'rw'
    if (location in rights.keys()):
        return rights[location]
    return abort(403)

def del_files_of_object(objid, types=['all']):
    allowed_types = ['images','thumbs','videos','audios']
    if (types == ['all']):
        types = allowed_types
    for filetype in types:
        if filetype in allowed_types:
            dbname = mediatypes[filetype]['db']
            ext = mediatypes[filetype]['ext']
            gridfsdb = database.Database(MongoClient(host=GRIDFS_HOST, port=GRIDFS_PORT), dbname)
            fs = GridFS(gridfsdb)
            if (filetype in ['audios','videos']):
                languages = mongodb.db.languages.find({}, {'_id': 0, 'code': 1, 'locale': 1})
                for language in languages:
                    isocode = ','.join([language['code'],language['locale']])
                    fileid = fs.find_one({'filename': isocode + objid + ext})
                    if (fileid is not None):
                        fs.delete(fileid._id)
            else:
                fileid = fs.find_one({'filename': objid + ext})
                if (fileid is not None):
                    fs.delete(fileid._id)
        else:
            return False

def del_obj_media(objid, isocode, mediatype):
    if (mediatype not in ['audios','videos']):
        return False

    gridfsdb = database.Database(MongoClient(host=GRIDFS_HOST, port=GRIDFS_PORT),mediatypes[mediatype]['db'])
    fs = GridFS(gridfsdb)

    mongodb.db.objects.update_one(
        { 'id': objid, 'translations.isocode': isocode },
        { '$set': { 'translations.$.audio': False } }
    )
    oldfile = fs.find_one({'filename': isocode + '-' + objid + mediatypes[mediatype]['ext']})
    if (oldfile is not None):
        fs.delete(oldfile._id)
    return True

def set_obj_media(objid, isocode, mediatype, file):
    if (file.filename[-4:] not in ['.mp3','.mp4']):
        return False
    if (mediatype not in ['audios','videos']):
        return False

    gridfsdb = database.Database(MongoClient(host=GRIDFS_HOST, port=GRIDFS_PORT),mediatypes[mediatype]['db'])
    fs = GridFS(gridfsdb)

    mongodb.db.objects.update_one(
        { 'id': objid, 'translations.isocode': isocode },
        { '$set': { 'translations.$.' + mediatype: True } }
    )
    oldfile = fs.find_one({'filename': isocode + '-' + objid + mediatypes[mediatype]['ext']})
    if (oldfile is not None):
        fs.delete(oldfile._id)
    oid = fs.put(file, content_type=file.content_type, filename=isocode + '-' + objid + mediatypes[mediatype]['ext'])

    return True

def create_obj_img_intodb(imagefile,objid):
    sizes = {'images': (320,240), 'thumbs': (64,64)}
    for filetype in sizes.keys():
        output = StringIO()
        im = Image.open(imagefile)
        im.thumbnail(sizes[filetype], Image.ANTIALIAS)
        im.save(output, format="PNG")
        contents = output.getvalue()
        output.close()
        gridfsdb = database.Database(MongoClient(host=GRIDFS_HOST, port=GRIDFS_PORT), filetype)
        fs = GridFS(gridfsdb)
        del_files_of_object(objid, types=[filetype])
        fs.put(contents, content_type=imagefile.content_type, filename = objid + '.png')
        del(contents)

@virtualrest.route('/')
def index():
    if (not session.get('logged_in')):
        return redirect(url_for('login'))
    languages = copy_cursor(mongodb.db.languages.find({}, sort=([('name',1),('variant',1)])))
    return render_template('layout.html',languages=languages)

@virtualrest.route('/login', methods=['GET','POST'])
def login():
    if (request.method == 'POST'):
        auth_return = auth_user(request.form['username'],request.form['passwd'])
        if (auth_return):
            session['logged_in'] = True
            session['user'] = {'username': auth_return['username'], 'fullname': auth_return['fullname']}
            session['rights'] = auth_return['rights']
            return redirect(url_for('index'))
        else:
            flash('Invalid Username or Password','danger')
    return render_template('login.html')

@virtualrest.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    return redirect(url_for('login'))

@virtualrest.route('/users', methods = ['GET', 'POST'] )
def users():
    if (not session.get('logged_in')):
        return redirect(url_for('login'))
    check_access('users')
    if (request.method == 'POST'):
        users_to_remove = request.form.getlist('user')
        roles_to_remove = request.form.getlist('role')
        if (len(users_to_remove) > 0):
            mongodb.db.users.delete_many({'username': {'$in': users_to_remove} })
    users = copy_cursor( mongodb.db.users.find({}, sort=([('username',1)]) ) )
    return render_template('users.html', users=users)

@virtualrest.route('/edituser/<userid>', methods = ['GET','POST'])
def edituser(userid):
    if (not session.get('logged_in')):
        return redirect(url_for('login'))
    if (check_access('users') != 'rw'):
        abort(403)

    if (request.method == 'POST'):
        if (len(request.form['password']) > 5):
            user_json = {
                'username': request.form['username'],
                'fullname': request.form['fullname'],
                'prefs': [],
                'password': hashlib.md5(request.form['password']).hexdigest(),
                'roles': request.form.getlist('roles')
            }
        else:
            user_json = {
                'username': request.form['username'],
                'fullname': request.form['fullname'],
                'prefs': [],
                'roles': request.form.getlist('roles')
            }

        result = mongodb.db.users.update_one( {'_id': ObjectId(request.form['_id'])}, {'$set': user_json } ).raw_result
        if ( result['ok'] > 0):
            flash(u'Changes saved!', 'success')
        else:
            flash(u'Changes not saved!', 'danger')
        return redirect(url_for('users'))

    user = mongodb.db.users.find_one({'_id': ObjectId(userid)}, {'password': 0})
    roles = copy_cursor( mongodb.db.roles.find({}, sort=([('rolename',1)]) ) )
    return render_template('user_detail.html', user=user, roles=roles)

@virtualrest.route('/newuser/<userid>', methods = ['GET','POST'])
def newuser(userid):
    if (not session.get('logged_in')):
        return redirect(url_for('login'))
    if (check_access('users') != 'rw'):
        abort(403)

    if (request.method == 'POST'):
       user_json = {
            'username': request.form['username'],
            'fullname': request.form['fullname'],
            'prefs': [],
            'password': hashlib.md5(request.form['password']).hexdigest(),
            'roles': request.form.getlist('roles')
        }

       result = mongodb.db.users.update_one( {'username': request.form['username']}, {'$set': user_json }, upsert = True ).raw_result
       if ( result['ok'] > 0):
           flash(u'User created!', 'success')
       else:
           flash(u'User creation failed!', 'danger')
    if (len(userid) != 12):
        user = {'username': '', 'fullname': '', 'roles': []}
    else:
        user = mongodb.db.users.find_one({'_id': ObjectId(userid)}, {'password': 0})
    roles = copy_cursor( mongodb.db.roles.find({}, sort=([('rolename',1)]) ) )
    user['username'] = 'newuser'
    return render_template('user_detail.html', user=user, roles=roles)


@virtualrest.route('/deluser/<userid>', methods = ['GET','POST'])
def deluser(userid):
    if (not session.get('logged_in')):
        return redirect(url_for('login'))
    if (check_access('users') != 'rw'):
        abort(403)
    mongodb.db.users.delete_one({'_id': ObjectId(userid)})
    return redirect(url_for('users'))

@virtualrest.route('/roles', methods = ['GET', 'POST'] )
def roles():
    if (not session.get('logged_in')):
        return redirect(url_for('login'))
    check_access('users')
    if (request.method == 'POST'):
        users_to_remove = request.form.getlist('user')
        roles_to_remove = request.form.getlist('role')
        if (len(roles_to_remove) > 0):
            mongodb.db.roles.delete_one({'rolename': {'$in': roles_to_remove} })
    users = copy_cursor( mongodb.db.users.find({}, sort=([('username',1)]) ) )
    roles = copy_cursor( mongodb.db.roles.find({}, sort=([('rolename',1)]) ) )
    return render_template('roles.html', users=users, roles=roles)

@virtualrest.route('/newrole/<roleid>', methods = ['GET','POST'])
def newrole(roleid):
    if (not session.get('logged_in')):
        return redirect(url_for('login'))
    if (check_access('users') != 'rw'):
        abort(403)

    if (request.method == 'POST'):
       role_json = {
            'rolename': request.form['rolename'],
            'description': request.form['description'],
            'rights': {}
        }

       for right in rights:
           role_json['rights'][right] = request.form[right]

       result = mongodb.db.roles.update_one( {'rolename': request.form['rolename']}, {'$set': role_json }, upsert = True ).raw_result
       if ( result['ok'] > 0):
           flash(u'Role created!', 'success')
       else:
           flash(u'Role creation failed!', 'danger')
    if (len(roleid) != 12):
        role = {'rolename': '', 'description': '', 'rights': {}}
    else:
        role = mongodb.db.roles.find_one({'_id': ObjectId(roleid)})
    role['rolename'] = 'newrole'
    return render_template('role_details.html', role=role, rights=rights)

@virtualrest.route('/delrole/<roleid>', methods = ['GET','POST'])
def delrole(roleid):
    if (not session.get('logged_in')):
        return redirect(url_for('login'))
    if (check_access('users') != 'rw'):
        abort(403)
    mongodb.db.roles.delete_one({'_id': ObjectId(roleid)})
    return redirect(url_for('roles'))

@virtualrest.route('/editrole/<roleid>', methods = ['GET','POST'])
def editrole(roleid):
    if (not session.get('logged_in')):
        return redirect(url_for('login'))
    if (check_access('users') != 'rw'):
        abort(403)

    if (request.method == 'POST'):
        role_json = {
            'rolename': request.form['rolename'],
            'description': request.form['description'],
            'rights': {}
        }
        for right in rights:
            role_json['rights'][right] = request.form[right]

        result = mongodb.db.roles.update_one( {'_id': ObjectId(request.form['_id'])}, {'$set': role_json } ).raw_result
        if ( result['ok'] > 0):
            flash(u'Changes saved!', 'success')
        else:
            flash(u'Changes not saved!', 'danger')

    role = mongodb.db.roles.find_one({'_id': ObjectId(roleid)})
    return render_template('role_details.html', role=role, rights=rights)


@virtualrest.route('/languages')
def languages():
    if (not session.get('logged_in')):
        return redirect(url_for('login'))
    access = check_access('languages')
    search_result = copy_cursor(mongodb.db.languages.find({}, sort=([('name',1),('variant',1)])))
    isocountries = copy_cursor(mongodb.db.isocountries.find({}, {'_id': 0, 'name': 1, 'alpha2':1}, sort=([('name',1)])))
    isolanguages = copy_cursor(mongodb.db.isolanguages.find({}, {'_id': 0}, sort=([('English',1)])))
    return render_template('languages.html', access=access, languages=search_result, isocountries=isocountries, isolanguages=isolanguages)

@virtualrest.route('/change_languages', methods = ['POST'])
def change_language():
    if (not session.get('logged_in')):
        return redirect(url_for('login'))
    if (check_access('languages') != 'rw'):
        abort(403)

    changes = to_dict(request.form)
    del(changes['_id'])
    result = mongodb.db.languages.update_one (
            { '_id': ObjectId(request.form['_id'])},
            { '$set': changes }
        )
    return redirect(url_for('languages'))

@virtualrest.route('/del_language/<_id>',methods=['GET'])
def del_language(_id):
    if (not session.get('logged_in')):
        return redirect(url_for('login'))
    if (check_access('languages') != 'rw'):
        abort(403)

    result = mongodb.db.languages.delete_one({'_id': ObjectId(_id)})
    return redirect(url_for('languages'))

@virtualrest.route('/add_language', methods=['POST'])
def add_language():
    if (not session.get('logged_in')):
        return redirect(url_for('login'))
    if (check_access('languages') != 'rw'):
        abort(403)

    result = to_dict(request.form)
    mongodb.db.languages.insert_one(result)
    return redirect(url_for('languages'))

@virtualrest.route('/translations/<code>-<locale>')
def translations(code,locale):
    if (not session.get('logged_in')):
        return redirect(url_for('login'))
    access = check_access('translations')

    search_result = mongodb.db.translations.find_one({'isocode': code + '-' + locale},{'_id': 0});
    configs = copy_cursor(mongodb.db.configs.find({},{'_id':0, 'bgcolor': 1, 'header_color': 1, 'font_color': 1}))
    if (search_result is None):
        Translation_JSON['isocode'] = code + '-' + locale
        mongodb.db.translations.insert_one(Translation_JSON)
        return redirect(url_for('translations', code=code,locale=locale))
    languages = copy_cursor(mongodb.db.languages.find({}, sort=([('name',1),('variant',1)])))
    return render_template('show_translations.html', access=access, translations=search_result, configs=configs, languages=languages)

@virtualrest.route('/change_translation/<isocode>/<tab>',methods=['POST'])
def change_translation(isocode,tab):
    if (not session.get('logged_in')):
        return redirect(url_for('login'))
    if (check_access('translations') != 'rw'):
        abort(403)

    changes = to_dict(request.form)
    if ('files' in changes):
        del(changes['files'])
    result = mongodb.db.translations.update_one(
        { 'isocode': isocode},
        { '$set': { tab: changes } }
    )
    return redirect(url_for('translations',_anchor='tab-'+tab, code=isocode[:2],locale=isocode[3:]))

@virtualrest.route('/main_config', methods=['GET','POST'])
def main_config():
    if (not session.get('logged_in')):
        return redirect(url_for('login'))
    access = check_access('main_config')
    if (request.method == 'POST' and access != 'rw'):
        abort(403)

    filenames = {'pubkey': 'rsa_1024_pub.pem', 'privkey': 'rsa_1024_priv.pem'}
    certs = None
    if (request.method == 'POST'):
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
    languages = copy_cursor(mongodb.db.languages.find({}, sort=([('name',1),('variant',1)])))
    return render_template('main_config.html', access=access, images=imgresult,configs=result,certs=certs,languages=languages)

@virtualrest.route('/upload_file/<filename>', methods=['POST'])
def upload_file(filename):
    if (not session.get('logged_in')):
        return redirect(url_for('login'))
    check_access('main_config')

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
    return redirect(url_for('main_config'))

@virtualrest.route('/setupcode')
def setupcode():
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
    size = int(request.args.get('size',8))
    qrdata = pyqrcode.create(data[:-4], )
    output = StringIO()
    qrdata.svg(output, scale=size)
    contents = output.getvalue()
    output.close();
    response = virtualrest.response_class(contents, direct_passthrough=True, mimetype='image/svg+xml')
    response.headers.set('Content-Length',len(contents))
    return response

@virtualrest.route('/export_list')
def export_list():
    if (not session.get('logged_in')):
        return redirect(url_for('login'))
    check_access('objects')
    objects = copy_cursor(mongodb.db.objects.find({},
        {
            '_id': 0,
            'id': 1,
            'translations.title': 1,
        },
        sort = [ ('id',1) ]
    ))
    return render_template('objects_list.html', objects=objects)

@virtualrest.route('/objects/', defaults={'max_results': 15, 'page': 0})
@virtualrest.route('/objects/<int:max_results>/<int:page>')
def objects(max_results, page):
    if (not session.get('logged_in')):
        return redirect(url_for('login'))
    access = check_access('objects')
    total_pages = mongodb.db.objects.find({}).count() / max_results
    objects = copy_cursor(mongodb.db.objects.find({},
        {
            '_id': 1,
            'id': 1,
            'translations.title': 1,
            'translations.audio': 1,
            'translations.video': 1,
            'translations.isocode': 1
        },
        skip = (max_results * page),
        limit = max_results,
        sort = [ ('id',1) ]
    ))
    isocountries = copy_cursor(mongodb.db.isocountries.find({}, {'_id': 0, 'name': 1, 'alpha2':1}, sort=([('name',1)])))
    isolanguages = copy_cursor(mongodb.db.isolanguages.find({}, {'_id': 0}, sort=([('English',1)])))
    languages = copy_cursor(mongodb.db.languages.find({}, sort=([('name',1),('variant',1)])))
    return render_template('objects.html',
        access=access,
        objects=objects,
        languages=languages,
        isolanguages=isolanguages,
        isocountries=isocountries,
        curpage=page,
        total_pages=total_pages,
        max_results=max_results
    )

@virtualrest.route('/get_object/<_id>')
def get_object(_id):
    if (not session.get('logged_in')):
        return redirect(url_for('login'))
    check_access('objects')

    search_result = mongodb.db.objects.find_one({'_id': ObjectId(_id)})
    languages = copy_cursor(mongodb.db.languages.find({}, sort = ( [('code',1), ('locale',1)])))
    languages_used = []
    for t in search_result['translations']:
        languages_used.append(t['isocode'])
    return render_template('object_detail.html', object=search_result, languages=languages, languages_used=languages_used)

@virtualrest.route('/add_object', methods=['POST'])
def add_object():
    if (not session.get('logged_in')):
        return redirect(url_for('login'))
    check_access('objects')
    keys = request.form.keys()
    objid = request.form['id']
    keys.remove('id')
    languages = []
    for key in keys:
        elements = request.form.getlist(key)
        languages.append({'isocode':elements[0],'title':elements[1],'text':elements[2]})
    Object_JSON['id'] = objid
    for language in languages:
        Object_JSON['translations'].append({
            'isocode': language['isocode'],
            'title': language['title'],
            'text': language['text'],
            'audio': False,
            'video': False
        })
    mongodb.db.objects.insert_one(Object_JSON.copy())
    create_obj_img_intodb(request.files['file'],objid)
    return redirect(url_for('objects'))

@virtualrest.route('/del_object/<_id>', methods=['GET'])
def del_object(_id):
    if (not session.get('logged_in')):
        return redirect(url_for('login'))
    check_access('objects')

    result = mongodb.db.objects.find_one_and_delete({ '_id': ObjectId(_id) }, projection={'_id':1, 'id':1})
    if (result is not None):
        del_files_of_object(result['id'], ['all'])
    return redirect(url_for('objects'))

@virtualrest.route('/change_object', methods=['POST'])
def change_object():
    if (not session.get('logged_in')):
        return redirect(url_for('login'))
    check_access('objects')

    _id = request.form['_id']
    objid = request.form['id']
    for file_key in request.files.keys():
        if (request.files[file_key].filename != ''):
            if (file_key == 'imagefile'):
                create_obj_img_intodb(request.files[file_key],objid)
            else:
                isocode = file_key[-5:]
                set_obj_media(objid, isocode, 'audios', request.files[file_key])

    keys = request.form.keys()
    keys.remove('_id')
    keys.remove('id')
    for key in keys:
        elements = request.form.getlist(key)
        if (len(elements) < 3):
            break
        if (elements[0] == 'new'):
            elements.pop(0)
            result = mongodb.db.objects.update_one(
                { '_id': ObjectId(_id) },
                { '$addToSet': {'translations': {
                    'isocode': elements[0],
                    'title': elements[1],
                    'text': elements[2],
                    'audio': False,
                    'video': False
                    }
                } },
                upsert = True
            )
        elif (elements[0] == 'removelanguage'):
            elements.pop(0)
            result = mongodb.db.objects.update_one(
                { '_id': ObjectId(_id) },
                { '$pull': {'translations': {'isocode': elements[0]} } }
            )
        else:
            result = mongodb.db.objects.update_one(
                {
                    '_id': ObjectId(_id),
                    'translations': { '$elemMatch': {'isocode': elements[0]} }
                },{
                    '$set': {
                        'id': objid,
                        'translations.$.title': elements[1],
                        'translations.$.text': elements[2]
                    }
                },
                upsert = False
            )
        if (elements[-1] == 'removeaudio'):
            del_obj_media(objid, elements[0], 'audios')

    return redirect(url_for('get_object',_id=_id))

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

@virtualrest.route('/statics/<rtype>/<filename>')
def statics(rtype,filename):
    if (rtype in ['imgs','fonts','css','js']):
        return send_from_directory(virtualrest.static_folder + '/' + rtype, filename, as_attachment=True)
    else:
        abort(404)

if __name__ == '__main__':
    localaddress = config.get('MAIN', 'local_address')
    localport = config.getint('MAIN', 'local_port')
    if (config.getboolean('MAIN', 'debug') ):
        virtualrest.run(host=localaddress, port=8080, debug=True)
    else:
        if (config.getboolean('MAIN', 'use_ssl')):
            key_file = config.get('MAIN', 'ssl_key_file')
            cert_file = config.get('MAIN', 'ssl_cert_file')
            http_server = WSGIServer((localaddress, localport), virtualrest, keyfile=key_file, certfile=cert_file)
        else:
            http_server = WSGIServer((localaddress, localport), virtualrest)
        try:
            http_server.serve_forever()
        except KeyboardInterrupt:
            http_server.stop()
