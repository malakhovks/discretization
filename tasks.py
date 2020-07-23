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
        service3Path = os.path.join(projectDir, 'deploy', 'confor', 'Service3.jar')
        service3DestinationTempXlsx = args['destination']
        service3DestinationOutputXml = "/".join([tempfile.mkdtemp(),'output.xml'])
        destinationTaskResultFolder = '/var/tmp/tasks/confor/' + args['spooler_task_name']
        if args['find'] == 'find':
            service3Args = ["java", '-jar', service3Path, service3DestinationTempXlsx, 'Find$', service3DestinationOutputXml]
        elif args['find'] == 'nofind':
            service3Args = ["java", '-jar', service3Path, service3DestinationTempXlsx, service3DestinationOutputXml]
        logging.debug('SERVICE_3 ARGS: ' + str(service3Args))
        # FIXME: Update service_3 with subprocess.run()
        try:
            service_3 = subprocess.call(service3Args, stdout=subprocess.DEVNULL)
            if service_3 == 0:
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
            shutil.move(service3DestinationOutputXml, destinationTaskResultFolder)
        except Exception as e:
            logging.error(traceback.format_exc())
            # logging.error(repr(e))
            return uwsgi.SPOOL_IGNORE
        return uwsgi.SPOOL_OK
    except Exception as e:
        logging.error(traceback.format_exc())
        # logging.error(repr(e))
        return uwsgi.SPOOL_IGNORE

@spool
def confor_service_3_4(args):
    try:
        logging.debug('Start SERVICE_3 --> SERVICE_4 execution ..................................................')
        projectDir = str(args['project_dir'])
        service3Path = os.path.join(projectDir, 'deploy', 'confor', 'Service3.jar')
        service4Path = os.path.join(projectDir, 'deploy', 'confor', 'Service4.jar')
        service3DestinationTempXlsx = args['destination']
        service3DestinationOutputXml = "/".join([tempfile.mkdtemp(),'output.xml'])
        service4DestinationOutputXml = "/".join([tempfile.mkdtemp(),'output.xml'])
        destinationTaskResultFolder = '/var/tmp/tasks/confor/' + args['spooler_task_name']

        if args['find'] == 'find':
            service3Args = ["java", '-jar', service3Path, service3DestinationTempXlsx, 'Find$', service3DestinationOutputXml]
        elif args['find'] == 'nofind':
            service3Args = ['java', '-jar', service3Path, service3DestinationTempXlsx, service3DestinationOutputXml]

        logging.debug('SERVICE_3 --> SERVICE_4 ARGS: ' + str(service3Args))

        service4Args = ['java', '-jar', '-Xmx3g', service4Path, service3DestinationOutputXml, service4DestinationOutputXml]

        # FIXME: Update service_3 with subprocess.run()
        try:
            service_3 = subprocess.call(service3Args, stdout=subprocess.DEVNULL)
            if service_3 == 0:
                logging.debug("Step [SERVICE_3 --> output.xml]: Success!")
                try:
                    service_4 = subprocess.call(service4Args, stdout=subprocess.DEVNULL)
                    if service_4 == 0:
                        logging.debug("Step [SERVICE_3 --> SERVICE_4 --> output.xml]: Success!")
                    else:
                        logging.error("Step [SERVICE_3 --> SERVICE_4 --> output.xml]: Error!")
                except Exception as e:
                    logging.error(e, exc_info=True)
                    return uwsgi.SPOOL_IGNORE
            else:
                logging.error("Step [SERVICE_3 --> output.xml]: Error!")
        except Exception as e:
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
            shutil.move(service4DestinationOutputXml, destinationTaskResultFolder)
        except Exception as e:
            logging.error(traceback.format_exc())
            # logging.error(repr(e))
            return uwsgi.SPOOL_IGNORE
        return uwsgi.SPOOL_OK
    except Exception as e:
        logging.error(traceback.format_exc())
        # logging.error(repr(e))
        return uwsgi.SPOOL_IGNORE