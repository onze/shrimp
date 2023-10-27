import config
import pprint
import shelve
import logging
logger = logging.getLogger(__name__)

filename = f'{config.persisted_dir}/local_storage'

with shelve.open(filename) as datastore:
    logger.info(f'local_storage @ {filename}: {pprint.pformat({k:v for k,v in datastore.items()})}')

def load(key, default):
    with shelve.open(filename) as datastore:
        return datastore.get(key, default)


def save(key, value):
    with shelve.open(filename) as datastore:
        datastore[key] = value
        logger.info(f'localstorage["{key}"]={value}')