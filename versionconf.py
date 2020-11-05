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
        print("GIT:\t\tbranch does not exist. Creating new one.")
        r = git.Repo.init('tmpwdc')
        nb=True
    else:
        print(err)
        sys.exit()

for x in settings['devices']:
    print("JUNOS:\t\tconnecting to " + x['name'] + ".")
    dev = Device(host=x['ip'], user=x['usr'], password=x['pass'])
    dev.open(gather_facts=False)
    data = dev.rpc.get_config(options={'format':'set'})
    f = open("./tmpwdc/"+x['name']+'.set', 'w')
    f.write(str(etree.tostring(data, encoding='unicode')))
    f.close()
    data = dev.rpc.get_config(options={'format':'text'})
    f = open("./tmpwdc/"+x['name']+'.txt', 'w')
    f.write(str(etree.tostring(data, encoding='unicode')))
    f.close()
    dev.close()
    print("JUNOS:\t\tfiles created.")

r.index.add('*.set')
r.index.add('*.txt')
print("GIT:\t\tadd done.")
r.index.commit('Saved configurations for use-case ' + sys.argv[1] + '@ ' + time.ctime())
print("GIT:\t\tcommit done..")

if nb:
    r.git.branch(sys.argv[1])
    r.git.checkout(sys.argv[1])
    print("GIT:\t\tset new branch.")
    rm = r.create_remote('origin', url=settings['url'])
    print("GIT:\t\tconnected to remote repo.")

r.remotes.origin.push(sys.argv[1])
print("GIT:\t\tpush done.")
