from jnpr.junos import Device
from jnpr.junos.exception import *
from jnpr.junos.utils.config import Config
from lxml import etree

import sys
import yaml
import os
import git
import shutil
import time

nb=False

print("HOST:\t\tpreparing environment.")
fs=open('settings.yml','r')
settings = yaml.load(fs, Loader=yaml.FullLoader)
fs.close()

if os.path.isdir('./tmpwdc'):
    shutil.rmtree('./tmpwdc')

try:
    os.mkdir('./tmpwdc')
except FileExistsError as err:
    print ("ERROR:    "+str(err))
except:
    print ("ABORT!    "+str(sys.exc_info()[0]))
    sys.exit()

try:
    print("GIT:\t\ttrying to clone repo.")
    r = git.Repo.clone_from(settings['url'],'tmpwdc', branch=sys.argv[1])
    print("GIT:\t\trepo cloned..")
except Exception as err:
    if "Remote branch " + sys.argv[1] +" not found in upstream origin" in str(err):
        print("GIT:\t\tbranch does not exist. Exiting.")
        sys.exit()
    else:
        print(err)
        sys.exit()

missing=[]

for x in settings['devices']:
    if not os.path.isfile("tmpwdc/"+x['name']+".txt"):
        missing.append(x['name'])
if len(missing)>0:
    print("GIT:\t\terror, missing configuration files for these devices " + str(missing) + " . Exiting.")
    sys.exit()

for x in settings['devices']:
    print("JUNOS:\t\tconnecting to " + x['name'] + ".")
    dev = Device(host=x['ip'], user=x['usr'], password=x['pass'])
    dev.open(gather_facts=False)
    try:
        oldip=dev.rpc.get_interface_information(interface_name='fxp0', terse=True).xpath(".//ifa-local/text()")[0].replace('\n','')
    except:
        oldip=dev.rpc.get_interface_information(interface_name='em0', terse=True).xpath(".//ifa-local/text()")[0].replace('\n','')
    if "VMX" in dev.facts['RE0']['model']:
        fxp0="delete apply-groups\nset apply-groups global\nset interfaces fxp0 unit 0 family inet address " + oldip + "\nset system host-name " + x['name']
    if "VSRX" in dev.facts['RE0']['model']:
        fxp0="delete apply-groups\nset apply-groups global\nset interfaces fxp0 unit 0 family inet address " + oldip + "\nset system host-name " + x['name']
    if "QFX" in dev.facts['RE0']['model']:
        fxp0="delete apply-groups\nset apply-groups global\nset interfaces em0 unit 0 family inet address " + oldip + "\nset system host-name " + x['name']
    cfg = Config(dev)
    cfile = "tmpwdc/"+x['name']+".txt"
    try:
        cfg.load(path=cfile, format='text', overwrite=True)
    except ConfigLoadError as err:
        print(err)
    try:
        cfg.load(fxp0, format='set')
    except ConfigLoadError as err:
        print(err)
    if cfg.commit_check():
        if cfg.commit:
            print ("JUNOS:\t\tcommitting ")
            cfg.commit(timeout=300)
            print ("JUNOS:\t\tcommit completed")
        else:
            print ("JUNOS:\t\terror, commit failed")
    else:
        print ("JUNOS:\t\terror, commit check failed")
    dev.close()

