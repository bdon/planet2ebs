from setuptools import setup, find_packages

setup(name='planet2ebs',
      version='0.0.1',
      description='OSM to EBS importing tool.',
      author='Brandon Liu',
      author_email='bdon@bdon.org',
      url='http://github.com/bdon/planet2ebs',
      install_requires=['boto<3','fabric<2','requests<3'],
      packages=['planet2ebs'],
      package_data={
        'planet2ebs': ['example-mapping.json'],
      },
      license='MIT',
      entry_points={
        'console_scripts': [
            'planet2ebs=planet2ebs:main',
        ],
      })
