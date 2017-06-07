## Shipyard Airflow ##

A python REST workflow orchestrator

To run:

```
$ virtualenv -p python2.7 /var/tmp/shipyard
$ . /var/tmp/shipyard/bin/activate
$ python setup.py install
$ uwsgi --http :9000 -w shipyard_airflow.shipyard --callable shipyard -L
```
