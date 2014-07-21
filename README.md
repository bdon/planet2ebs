`ami` directory - builds the AMI used for these operations

`planet2ebs create -source-file=http://example.com/planet.osm.pbf -cache-volume -price=4 mapping.json`
`planet2ebs create -source-file=ebs://vol-234324234/planet.osm.obf mapping.json`
`planet2ebs provision -source-db=ebs://vol-123123/pgdata`
`planet2ebs cleanup`
