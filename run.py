import boto.ec2
from urlparse import urlparse
from boto.ec2.connection import EC2Connection
from boto.ec2.blockdevicemapping import BlockDeviceType
from boto.ec2.blockdevicemapping import BlockDeviceMapping
from fabric.api import run, env, sudo
from fabric.network import disconnect_all

import time
import shutil
import sys
import os
import time
import traceback

try:
   os.environ["AWS_ACCESS_KEY_ID"]
   os.environ["AWS_SECRET_ACCESS_KEY"]
except KeyError:
   print "Please set the environment variable FOO"
   sys.exit(1)

def waitForState(obj, s):
  status = obj.update()
  while status != s:
    time.sleep(10)
    status = obj.update()
    print status
  print "Done:"
  print status
  return

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else: raise

conn = boto.ec2.connect_to_region("us-west-2",
  aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
  aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"]
)

#print urlparse("ebs://vol-324234324/data/foo.pbf")
print "Creating temporary keypair..."

instance = None
vol = None
kp = None
sg = None

try:
  kp = conn.create_key_pair("planetebs")
  mkdir_p("temp")
  kp.save("temp")

  sg = conn.create_security_group("planetebs","temp")
  conn.authorize_security_group(group_name="planetebs",from_port=22,to_port=22,cidr_ip="0.0.0.0/0",ip_protocol="tcp")

  reservation = conn.run_instances('ami-b5a9d485', instance_type="r3.large", key_name="planetebs",security_groups=["planetebs"])
  instance = reservation.instances[0]
  print('Waiting for instance to start...')
  waitForState(instance, 'running')

  vol = conn.create_volume(30, instance.placement)
  waitForState(vol, 'available')
  print "Volume state"
  vol.attach(instance.id, '/dev/sdh')
  waitForState(vol, 'in-use')

  host_string =  "ubuntu@{0}".format(instance.public_dns_name)
  env.host_string = host_string
  env.key_filename = "temp/planetebs.pem"
  env.connection_attempts = 5
  run("ls -lah")
  sudo("mkdir -p /mnt/planet")
  sudo("mkfs -t ext4 /dev/xvdh")
  sudo("mount /dev/xvdh /mnt/planet")
  run("df -h /mnt/planet")
except:
  traceback.print_exc()
finally:
  print "Closing Connections"
  disconnect_all()
  if instance:
    print "Terminating instance"
    conn.terminate_instances(instance_ids=[instance.id])
    waitForState(instance, 'terminated')
  if sg:
    print "Deleting security group"
    sg.delete()
  if kp:
    print "Deleting remote keypair"
    kp.delete()
    print "Removing local keypair"
    shutil.rmtree("temp")
