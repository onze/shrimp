import os
import shutil
import logging
logging.basicConfig(encoding='utf-8', level=logging.DEBUG)
logger = logging.getLogger(__name__)
import config


def silent_loggers():
    for name in (
        'werkzeug',
    ):
        logging.getLogger(name).setLevel(logging.WARNING)


def make_log_dir():
    log_dir = config.tmp_dir+'/logs'
    shutil.rmtree(log_dir, ignore_errors=True)
    os.makedirs(log_dir, exist_ok=True)


if __name__ == '__main__':
    logger.info('starting shrimp...')
    silent_loggers()
    make_log_dir()
    import api
    import commander
    commander.init(api.socketio_engine)
    import videofeed
    api.serve()
