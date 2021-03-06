#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# load tempfile for temporary dir creation
import sys, os, tempfile, shutil
# load misc utils
import json
# import uuid
from werkzeug.utils import secure_filename, safe_join
import logging
# logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.DEBUG)
# logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.ERROR)

# load libraries for string proccessing
import re, string

# for intervals computation
import pandas as pd
# load libraries for XML proccessing
import xml.etree.ElementTree as ET

# load libraries for API proccessing
from flask import Flask, jsonify, flash, request, Response, abort, render_template, make_response, send_file

# A Flask extension for handling Cross Origin Resource Sharing (CORS), making cross-origin AJAX possible.
from flask_cors import CORS

# for spooler tasks
import uwsgi
from tasks import confor_service_3, confor_service_3_4

ALLOWED_EXTENSIONS = set(['xlsx', 'csv', 'xml'])

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

app.use_x_sendfile = True

# ! Functions ------------------------------------------------------------------------------------------

# function that check if an extension is valid
def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_number_repl_isdigit(s):
    """ Returns True is string is a number. """
    return s.replace('.','',1).isdigit()

@app.route('/')
def index():
    return Response(render_template('index.html'), mimetype='text/html')

# ! API ---------------------------------------------------------------------------------------------------

# * discretization by intervals
@app.route('/api/confor/discretization', methods=['POST'])
def discretization_by_intervals():
    # check if the post request has the file part
    if 'input-csv' not in request.files:
        flash('No files')
        return abort(400)
    if 'input-xml' not in request.files:
        flash('No files')
        return abort(400)

    uploaded_csv = request.files['input-csv']
    uploaded_xml = request.files['input-xml']

    destinations_list = []
    intervals_dict = {}

    # if user does not select file, browser also submit an empty part without filename
    if uploaded_csv.filename == '':
        flash('No selected file')
        return abort(400)
    # if user does not select file, browser also submit an empty part without filename
    if uploaded_xml.filename == '':
        flash('No selected file')
        return abort(400)

    if uploaded_csv and allowed_file(uploaded_csv.filename):
        if uploaded_csv.filename.rsplit('.', 1)[1].lower() == 'csv':
            csv_filename = secure_filename(uploaded_csv.filename)
            destination = "/".join([tempfile.mkdtemp(),csv_filename])
            uploaded_csv.save(destination)
            destinations_list.append(destination)
            uploaded_csv.close()

    if uploaded_xml and allowed_file(uploaded_xml.filename):
        if uploaded_xml.filename.rsplit('.', 1)[1].lower() == 'xml':
            xml_filename = secure_filename(uploaded_xml.filename)
            destination = "/".join([tempfile.mkdtemp(),xml_filename])
            uploaded_xml.save(destination)
            destinations_list.append(destination)
            uploaded_xml.close()

    xml_tree = ET.parse(destinations_list[1])
    xml_root = xml_tree.getroot()
    for attribute in xml_root.findall('Attribute'):
        name = attribute.find('Name')
        logging.debug(name.text)
        intervals_dict.update({name.text: {'intervals': [], 'index': {}}})

    logging.debug('INTERVALS EMPTY: ')
    logging.debug(intervals_dict)

    for attribute in xml_root.findall('Attribute'):
        name = attribute.find('Name')
        print(name.text)
        for interval in attribute.findall('Interval'):
            min_value = interval.find('Min').text
            max_value = interval.find('Max').text
            intervals_dict[name.text]['intervals'].append(pd.Interval(float(min_value), float(max_value), closed='both'))

    logging.debug('INTERVALS INTERVALS: ')
    logging.debug(intervals_dict)

    # intervals_dict['sepal length']['index'] = pd.IntervalIndex(intervals_dict['sepal length']['intervals'])

    for key, value in intervals_dict.items():
        value['index'] = pd.IntervalIndex(value['intervals'])

    logging.debug('INTERVALS INTERVALS INDEX: ')
    logging.debug(intervals_dict)

    data = pd.read_csv(destinations_list[0], sep=';', dtype = str)

    columns_names_list = data.columns.values.tolist()

    for col_name in columns_names_list:
        if col_name not in ['Object', 'Class']:
            for item_index,item in enumerate(data[col_name]):
                print(item)
                print(type(item))
                if type(item) is not float:
                    if is_number_repl_isdigit(item):
                        if isinstance(intervals_dict[col_name]['index'].get_loc(float(item)), slice):
                            data.loc[item_index, col_name] = int(intervals_dict[col_name]['index'].get_loc(float(item)).start) + 1
                        else:
                            data.loc[item_index, col_name] = intervals_dict[col_name]['index'].get_loc(float(item)) + 1
                else:
                    data.loc[item_index, col_name] = ''

    destination = safe_join(tempfile.mkdtemp(), 'discretization-by-intervals.csv')
    try:
        # data.to_csv(destination, index=False, sep=';')
        return Response(data.to_csv(index=False, sep=';'), mimetype='text/csv')
        # data.to_csv(destination, index=False, sep=request.args['sep'])
    except Exception as e:
        logging.error(e, exc_info=True)
        return abort(500)

    # try:
    #     # safe_path = safe_join('/var/tmp/tasks/confor/' + taskID, 'output.xml')
    #     redirect_path = destination
    #     if os.path.exists(destination):
    #         return send_file(destination,
    #                  mimetype='text/csv',
    #                  download_name='discretization-by-intervals.csv',
    #                  as_attachment=True)
    #     # return send_file(safe_path, conditional=True, mimetype='text/xml')
    # except Exception as e:
    #     logging.error(e, exc_info=True)
    #     return abort(500)

