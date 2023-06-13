import logging
logging.basicConfig(encoding='utf-8', level=logging.DEBUG)
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    logger.info('starting shrimp station...')
    import controller
    import api
    import config
    api.app.run(
        host='0.0.0.0',
        debug=config.server.debug,
    )
