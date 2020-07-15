# load misc utils
import time, logging, sys, os, tempfile, subprocess
import traceback
import uwsgi
from uwsgidecorators import spool
import shutil, os, re, string

# logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.DEBUG)
# logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.ERROR)

@spool
def confor_task(args):
    try:
        logging.debug('Start task execution')
        # data size in bytes
        logging.debug('Data size in bytes: ' + str(len(args['body'])))
        projectDir = str(args['project_dir'])
        pathToConfor = os.path.join(projectDir, 'deploy', 'confor', 'Service3.jar')
        destinationTempXlsx = "/".join([tempfile.mkdtemp(),'xlsxFile.xlsx'])
        destinationOutputXml = "/".join([tempfile.mkdtemp(),'output.xml'])
        try:
             with open(destinationTempXlsx, 'wb') as tempXlsx:
                tempXlsx.write(args['body'])
        except IOError as e:
            logging.error(traceback.format_exc())
            # logging.error(repr(e))
            return uwsgi.SPOOL_IGNORE
        args = ["java", '-jar', pathToConfor, destinationTempXlsx, destinationOutputXml]
        try:
            code = subprocess.call(args, stdout=subprocess.DEVNULL)
            if code == 0:
                logging.debug("subprocess.call (confor --> output.xml): Success!")
            else:
                logging.error("subprocess.call (confor --> output.xml): Error!")
        except OSError as e:
            logging.error(e, exc_info=True)
            return abort(500)
        # copy output.xml file with results to unique folder with id
        try:
            shutil.copy2(destinationOutputXml, '/var/tmp/tasks/confor/' + args['spooler_task_name'])
        except Exception as e:
            logging.error(traceback.format_exc())
            # logging.error(repr(e))
            return uwsgi.SPOOL_IGNORE
        return uwsgi.SPOOL_OK
    except Exception as e:
        logging.error(traceback.format_exc())
        # logging.error(repr(e))
        return uwsgi.SPOOL_IGNORE