from setuptools import setup, find_packages

setup(name='planet2ebs',
      version='0.0.1',
      description='OSM to EBS importing tool.',
      author='Brandon Liu',
      author_email='bdon@bdon.org',
      url='http://github.com/bdon/planet2ebs',
      install_requires=['boto','fabric','requests'],
      packages=[],
      scripts=['planet2ebs.py'],
      data_files=[('share/planet2ebs', [''])],
      license='MIT')
