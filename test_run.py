import pytest
import objects

# a false Boto connection
class FakeConn():
  def __init__(self):
    self.attach_volumes = []

  def attach_volume(self,*args):
    self.attach_volumes.append(args)

class FakeFab():
  def __init__(self):
    self.sudos = []
    self.runs = []

  def sudo(self,cmd):
    self.sudos.append(cmd)

  def run(self,cmd):
    print "FAKE RUN "
    self.runs.append(cmd)

class FakeRequests():
  def head(self):
    pass

def test_urlparse_http():
  source = objects.PbfSource("http://example.com/foo/bar.pbf")
  assert source.scheme == 'http'

def test_urlparse_ebs():
  source = objects.PbfSource("ebs://vol-999/foo/bar.pbf")
  assert source.scheme == 'ebs'

def test_source_use_http():
  conn = FakeConn()
  fab = FakeFab()
  source = objects.PbfSource("http://example.com/foo/bar.pbf")
  with source.use(conn,fab,"i-999") as path:
    assert path == "/home/ubuntu/osm.pbf"

  assert fab.runs == ["curl -s -o /home/ubuntu/osm.pbf http://example.com/foo/bar.pbf"]
  assert fab.sudos == []

def test_source_use_ebs():
  conn = FakeConn()
  fab = FakeFab()
  assert fab.runs == []
  source = objects.PbfSource("ebs://vol-999/foo/bar.pbf")
  with source.use(conn,fab,"i-999") as path:
    assert path == "/mnt/pbfsource/foo/bar.pbf"

  assert fab.sudos == [
    "mkdir -p /mnt/pbfsource",
    "mount /dev/xvdh /mnt/pbfsource",
    "chown -R ubuntu:ubuntu /mnt/pbfsource",
    "umount /mnt/pbfsource"
  ]
  assert fab.runs == []

  assert conn.attach_volumes == [("vol-999","i-999","/dev/xvh")]


def test_source_sanitycheck_http():
  # this is untested
  pass

def test_source_sanitycheck_ebs():
  # this is untested
  pass

def test_source_artifacts_http():
  # assert that 1 EBS volume was created
  pass

