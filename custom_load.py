#! /usr/bin/python

'''Import Required Modules'''
from jnpr.junos import Device
from jnpr.junos.exception import *
from jnpr.junos.utils.config import Config

import time
import re
import sys
import yaml


fh=open('custom_input.txt','r')
hosts = yaml.load(fh, Loader=yaml.FullLoader)

for x in hosts:
    if x['conf']=="":
        print('Skip '+x['name'])
        continue
    '''Connect to device'''
    print ("Connecting to "+x['name'])
    dev = Device(host=x['ip'], user="root", password="Embe1mpls")
    dev.open(gather_facts=False)
    cfg = Config(dev)
    try:
        cfg.load(x['conf'], format='set')
    except ConfigLoadError as err:
        print(err)
    if cfg.commit_check():
        if cfg.commit:
            print ('Committing...')
            cfg.commit(timeout=300)
            print ('Successfully Committed')
        else:
            print ('Commit Failed')
    else:
        print ('Commit Check Failed')
    dev.close()
