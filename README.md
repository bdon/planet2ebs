planet2ebs - runs OpenStreetMap rendering databases for cheap on amazon.



`ami` directory - builds the AMI used for these operations

`planet2ebs http://example.com/planet.osm.pbf`
`planet2ebs http://example.com/planet.osm.pbf mapping.json`
`planet2ebs ebs://vol-234324234/planet.osm.pbf mapping.json`
`planet2ebs start ebs://vol-123123/pgdata`
`planet2ebs stop ebs://vol-123123/pgdata`

start/stop:
ensure that the render user exists with the given password
use pg_ctl to start the cluster.

after running db, you will be able to connect to the psql database like this:
psql 

`planet2ebs cleanup`

Build artifact: 
ebs://


# use the Main cluster instead, changing postgresql.conf


["i2.xlarge",{'/mnt/xvdf','}]
import on instancestore
otherwise need 2 ebs volumes

