# API Server Install

Requires postgres 9.3rc1
Install and add postgres bin directory to your path.

* make virtualenv
```
virtualenv -p python2.7 --no-setuptools mpo_env
```
* load virtualenv
```
source mpo_env/bin/activate
```
* check pip
```
pip -v
```
*install pip reliably, but have to delete pip first
```
rm -rf mpo_env/bin/pip* mpo_env/lib/python2.7/site-packages/pip*
curl --silent --show-error --retry 5 https://bootstrap.pypa.io/get-pip.py | python
#or maybe, this previous one doesn't work for me on my OSX box. get missing 'main' error. 
easy_install pip
#if you get error from zipimport and setuptools, try fresh install of setuptools
pip install -U setuptools
#or
wget https://bitbucket.org/pypa/setuptools/raw/0.8/ez_setup.py
python ez_setup.py
```
* install python packages in virtual env
```
pip install -r pip_list.txt
```
* enjoy
```
svn co https://www.psfc.mit.edu/mposvn/trunk mpo
export MPO_HOME=$PWD/mpo
cd $MPO_HOME
chmod 600 $MPO_HOME/*.key
\#below only if you want to run local copy of database
export PGDATA=$MPO_HOME/db/data 
mkdir $PGDATA
pg_ctl start -D $PGDATA

```
#Web Server Install
Needs pydot. pyparsing dependence broken in 2.x so do
```
pip install -Iv https://pypi.python.org/packages/source/p/pyparsing/pyparsing-1.5.7.tar.gz#md5=9be0fcdcc595199c646ab317c1d9a709
pip install pydot
```
