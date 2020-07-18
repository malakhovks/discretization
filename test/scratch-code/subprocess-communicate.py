#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# load tempfile for temporary dir creation
import sys, os, tempfile, subprocess

# load libraries for NLP pipeline
import spacy
# load Visualizers 
from spacy import displacy
# load Matcher
from spacy.matcher import Matcher
# load textacy
import textacy
import textacy.ke

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

# load libraries for pdf processing pdfminer
from io import StringIO, BytesIO
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser

# load libraries for docx processing
import zipfile
WORD_NAMESPACE = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
PARA = WORD_NAMESPACE + 'p'
TEXT = WORD_NAMESPACE + 't'
# load libraries for XML proccessing
import xml.etree.ElementTree as ET

# load libraries for API proccessing
from flask import Flask, jsonify, flash, request, Response, redirect, url_for, abort, render_template

# A Flask extension for handling Cross Origin Resource Sharing (CORS), making cross-origin AJAX possible.
from flask_cors import CORS

ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'docx'])

# Load globally spaCy model via package name
NLP_NB = spacy.load('nb_core_news_sm')
# Load lemmas only
NLP_NB_LEMMA = spacy.load('nb_core_news_sm', disable=["parser", "tagger"])
# NLP_NB_VECTORES = spacy.load('./tmp/nb_nowac_vectores')
# NLP_EN_VECTORES = spacy.load('en_core_web_lg')

# Load globally textacy spaCy model
nb = textacy.load_spacy_lang("nb_core_news_sm", disable=("parser",))

# load SnowballStemmer stemmer from nltk
from nltk.stem.snowball import SnowballStemmer
# Load globally english SnowballStemmer
NORWEGIAN_STEMMER = SnowballStemmer("norwegian")

# for hunspell https://github.com/blatinier/pyhunspell
import hunspell
nb_spell = hunspell.HunSpell('./deploy/dictionary/nb.dic', './deploy/dictionary/nb.aff')

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

# default sentence normalization
def sentence_normalization_default(raw_sentence):
    # remove tabs and insert spaces
    raw_sentence = re.sub('[\t]', ' ', raw_sentence)
    # remove multiple spaces
    raw_sentence = re.sub('\s\s+', ' ', raw_sentence)
    # remove all numbers
    # line = re.sub(r'\d+','',line)
    # remove leading and ending spaces
    raw_sentence = raw_sentence.strip()
    normalized_sentence = raw_sentence
    return normalized_sentence

# default text normalization
def text_normalization_default(raw_text):
    raw_text_list = []
    for line in raw_text.splitlines(True):
        # if line contains letters
        if re.search(r'[a-z]+', line):
            """
            remove \n \r \r\n new lines and insert spaces
            \r = CR (Carriage Return) → Used as a new line character in Mac OS before X
            \n = LF (Line Feed) → Used as a new line character in Unix/Mac OS X
            \r\n = CR + LF → Used as a new line character in Windows
            """
            """
            \W pattern: When the LOCALE and UNICODE flags are not specified, matches any non-alphanumeric character;
            this is equivalent to the set [^a-zA-Z0-9_]. With LOCALE, it will match any character not in the set [0-9_], and not defined as alphanumeric for the current locale.
            If UNICODE is set, this will match anything other than [0-9_] plus characters classified as not alphanumeric in the Unicode character properties database.
            To remove all the non-word characters, the \W pattern can be used as follows:
            """
            # line = re.sub(r'\W', ' ', line, flags=re.I)
            # remove all non-words except punctuation
            # line = re.sub('[^\w.,;!?-]', ' ', line)
            # remove all words which contains number
            line = re.sub(r'\w*\d\w*', ' ', line)
            # remove % symbol
            line = re.sub('%', ' ', line)
            # remove ° symbol
            line = re.sub('[°]', ' ', line)
            line = re.sub('[\n]', ' ', line)
            line = re.sub('[\r\n]', ' ', line)
            line = re.sub('[\r]', ' ', line)
            # remove tabs and insert spaces
            line = re.sub('[\t]', ' ', line)
            # Replace multiple dots with space
            line = re.sub('\.\.+', ' ', line)
            # remove multiple spaces
            line = re.sub('\s\s+', ' ', line)
            # remove all numbers
            # line = re.sub(r'\d+','',line)
            # remove leading and ending spaces
            line = line.strip()
            raw_text_list.append(line)
    yet_raw_text = ' '.join(raw_text_list)
    return yet_raw_text

