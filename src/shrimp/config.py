'''
Loads config.yaml as this module's attributes, such that
```
import config
```
gets you a `config` object representing the root of that yaml file.
'''
import os
import munch
import yaml
import socket
import logging
logger = logging.getLogger(__name__)

this_dir = os.path.dirname(__file__)
with open(f'config.{socket.gethostname()}.yaml') as f:
    config = munch.Munch.fromDict(yaml.safe_load(f))
    assert config is not None

globals().update(config)

logger.debug(f'Config: {config.toDict()}')
