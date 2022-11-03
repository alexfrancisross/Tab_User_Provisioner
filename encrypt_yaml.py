from yaml.loader import SafeLoader
from cryptoyaml import generate_key, CryptoYAML
CONFIG='settings.yaml'
CONFIG_ENCRYPTED = 'settings.yaml.aes'
KEY = '.\key'
import yaml
import os

def read_yaml(file_path):
    with open(file_path) as f:
        data = yaml.load(f, Loader=SafeLoader)
    return data

def create_encrytpted_yaml():
    #if key does not exists
    if not (os.path.exists(KEY)):
        new_key = generate_key(KEY)
    config = CryptoYAML(CONFIG_ENCRYPTED,keyfile=KEY)
    return config

def write_encrypted_yaml(data, config):
    keys = data.keys()
    for key in keys:
        items = data[key]
        config.data[key] = data[key]
        for item in items:
           config.data[key][item] = data[key][item]
           print('item ' + key + ' : ' + item + ' written to encrypted yaml file')
    config.write()
    print('succesfully encrypted yaml file')

def read_encrypted_yaml(file_path):
    read = CryptoYAML(file_path, keyfile=KEY)
    print(read.data)
    return data

data=read_yaml(CONFIG)
config = create_encrytpted_yaml()
write_encrypted_yaml(data, config)
#read_encrypted_yaml(CONFIG_ENCRYPTED)