# Extracting all the text from DOCX
def get_unicode_from_docx(docx_path):
    """
    Take the path of a docx file as argument, return the text in unicode.
    """
    document = zipfile.ZipFile(docx_path)
    xml_content = document.read('word/document.xml')
    document.close()
    tree = ET.XML(xml_content)
    paragraphs = []
    for paragraph in tree.iter(PARA):
        texts = [node.text
                 for node in paragraph.iter(TEXT)
                 if node.text]
        if texts:
            paragraphs.append(''.join(texts))
    return '\n\n'.join(paragraphs)
# Extracting all the text from PDF with PDFMiner.six
def get_unicode_from_pdf(pdf_path):
    rsrcmgr = PDFResourceManager()
    codec = 'utf-8'
    laparams = LAParams()
    # save document layout including spaces that are only visual not a character
    """
    Some pdfs mark the entire text as figure and by default PDFMiner doesn't try to perform layout analysis for figure text. To override this behavior the all_texts parameter needs to be set to True
    """
    laparams = LAParams()
    setattr(laparams, 'all_texts', True)
    # save document layout including spaces that are only visual not a character
    with StringIO() as retstr:
        with TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams) as device:
            with open(pdf_path, 'rb') as fp:
                interpreter = PDFPageInterpreter(rsrcmgr, device)
                password = ""
                maxpages = 0
                caching = True
                pagenos = set()
                for page in PDFPage.get_pages(fp, pagenos, maxpages=maxpages, password=password, caching=caching, check_extractable=True):
                    interpreter.process_page(page)
        return retstr.getvalue()
