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
def confor_service_3(args):
    try:
        logging.debug('Start SERVICE_3 execution ..................................................')
        projectDir = str(args['project_dir'])
        pathToConfor = os.path.join(projectDir, 'deploy', 'confor', 'Service3.jar')
        destinationTempXlsx = args['destination']
        destinationOutputXml = "/".join([tempfile.mkdtemp(),'output.xml'])
        destinationTaskResultFolder = '/var/tmp/tasks/confor/' + args['spooler_task_name']
        if args['find'] == 'find':
            args = ["java", '-jar', pathToConfor, destinationTempXlsx, 'Find$', destinationOutputXml]
        elif args['find'] == 'nofind':
            args = ["java", '-jar', pathToConfor, destinationTempXlsx, destinationOutputXml]
        logging.debug('ARGS: ' + str(args))
        # FIXME: Update with subprocess.run()
        try:
            code = subprocess.call(args, stdout=subprocess.DEVNULL)
            if code == 0:
                logging.debug("SERVICE_3 --> output.xml: Success!")
            else:
                logging.error("SERVICE_3 --> output.xml: Error!")
        except OSError as e:
            logging.error(e, exc_info=True)
            return uwsgi.SPOOL_IGNORE
        if not os.path.exists(destinationTaskResultFolder):
            try:
                os.makedirs(destinationTaskResultFolder, 0o755)
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise
        # copy output.xml file with results to unique folder with id
        try:
            shutil.move(destinationOutputXml, destinationTaskResultFolder)
        except Exception as e:
            logging.error(traceback.format_exc())
            # logging.error(repr(e))
            return uwsgi.SPOOL_IGNORE
        return uwsgi.SPOOL_OK
    except Exception as e:
        logging.error(traceback.format_exc())
        # logging.error(repr(e))
        return uwsgi.SPOOL_IGNORE