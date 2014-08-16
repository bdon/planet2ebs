from urlparse import urlparse
import requests
import os, shutil
import time
import math

def waitForState(obj, s):
  status = obj.update()
  while status != s:
    time.sleep(10)
    status = obj.update()
  return

class PbfSourceHttpCm(object):
  def __init__(self,source,fab):
    self.source = source
    self.fab = fab

  def __enter__(self):
    self.fab.run("curl -s -o /home/ubuntu/osm.pbf {0}".format(self.source.url))
    return "/home/ubuntu/osm.pbf"

  def __exit__(self,type,value,traceback):
    pass

class PbfSourceEbsCm(object):
  def __init__(self,source,conn,fab,instance_id,mountname):
    self.source = source
    self.fab = fab
    self.conn = conn
    self.instance_id = instance_id
    self.vol = None
    self.mountname = mountname

  def __enter__(self):
    self.vol = self.conn.get_all_volumes([self.source.netloc])[0]
    self.vol.attach(self.instance_id, "/dev/sdh")
    waitForState(self.vol, 'in-use')
    self.fab.sudo("mkdir -p /mnt/" + self.mountname)
    time.sleep(10) # Why???
    self.fab.sudo("mount /dev/xvdh /mnt/" + self.mountname)
    self.fab.sudo("chown -R ubuntu:ubuntu /mnt/" + self.mountname)
    return "/mnt/" + self.mountname + self.source.path

  def __exit__(self,type,value,traceback):
    self.fab.sudo("umount /mnt/" + self.mountname)
    print "Detaching volume"
    if self.vol:
      self.vol.detach()
      waitForState(self.vol, "available")

class PbfSource(object):
  def __init__(self,s):
    p = urlparse(s)
    self.path = p.path
    self.scheme = p.scheme
    self.url = s
    self.netloc = p.netloc

  # returns a context manager to prepare/teardown the source.
  def use(self,conn,fab,instance_id):
    if self.scheme == "http":
      return PbfSourceHttpCm(self,fab)
    elif self.scheme == "ebs":
      return PbfSourceEbsCm(self,conn,fab,instance_id,"pbfsource")

  def artifacts(self):
    pass

  def size(self,conn):
    if self.scheme == 'http':
      resp = requests.head(self.url)
      if resp.status_code == 200:
        size_bytes = int(resp.headers['content-length'])
        return int(math.ceil(size_bytes / 1000.0 / 1000.0 / 1000.0))
      else:
        raise Exception("File does not exist")
    if self.scheme ==  'ebs':
      vol = conn.get_all_volumes([self.netloc])[0]
      if vol.update() == "available":
        return vol.size
      else:
        raise Exception("Volume is not available.")

# Untested below this.

class Instance:
  def __init__(self,conn,timestamp,tags={}):
    self.timestamp = timestamp
    self.conn = conn
    self.tags= tags

  def __enter__(self):
    print("Preparing ec2 instance...")
    tmpnam = "planet2ebs-{0}".format(self.timestamp)
    self.kp = self.conn.create_key_pair(tmpnam)
    self.kp.save(".")
    self.sg = self.conn.create_security_group(tmpnam,"Temporary security group for planet2ebs")
    self.conn.authorize_security_group(group_name=tmpnam,from_port=22,to_port=22,cidr_ip="0.0.0.0/0",ip_protocol="tcp")
    self.conn.authorize_security_group(group_name=tmpnam,from_port=5432,to_port=5432,cidr_ip="0.0.0.0/0",ip_protocol="tcp")
    reservation = self.conn.run_instances('ami-8393d6b3', instance_type="t1.micro", key_name=tmpnam,security_groups=[tmpnam])
    instance = reservation.instances[0]
    print('Waiting for instance to start...')
    waitForState(instance, 'running')
    for k,v in self.tags.iteritems():
      instance.add_tag(k,v)
    self.instance = instance
    return instance

  def __exit__(self,type,value,traceback):
    print("Terminating instance")
    self.conn.terminate_instances(instance_ids=[self.instance.id])
    waitForState(self.instance, 'terminated')
    self.sg.delete()
    self.kp.delete()
    os.remove("planet2ebs-{0}.pem".format(self.timestamp))

class EbsArtifact(object):
  def __init__(self,mountpoint,vol_id):
    self.vol_id = vol_id
    self.mountpoint = mountpoint

  def output(self):
    return self.vol_id

# one or more of these created each run.
class NewArtifact(object):
  def __init__(self, conn, instance, fab, size,name,tags={}):
    self.instance = instance
    self.fab = fab
    self.conn = conn
    self.mountpoint = "/mnt/" + name
    self.tags = tags
    self.size = size

  def __enter__(self):
    self.vol = self.conn.create_volume(self.size, self.instance.placement)
    waitForState(self.vol, 'available')
    self.vol.attach(self.instance.id, '/dev/sdg')
    for k,v in self.tags.iteritems():
      self.vol.add_tag(k,v)
    waitForState(self.vol, 'in-use')
    time.sleep(10) # Why???
    self.fab.sudo("mkfs -t ext4 /dev/xvdg > /dev/null")
    self.fab.sudo("mkdir -p " + self.mountpoint)
    self.fab.sudo("mount /dev/xvdg " + self.mountpoint)
    self.fab.sudo("chown -R ubuntu:ubuntu " + self.mountpoint)
    return EbsArtifact(self.mountpoint,self.vol.id)

  def __exit__(self,type,value,traceback):
    self.fab.sudo("service postgresql stop") # idempotent
    self.fab.sudo("umount " + self.mountpoint)
    print "Detaching volume"
    self.vol.detach()
    waitForState(self.vol, "available")