# * SERVICE 3 --> output
@app.route('/api/confor/service/3', methods=['POST'])
def queued_service_3():
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
            # FIXME: Update toTask with try except
            toTask = confor_service_3.spool(project_dir = projectDir.encode(), filename = xlsxFileName.encode(), find = request.args['find'], destination = destination)
            toTask = toTask.decode('utf-8', errors='ignore')
            toTask = toTask.rpartition('/')[2]
            return jsonify({'task': { 'status': 'queued', 'service': '3','parameters': {'find': request.args['find'], 'encoding': 'utf-8', 'extension': 'xlsx'}, 'file': xlsxFileName, 'id': toTask}}), 202
    else:
        return jsonify({'file': { 'filename': 'not allowed'}}), 400

# * SERVICE 3 --> 4 --> output sequentially
@app.route('/api/confor/service/3/4', methods=['POST'])
def queued_service_3_4():
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
            # FIXME: Update toTask with try except
            toTask = confor_service_3_4.spool(project_dir = projectDir.encode(), filename = xlsxFileName.encode(), find = request.args['find'], destination = destination)
            toTask = toTask.decode('utf-8', errors='ignore')
            toTask = toTask.rpartition('/')[2]
            return jsonify({'task': { 'status': 'queued', 'service': '3-4','parameters': {'find': request.args['find'], 'encoding': 'utf-8', 'extension': 'xlsx'}, 'file': xlsxFileName, 'id': toTask}}), 202
    else:
        return jsonify({'file': { 'filename': 'not allowed'}}), 400

@app.route('/api/confor/service/status')
def check_service_status():
    taskID = request.args.get('id')
    if not os.path.exists('/var/tmp/tasks/confor/' + taskID):
        return jsonify({'task': {'id': taskID, 'status': False}}), 204
    if os.path.exists('/var/tmp/tasks/confor/' + taskID):
        return jsonify({'task': {'id': taskID, 'status': True}}), 200

@app.route('/api/confor/service/output')
def get_service_output_xml():
    taskID = request.args.get('id')
    if not os.path.exists('/var/tmp/tasks/confor/' + taskID):
        return jsonify({'task': taskID, 'status': False}), 204
    if not os.path.isfile('/var/tmp/tasks/confor/' + taskID + '/output.xml'):
        return jsonify({'task': taskID, 'status': False}), 204

    # This works in async !!!
    # @after_this_request
    # def remove_output_xml(response):
    #     safe_path = safe_join('/var/tmp/tasks/confor/' + taskID, 'output.xml')
    #     try:
    #         os.remove(safe_path)
    #         if not os.path.isfile(safe_path):
    #             shutil.rmtree('/var/tmp/tasks/confor/' + taskID)
    #     except Exception as e:
    #         logging.error(e, exc_info=True)
    #         return abort(500)
    #     return response

    # FIXME: Need to delete taskID folders
    try:
        # safe_path = safe_join('/var/tmp/tasks/confor/' + taskID, 'output.xml')
        redirect_path = safe_join('/download_file/' + taskID, 'output.xml')
        response = make_response("")
        response.headers["X-Accel-Redirect"] = redirect_path
        response.headers["Content-Type"] = 'text/xml'
        return response
        # return send_file(safe_path, conditional=True, mimetype='text/xml')
    except Exception as e:
        logging.error(e, exc_info=True)
        return abort(500)

if __name__ == '__main__':
    # default port = 5000
    app.run(host = '0.0.0.0')