"""
# API ---------------------------------------------------------------------------------------------------
# """
# --------------------------------------------------------------------------------------------------------
@app.route('/api/bot/nb/message/json/allterms', methods=['POST'])
def get_allterms_json():
    req_data = request.get_json()

    # for allterms JSON structure
    allterms = {
      "termsintext": {
        "exporterms": {
            "term": {}
        },
        "keyterms": {
            "algorithm": {
                "textrank": {
                    "terms": []
                }
            }
        },
        "sentences": {
            "sent": []
        }
      }
    }

    terms_element = allterms['termsintext']['exporterms']['term']
    terms_textrank_array = allterms['termsintext']['keyterms']['algorithm']['textrank']['terms']
    sent_array = allterms['termsintext']['sentences']['sent']
    # for allterms JSON structure

    # patterns for spaCy Matcher https://spacy.io/usage/rule-based-matching
    patterns = [
    # 1 term
    [{'POS': {'IN':['NOUN', 'PROPN']}}],
    # [{'POS': 'PROPN'}],
    # [{'POS': 'NOUN'}],
    # 2 terms
    [{'POS': {'IN':['NOUN', 'ADJ','PROPN']}}, {'POS': {'IN':['NOUN', 'ADJ','PROPN']}}],
    # 3 terms
    [{'POS': {'IN':['NOUN', 'ADJ','PROPN']}}, {'POS': {'IN':['NOUN', 'ADJ','PROPN']}}, {'POS': {'IN':['NOUN', 'ADJ','PROPN']}}],
    # 4 terms
    [{'POS': {'IN':['NOUN', 'ADJ','PROPN']}}, {'POS': {'IN':['NOUN', 'ADJ','PROPN']}},{'POS': {'IN':['NOUN', 'ADJ','PROPN']}}, {'POS': {'IN':['NOUN', 'ADJ','PROPN']}}],
    # 3 terms with APD in the middle
    [{'POS': {'IN':['NOUN', 'ADJ','PROPN']}}, {'POS': {'IN':['NOUN', 'ADJ','PROPN', 'ADP']}}, {'POS': {'IN':['NOUN', 'ADJ','PROPN']}}]
    ]
    matcher = Matcher(NLP_NB.vocab)
    matcher.add("NOUN/PROPN", None, patterns[0])
    matcher.add("NOUN/ADJ/PROPN+NOUN/ADJ/PROPN", None, patterns[1])
    matcher.add("NOUN/ADJ/PROPN+NOUN/ADJ/PROPN+NOUN/ADJ/PROPN", None, patterns[2])
    matcher.add("NOUN/ADJ/PROPN+NOUN/ADJ/PROPN+NOUN/ADJ/PROPN+NOUN/ADJ/PROPN", None, patterns[3])
    matcher.add("NOUN/ADJ/PROPN+NOUN/ADJ/PROPN/ADP+NOUN/ADJ/PROPN", None, patterns[4])

    try:
        # spaCy doc init + default sentence normalization
        doc = NLP_NB(req_data['message'])

        # Helper list for 1-word terms
        # one_word_terms_help_list_json = []
        # Helper list for 2-word terms
        # two_word_terms_help_list_json = []
        # Helper list for 3-word terms
        # three_word_terms_help_list_json = []

        # Helper list for multiple-word terms (from 4-word terms)
        multiple_word_terms_help_list = []

        # Main text parsing cycle for sentences
        for sentence_index, sentence in enumerate(doc.sents):
            # default sentence normalization
            # sentence_clean = sentence_normalization_default(sentence.text)
            sentence_clean = sentence.text

            # for processing specific sentence
            doc_for_chunks = NLP_NB(sentence_clean)

            # for processing specific sentence with textacy
            doc_textacy = textacy.make_spacy_doc(sentence_clean, lang=nb)

            logging.debug('Sentence: ' + doc_for_chunks.text)

            # TEXTACY TextRank for KEY TERMS ---------------------
            key_terms_list = textacy.ke.textrank(doc_textacy, normalize="lemma", topn=10)

            if key_terms_list:
                logging.debug('TextRank Key terms list: ' + str(key_terms_list))
                for trm in key_terms_list:
                    if not terms_textrank_array:
                        terms_textrank_array.append({'tname': trm[0], 'rank': trm[1], 'sentidx': [sentence_index]})
                    if terms_textrank_array:
                        indx_if_exist = next((i for i, item in enumerate(terms_textrank_array) if item["tname"] == trm[0]), None)
                        if indx_if_exist:
                            logging.debug('Index of a sentence in which the term is: ' + str(indx_if_exist))
                            terms_textrank_array[indx_if_exist]['sentidx'].append(sentence_index)
                        if indx_if_exist is None:
                            logging.debug('Index of a sentence in which the term is: ' + str(indx_if_exist))
                            terms_textrank_array.append({'tname': trm[0], 'rank': trm[1], 'sentidx': [sentence_index]})
            if not key_terms_list:
                logging.debug('TextRank Key terms list: EMPTY')


            # MATCHING NOUN --------------------------------------

            matches = matcher(doc_for_chunks)
            # add sentence to sent array
            sent_array.append(doc_for_chunks.text)
            for match_id, start, end in matches:
                string_id = NLP_NB.vocab.strings[match_id]
                span = doc_for_chunks[start:end]

                if len(span) == 1:

                    logging.debug('Matched span: ' + span.text + ' | Span lenght: ' + str(len(span)) + ' | Span POS: ' + span.root.pos_)

                    if span.lemma_ not in terms_element:
                    # if span.lemma_ not in one_word_terms_help_list_json:
                        # one_word_terms_help_list_json.append(span.lemma_)
                        term_properties = {}
                        sentpos_array = []
                        term_properties['wcount'] = '1'
                        term_properties['ttype'] = span.root.pos_
                        term_properties['tname'] = span.lemma_
                        term_properties['osn'] = NORWEGIAN_STEMMER.stem(span.text)
                        sentpos_array.append(str(sentence_index) + '/' + str(span.start+1))
                        term_properties['sentpos'] = sentpos_array
                        terms_element[span.lemma_] = term_properties

                    else:
                        if span.lemma_ in terms_element:
                            if str(sentence_index) + '/' + str(span.start+1) not in terms_element[span.lemma_]['sentpos']:
                                terms_element[span.lemma_]['sentpos'].append(str(sentence_index) + '/' + str(span.start+1))

                if len(span) == 2:

                    logging.debug('Matched span: ' + span.text + ' | Span lenght: ' + str(len(span)) + ' | Span POS: ' + str([tkn.pos_ for tkn in span]) + ' | Span\'s root: ' + span.root.lemma_ + ' | Span subtree: ' + str([sub.head for sub in span.subtree]))

                    if span.lemma_ not in terms_element:
                    # if span.lemma_ not in two_word_terms_help_list_json:
                        # two_word_terms_help_list_json.append(span.lemma_)
                        term_properties = {}
                        sentpos_array = []
                        term_properties['wcount'] = '2'
                        term_properties['ttype'] = '_'.join(tkn.pos_ for tkn in span)
                        term_properties['tname'] = span.lemma_
                        term_properties['osn'] = [NORWEGIAN_STEMMER.stem(tkn.text) for tkn in span]
                        sentpos_array.append(str(sentence_index) + '/' + str(span.start+1))
                        term_properties['sentpos'] = sentpos_array
                        terms_element[span.lemma_] = term_properties

                        if span.root.pos_ in ['NOUN', 'PROPN']:
                            if span.root.lemma_ in terms_element:
                                if 'reldown' in terms_element[span.root.lemma_]:
                                    terms_element[span.root.lemma_]['reldown'].append(list(terms_element).index(span.lemma_) + 1)
                                else:
                                    reldown_array = []
                                    reldown_array.append(list(terms_element).index(span.lemma_) + 1)
                                    terms_element[span.root.lemma_]['reldown'] = reldown_array
                            else:
                                # one_word_terms_help_list_json.append(span.root.lemma_)
                                term_properties = {}
                                sentpos_array = []
                                term_properties['wcount'] = '1'
                                term_properties['ttype'] = span.root.pos_
                                term_properties['tname'] = span.root.lemma_
                                term_properties['osn'] = NORWEGIAN_STEMMER.stem(span.root.text)
                                sentpos_array.append(str(sentence_index) + '/' + str(span.root.i+1))
                                term_properties['sentpos'] = sentpos_array
                                reldown_array = []
                                reldown_array.append(list(terms_element).index(span.lemma_) + 1)
                                term_properties['reldown'] = reldown_array
                                terms_element[span.root.lemma_] = term_properties

                            # if ROOT in 0 position
                            if [tkn.text for tkn in span].index(span.root.text) == 0:
                                if  span[1].pos_ in ['NOUN', 'PROPN']:
                                    if span[1].lemma_ in terms_element:
                                        if 'reldown' in terms_element[span[1].lemma_]:
                                            terms_element[span[1].lemma_]['reldown'].append(list(terms_element).index(span.lemma_) + 1)
                                        else:
                                            reldown_array = []
                                            reldown_array.append(list(terms_element).index(span.lemma_) + 1)
                                            terms_element[span[1].lemma_]['reldown'] = reldown_array
                                    else:
                                        # one_word_terms_help_list_json.append(span[1].lemma_)
                                        term_properties = {}
                                        sentpos_array = []
                                        term_properties['wcount'] = '1'
                                        term_properties['ttype'] = span[1].pos_
                                        term_properties['tname'] = span[1].lemma_
                                        term_properties['osn'] = NORWEGIAN_STEMMER.stem(span[1].text)
                                        sentpos_array.append(str(sentence_index) + '/' + str(span[1].i+1))
                                        term_properties['sentpos'] = sentpos_array
                                        reldown_array = []
                                        reldown_array.append(list(terms_element).index(span.lemma_) + 1)
                                        term_properties['reldown'] = reldown_array
                                        terms_element[span[1].lemma_] = term_properties
                            # if ROOT in 1 position
                            else:
                                if span[0].pos_ in ['NOUN', 'PROPN']:
                                    if span[0].lemma_ in terms_element:
                                        if 'reldown' in terms_element[span[0].lemma_]:
                                            terms_element[span[0].lemma_]['reldown'].append(list(terms_element).index(span.lemma_) + 1)
                                        else:
                                            reldown_array = []
                                            reldown_array.append(list(terms_element).index(span.lemma_) + 1)
                                            terms_element[span[0].lemma_]['reldown'] = reldown_array
                                    else:
                                        # one_word_terms_help_list_json.append(span[1].lemma_)
                                        term_properties = {}
                                        sentpos_array = []
                                        term_properties['wcount'] = '1'
                                        term_properties['ttype'] = span[0].pos_
                                        term_properties['tname'] = span[0].lemma_
                                        term_properties['osn'] = NORWEGIAN_STEMMER.stem(span[0].text)
                                        sentpos_array.append(str(sentence_index) + '/' + str(span[0].i+1))
                                        term_properties['sentpos'] = sentpos_array
                                        reldown_array = []
                                        reldown_array.append(list(terms_element).index(span.lemma_) + 1)
                                        term_properties['reldown'] = reldown_array
                                        terms_element[span[0].lemma_] = term_properties

                            if 'relup' in terms_element[span.lemma_]:
                                terms_element[span.lemma_]['relup'].append(list(terms_element).index(span.lemma_) + 1)
                            else:
                                relup_array = []
                                relup_array.append(list(terms_element).index(span.root.lemma_) + 1)
                                terms_element[span.lemma_]['relup'] = relup_array

                        # if span.root.pos_ == 'ADJ':
                        #     if span.root.lemma_ in terms_element:
                        #         if 'reldown' in terms_element[span.root.lemma_]:
                        #             terms_element[span.root.lemma_]['reldown'].append(list(terms_element).index(span.root.lemma_) + 1)
                        #         else:
                        #             reldown_array = []
                        #             reldown_array.append(list(terms_element).index(span.root.lemma_) + 1)
                        #             terms_element[span.root.lemma_]['reldown'] = reldown_array
                        #     else:
                        #         one_word_terms_help_list_json.append(span.root.lemma_)
                        #         term_properties = {}
                        #         sentpos_array = []
                        #         term_properties['wcount'] = '1'
                        #         term_properties['ttype'] = span.root.pos_
                        #         term_properties['tname'] = span.root.lemma_
                        #         term_properties['osn'] = NORWEGIAN_STEMMER.stem(span.root.text)
                        #         sentpos_array.append(str(sentence_index) + '/' + str(span.root.i+1))
                        #         term_properties['sentpos'] = sentpos_array
                        #         reldown_array = []
                        #         reldown_array.append(list(terms_element).index(span.lemma_) + 1)
                        #         term_properties['reldown'] = reldown_array
                        #         terms_element[span.root.lemma_] = term_properties

                        #     if 'relup' in terms_element[span.lemma_]:
                        #         terms_element[span.lemma_]['relup'].append(list(terms_element).index(span.lemma_) + 1)
                        #     else:
                        #         relup_array = []
                        #         relup_array.append(list(terms_element).index(span.root.lemma_) + 1)
                        #         terms_element[span.lemma_]['relup'] = relup_array

                    else:
                        if span.lemma_ in terms_element:
                            if str(sentence_index) + '/' + str(span.start+1) not in terms_element[span.lemma_]['sentpos']:
                                terms_element[span.lemma_]['sentpos'].append(str(sentence_index) + '/' + str(span.start+1))

                if len(span) == 3:

                    logging.debug('Matched span: ' + span.text + ' | Span lenght: ' + str(len(span)) + ' | Span POS: ' + str([tkn.pos_ for tkn in span]) + ' | Span\'s root: ' + span.root.lemma_ + ' | Span subtree: ' + str([sub.head for sub in span.subtree]))

                    if span.lemma_ not in terms_element:
                    # if span.lemma_ not in three_word_terms_help_list_json:
                        # three_word_terms_help_list_json.append(span.lemma_)
                        term_properties = {}
                        sentpos_array = []
                        term_properties['wcount'] = '3'
                        term_properties['ttype'] = '_'.join(tkn.pos_ for tkn in span)
                        term_properties['tname'] = span.lemma_
                        term_properties['osn'] = [NORWEGIAN_STEMMER.stem(tkn.text) for tkn in span]
                        sentpos_array.append(str(sentence_index) + '/' + str(span.start+1))
                        term_properties['sentpos'] = sentpos_array
                        terms_element[span.lemma_] = term_properties

                    else:
                        if span.lemma_ in terms_element:
                            if str(sentence_index) + '/' + str(span.start+1) not in terms_element[span.lemma_]['sentpos']:
                                terms_element[span.lemma_]['sentpos'].append(str(sentence_index) + '/' + str(span.start+1))

                if len(span) == 4:

                    logging.debug('Matched span: ' + span.text + ' | Span lenght: ' + str(len(span)) + ' | Span POS: ' + str([tkn.pos_ for tkn in span]) + ' | Span\'s root: ' + span.root.lemma_ + ' | Span subtree: ' + str([sub.head for sub in span.subtree]))

        logging.debug(allterms)

        return Response(json.dumps(allterms), mimetype='application/json')

    except Exception as e:
        logging.error(e, exc_info=True)
        return abort(500)
