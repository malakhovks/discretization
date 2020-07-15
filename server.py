#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# load tempfile for temporary dir creation
import sys, os, tempfile
# load misc utils
import json
# import uuid
from werkzeug.utils import secure_filename
import logging
# logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.DEBUG)
# logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.ERROR)

# load libraries for string proccessing
import re, string

# from io import StringIO, BytesIO

# load libraries for API proccessing
from flask import Flask, jsonify, flash, request, Response, redirect, url_for, abort, render_template

# A Flask extension for handling Cross Origin Resource Sharing (CORS), making cross-origin AJAX possible.
from flask_cors import CORS

# for spooler
import uwsgi
from tasks import confor_task

ALLOWED_EXTENSIONS = set(['xlsx'])

__author__ = "Kyrylo Malakhov <malakhovks@nas.gov.ua> and Vitalii Velychko <aduisukr@gmail.com>"
__copyright__ = "Copyright (C) 2020 Kyrylo Malakhov <malakhovks@nas.gov.ua> and Vitalii Velychko <aduisukr@gmail.com>"

app = Flask(__name__)
CORS(app)

"""
Limited the maximum allowed payload to 16 megabytes.
If a larger file is transmitted, Flask will raise an RequestEntityTooLarge exception.
"""
# app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

"""
Set the secret key to some random bytes. Keep this really secret!
How to generate good secret keys.
A secret key should be as random as possible. Your operating system has ways to generate pretty random data based on a cryptographic random generator. Use the following command to quickly generate a value for Flask.secret_key (or SECRET_KEY):
$ python -c 'import os; print(os.urandom(16))'
b'_5#y2L"F4Q8z\n\xec]/'
"""
# app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
app.secret_key = os.urandom(42)


"""
# ------------------------------------------------------------------------------------------------------
# Functions
# ------------------------------------------------------------------------------------------------------
# """
# function that check if an extension is valid
def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return 'Hello, CONFOR!'

"""
# API ---------------------------------------------------------------------------------------------------
# """

@app.route('/api/confor/file/find', methods=['POST'])
def queued_find():
    # check if the post request has the file part
    if 'file' not in request.files:
        flash('No file part')
        return abort(400)

    file = request.files['file']

    # if user does not select file, browser also submit an empty part without filename
    if file.filename == '':
        flash('No selected file')
        return abort(400)

    if file and allowed_file(file.filename):
        projectDir = os.getcwd()
        # xlsx processing
        if file.filename.rsplit('.', 1)[1].lower() == 'xlsx':
            xlsxFileName = secure_filename(file.filename)
            xlsxFile = secure_filename(file.filename)
            destination = "/".join([tempfile.mkdtemp(),xlsxFile])
            file.save(destination)
            file.close()
            try:
                with open(destination,'rb') as xlsxFile:
                    xlsxFileBinary = xlsxFile.read()
            except IOError as e:
                logging.error(e, exc_info=True)
                return abort(500)
            toTask = confor_task.spool(project_dir = projectDir.encode(), filename = xlsxFileName.encode(), body = xlsxFileBinary)
            toTask = toTask.decode('utf-8', errors='ignore')
            toTask = toTask.rpartition('/')[2]
            return jsonify({'task': { 'status': 'queued', 'parameters': {'mode':'find', 'encoding': 'Windows-1251'}, 'file': xlsxFileName, 'id': resp}}), 202
    else:
        return jsonify({'file': { 'filename': 'not allowed'}}), 400

@app.route('/api/confor/file/find/status')
def check_find_status():
    taskID = request.args.get('id')
    if not os.path.exists('/var/tmp/tasks/confor/' + taskID):
        return jsonify({'task': {'id': taskID, 'status': False}}), 204
    if os.path.exists('/var/tmp/tasks/confor/' + task_id):
        return jsonify({'task': {'id': taskID, 'status': True}}), 200

@app.route('/api/confor/file/task/output')
def get_output_xml():
    taskID = request.args.get('id')
    if not os.path.exists('/var/tmp/tasks/confor/' + taskID):
        return jsonify({'task': taskID, 'status': False}), 204
    if not os.path.isfile('/var/tmp/tasks/confor/' + taskID + '/output.xml'):
        return jsonify({'task': task_id, 'status': False}), 204

    try:
        safe_path = safe_join('/var/tmp/tasks/confor/' + taskID, 'output.xml')
        return send_file(safe_path, conditional=True, mimetype='text/xml')
    except Exception as e:
        logging.error(e, exc_info=True)
        return abort(500)

@app.route('/api/confor/file/nofind', methods=['POST'])
def noFind():
    return 'Hello, CONFOR!'

if __name__ == '__main__':
    # default port = 5000
    app.run(host = '0.0.0.0')