# --------------------------------------------------------------------------------------------------------
# Text messages
@app.route('/api/bot/nb/message/xml/parce', methods=['POST'])
def get_parcexml():
    # POS UD
    # https://universaldependencies.org/u/pos/
    if request.args.get('pos', None) == 'udkonspekt':
        speech_dict_POS_tags = {'NOUN':'S1', 'ADJ':'S2', 'VERB': 'S4', 'INTJ':'S21', 'PUNCT':'98', 'SYM':'98', 'CONJ':'U', 'NUM':'S7', 'X':'99', 'PRON':'S11', 'ADP':'P', 'PROPN':'S22', 'ADV':'S16', 'AUX':'99', 'CCONJ':'U', 'DET':'99', 'PART':'99', 'SCONJ':'U', 'SPACE':'98'}
    # TODO Correctly relate the parts of speech with spaCy
    # tag_map.py in https://github.com/explosion/spaCy/tree/master/spacy/lang
    # POS spaCy
    if request.args.get('pos', None) == 'spacykonspekt':
        speech_dict_POS_tags = {'NOUN':'S1', 'ADJ':'S2', 'VERB': 'S4', 'INTJ':'S21', 'PUNCT':'98', 'SYM':'98', 'CONJ':'U', 'NUM':'S7', 'X':'S29', 'PRON':'S10', 'ADP':'P', 'PROPN':'S22', 'ADV':'S16', 'AUX':'AUX', 'CCONJ':'CCONJ', 'DET':'DET', 'PART':'PART', 'SCONJ':'SCONJ', 'SPACE':'SPACE'}

    req_data = request.get_json()

    try:
        doc = NLP_NB(req_data['message'])
        """
        # create the <parce.xml> file structure
        """
        # create root element <text>
        root_element = ET.Element("text")

        for sentence_index, sentence in enumerate(doc.sents):
            # XML structure creation
            new_sentence_element = ET.Element('sentence')
            # create and append <sentnumber>
            new_sentnumber_element = ET.Element('sentnumber')
            new_sentnumber_element.text = str(sentence_index+1)
            new_sentence_element.append(new_sentnumber_element)
            # create and append <sent>
            new_sent_element = ET.Element('sent')
            new_sent_element.text = sentence.text
            new_sentence_element.append(new_sent_element)

            doc_for_lemmas = NLP_NB(sentence.text)

            logging.debug('Sentence: ' + sentence.text)

            # create amd append <ner>, <entity>
            # NER labels description https://spacy.io/api/annotation#named-entities
            if len(doc_for_lemmas.ents) != 0:
                # create <ner>
                ner_element = ET.Element('ner')
                for ent in doc_for_lemmas.ents:
                    # create <entity>
                    new_entity_element = ET.Element('entity')
                    # create and append <entitytext>
                    new_entity_text_element = ET.Element('entitytext')
                    new_entity_text_element.text = ent.text
                    new_entity_element.append(new_entity_text_element)
                    # create and append <label>
                    new_entity_label_element = ET.Element('label')
                    new_entity_label_element.text = ent.label_
                    new_entity_element.append(new_entity_label_element)
                    # create and append <startentitypos>
                    new_start_entity_pos_character_element = ET.Element('startentityposcharacter')
                    new_start_entity_pos_token_element = ET.Element('startentitypostoken')
                    new_start_entity_pos_character_element.text = str(ent.start_char + 1)
                    new_start_entity_pos_token_element.text = str(ent.start + 1)
                    new_entity_element.append(new_start_entity_pos_character_element)
                    new_entity_element.append(new_start_entity_pos_token_element)
                    # create and append <endentitypos>
                    new_end_entity_pos_character_element = ET.Element('endentityposcharacter')
                    new_end_entity_pos_token_element = ET.Element('endentitypostoken')
                    new_end_entity_pos_character_element.text = str(ent.end_char)
                    new_end_entity_pos_token_element.text = str(ent.end)
                    new_entity_element.append(new_end_entity_pos_character_element)
                    new_entity_element.append(new_end_entity_pos_token_element)
                    # append <entity> to <ner>
                    ner_element.append(new_entity_element)
                # append <ner> to <sentence>
                new_sentence_element.append(ner_element)
            # create and append <item>, <word>, <lemma>, <number>, <pos>, <speech>
            for lemma in doc_for_lemmas:
                # create and append <item>
                new_item_element = ET.Element('item')
                # create and append <word>
                new_word_element = ET.Element('word')
                new_word_element.text = lemma.text
                new_item_element.append(new_word_element)
                # create and append <spell>
                if 'spell' in req_data:
                    if req_data['spell'] == True:
                        new_spell_element = ET.Element('spell')
                        new_correctness_element = ET.Element('correctness')
                        if nb_spell.spell(lemma.text):
                            new_correctness_element.text = str(nb_spell.spell(lemma.text))
                            new_spell_element.append(new_correctness_element)
                            new_item_element.append(new_spell_element)
                        else:
                            new_correctness_element.text = str(nb_spell.spell(lemma.text))
                            new_spell_element.append(new_correctness_element)
                            new_suggest_element = ET.Element('suggest')
                            for sggst in nb_spell.suggest(lemma.text):
                                new_sug_element = ET.Element('sug')
                                new_sug_element.text = sggst
                                new_spell_element.append(new_sug_element)
                            new_item_element.append(new_spell_element)
                # create and append <lemma>
                new_lemma_element = ET.Element('lemma')
                new_lemma_element.text = lemma.lemma_ #.encode('ascii', 'ignore')
                new_item_element.append(new_lemma_element)
                # create and append <number>
                new_number_element = ET.Element('number')
                new_number_element.text = str(lemma.i+1)
                new_item_element.append(new_number_element)
                # create and append <speech>
                new_speech_element = ET.Element('speech')
                # compound words split
                if 'compound' in req_data:
                    if req_data['compound']:
                        if lemma.pos_ in ["NOUN"]:
                            destination_text_for_mtag = '/tmp/mtag-master/text.txt'
                            try:
                                with open(destination_text_for_mtag, 'w') as f:
                                    f.write(lemma.lemma_ + ' . ' + lemma.text.lower())
                            except IOError as e:
                                logging.error(e, exc_info=True)
                                return abort(500)
                            args = ["/tmp/mtag-master/mtag.py", destination_text_for_mtag]
                            process = subprocess.Popen(args, stdout=subprocess.PIPE)
                            data = process.communicate()
                            logging.debug('-------------------------------------------------------------------------')
                            logging.debug('data[0]: ' + data[0].decode())
                            logging.debug('data[1]: %s', data[1])

                            if data[0].decode() == '':
                                logging.debug('Error while processing Word <' + lemma.text + '>. Maybe spell error.')
                            else:
                                out = re.sub('[\t]', '', data[0].decode())
                                out_1 = out.split('\n')[1]
                                out_n = out.split('\n')[out.split('\n').index('"." symb') + 2]

                                logging.debug('out_n: ' + out_n)

                                try:
                                    mtag_compound_lemma = re.search(r'\"(.*)\"', out_n).group(1)

                                    # Check for lemma correctness
                                    # if correct
                                    if lemma.lemma_ == mtag_compound_lemma:
                                        logging.debug('Compound word lemma correctness (spaCy IS EQUAL mtag): ' + mtag_compound_lemma + ' :')

                                        second_word = re.search(r'\<\+(.*)\>', out_1).group(1)
                                        # get second_word lemma spaCy
                                        doc_second_lemma = NLP_NB_LEMMA(second_word)
                                        spacy_second_word_lemma_arr = [token.lemma_ for token in doc_second_lemma]
                                        logging.debug('Compound word <second_lemma>: ' + spacy_second_word_lemma_arr[0])

                                        first_word = re.search(r'(.*)' + second_word, mtag_compound_lemma).group(1)
                                        # get first_word lemma mtag
                                        try:
                                            with open(destination_text_for_mtag, 'w') as f:
                                                f.write(first_word)
                                        except IOError as e:
                                            logging.error(e, exc_info=True)
                                            return abort(500)
                                        args = ["/tmp/mtag-master/mtag.py", destination_text_for_mtag]
                                        process = subprocess.Popen(args, stdout=subprocess.PIPE)
                                        data = process.communicate()
                                        out = re.sub('[\t]', '', data[0].decode())
                                        out_1 = out.split('\n')[1]
                                        mtag_first_word_lemma = re.search(r'\"(.*)\"', out_1).group(1)
                                        logging.debug('Compound word <first_lemma>: ' + mtag_first_word_lemma)

                                        # create <compound>
                                        new_compound_element = ET.Element('compound')
                                        first_word_element = ET.Element('first_lemma')
                                        first_word_element.text = mtag_first_word_lemma
                                        new_compound_element.append(first_word_element)
                                        second_word_element = ET.Element('second_lemma')
                                        second_word_element.text = spacy_second_word_lemma_arr[0]
                                        new_compound_element.append(second_word_element)
                                        new_item_element.append(new_compound_element)
                                    # if not correct
                                    else:
                                        logging.debug('Compound word lemma correctness (lemmas IS NOT EQUAL) spaCy | mtag: ' + lemma.lemma_ + ' | ' + mtag_compound_lemma)

                                        correct_lemma_element = new_item_element.find('lemma')
                                        correct_lemma_element.text = mtag_compound_lemma

                                        second_word = re.search(r'\<\+(.*)\>', out_n).group(1)
                                        # get second_word lemma spaCy
                                        doc_second_lemma = NLP_NB_LEMMA(second_word)
                                        spacy_second_word_lemma_arr = [token.lemma_ for token in doc_second_lemma]
                                        logging.debug('Compound word <second_lemma>: ' + spacy_second_word_lemma_arr[0])

                                        first_word = re.search(r'(.*)' + spacy_second_word_lemma_arr[0], mtag_compound_lemma).group(1)

                                        # get first_word lemma mtag
                                        try:
                                            with open(destination_text_for_mtag, 'w') as f:
                                                f.write(first_word)
                                        except IOError as e:
                                            logging.error(e, exc_info=True)
                                            return abort(500)
                                        args = ["/tmp/mtag-master/mtag.py", destination_text_for_mtag]
                                        process = subprocess.Popen(args, stdout=subprocess.PIPE)
                                        data = process.communicate()
                                        out = re.sub('[\t]', '', data[0].decode())
                                        out_1 = out.split('\n')[1]
                                        mtag_first_word_lemma = re.search(r'\"(.*)\"', out_1).group(1)
                                        logging.debug('Compound word <first_lemma>: ' + mtag_first_word_lemma)

                                        # create <compound>
                                        new_compound_element = ET.Element('compound')
                                        first_word_element = ET.Element('first_lemma')
                                        first_word_element.text = mtag_first_word_lemma
                                        new_compound_element.append(first_word_element)
                                        second_word_element = ET.Element('second_lemma')
                                        second_word_element.text = spacy_second_word_lemma_arr[0]
                                        new_compound_element.append(second_word_element)
                                        new_item_element.append(new_compound_element)
                                except AttributeError:
                                    logging.debug('Error while processing Word <' + lemma.lemma_ + '>. Maybe not compound word.')
                if 'pos' in req_data:
                    if req_data['pos'] == 'ud':
                        new_speech_element.text = lemma.pos_
                    elif req_data['pos'] == 'udkonspekt':
                        # relate the universal dependencies parts of speech with konspekt tags
                        new_speech_element.text = speech_dict_POS_tags[lemma.pos_]
                    elif req_data['pos'] == 'spacykonspekt':
                        # relate the spaCy parts of speech with konspekt tags
                        new_speech_element.text = speech_dict_POS_tags[lemma.tag_]
                    elif req_data['pos'] == 'spacy':
                        # spaCy Fine-grained part-of-speech.
                        # tag_map.py in https://github.com/explosion/spaCy/tree/master/spacy/lang
                        new_speech_element.text = lemma.tag_
                if 'pos' not in req_data:
                    # Coarse-grained part-of-speech from the Universal POS tag set.
                    # https://spacy.io/api/annotation#pos-tagging
                    new_speech_element.text = lemma.pos_
                new_item_element.append(new_speech_element)
                # create and append <pos>
                new_pos_element = ET.Element('pos')
                new_pos_element.text = str(lemma.idx+1)
                new_item_element.append(new_pos_element)

                # create and append <relate> and <rel_type>
                new_rel_type_element = ET.Element('rel_type')
                new_relate_element = ET.Element('relate')
                if lemma.dep_ == 'punct':
                    new_rel_type_element.text = 'K0'
                    new_relate_element.text = '0'
                    new_item_element.append(new_rel_type_element)
                    new_item_element.append(new_relate_element)
                else:
                    new_rel_type_element.text = lemma.dep_
                    new_item_element.append(new_rel_type_element)
                    new_relate_element.text = str(lemma.head.i+1)
                    new_item_element.append(new_relate_element)

                # create and append <group_n>
                new_group_n_element = ET.Element('group_n')
                new_group_n_element.text = '1'
                new_item_element.append(new_group_n_element)

                new_sentence_element.append(new_item_element)
            # create full <parce.xml> file structure
            root_element.append(new_sentence_element)
        return Response(ET.tostring(root_element, encoding='utf8', method='xml'), mimetype='text/xml')
    except Exception as e:
        logging.error(e, exc_info=True)
        return abort(500)
# --------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
    # default port = 5000
    app.run(host = '0.0.0.0')
