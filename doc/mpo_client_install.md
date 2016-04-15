# CLIENT INSTALLATION

For commandline and scripting tools, only the mpo_arg.py class
is strictly needed. The only non standard python dependencies of this are requests.py and urllib3.py
These dependencies are provided in a virtual environment. For installation, 
the requirements are system installed python2.7, pip,  and the virtualenv package for python.

* Grab a copy of the MPO distribution.
```
pushd /tmp
git clone https://github.com/MPO-Group/MPO.git
popd
```

* Install virtualenv if needed, 
```
sudo pip install virtualenv
```

* and set up python environment
```
cd <directory above desired install location>
mkdir MPO ; cd MPO
export MPO_ROOT=$PWD #or `setenv MPO_ROOT $PWD` as appropriate for your shell
virtualenv mpo_env
source mpo_env/bin/activate
pip install requests urllib3
deactivate #leave virtual environment - it will still work.
``` 

* create user preferences directory
```
mkdir $HOME/.mpo
chown $USER:$USER $HOME/mpo
chmod 700 $HOME/.mpo
pushd $HOME/.mpo
cp /tmp/MPO/mpo.conf .
```

* add your certificate as issued by MPO (or other CA supported by the mpo server you are using).
```
cp <path_to_key>/my_key.pem .
#optionally copy demo key.
cp "/tmp/MPO/MPO Demo User.pem" mpo_demo.pem
```

* edit mpo.conf to specify your certificate and other preferences:
```
vim mpo.conf
```

* install client source and option sub-classes for archiving actions.
```
popd  #should be back in $MPO_ROOT
cp /tmp/MPO/mpo.py .
cp /tmp/MPO/client/python/mpo*.py .
```

* Change the first line of mpo.py to point to your new python copy
 First line eg:   #!/home/user/mpo_env/bin/python
 you may also set mpo environment defaults here. Especially the
 default MPO api server and your MPO authorization.
```
vi $MPO_ROOT/mpo.py
```


* Finish up.
```
chmod +x $MPO_ROOT/mpo.py
alias mpo=$MPO_ROOT/mpo.py
rm -rf /tmp/MPO
```

* Try it out.  
* help on the mpo command

```
$ mpo --help
usage: mpo.py [-h] [--user USER] [--pass PASS]
              [--format {id,raw,text,json,dict,pretty} | --field FIELD]
              [--verbose] [--host HOST] [--dryrun]
              {get,post,delete,init,start_workflow,add,add_data,step,add_action,ontology_term,define,ontology_instance,add_metadata,metadata,annotate,archive,collect,ls,restore,comment,add_comment,meta,search}
              ...

MPO Command line API

positional arguments:
  {get,post,delete,init,start_workflow,add,add_data,step,add_action,ontology_term,define,ontology_instance,add_metadata,metadata,annotate,archive,collect,ls,restore,comment,add_comment,meta,search}
                        commands
    get                 GET from a route
    post                POST to a route
    delete              DELETE to a route
    init (start_workflow)
                        Start a new workflow
    add (add_data)      Add a data object to a workflow.
    step (add_action)   Add an action to a workflow.
    ontology_term (define)
                        Add a term to the vocabulary
    ontology_instance (add_metadata,metadata,annotate)
                        Add a term to the vocabulary
    archive             Archive a data object.
    collect             Create a new collection
    ls                  list the Archive of a data object.
    restore             restore the Archive of a data object.
    comment (add_comment)
                        Attach a comment an object.
    meta                Add metadata to a dataobject.
    search              SEARCH the MPO store

optional arguments:
  -h, --help            show this help message and exit
  --user USER, -u USER  Specify user.
  --pass PASS, -p PASS  Specify password.
  --format {id,raw,text,json,dict,pretty}, -f {id,raw,text,json,dict,pretty}
                        Set the format of the response.
  --field FIELD         Return a specific field to shell. EG "--field=uid" is
                        the same as "--format=id".
  --verbose, -v         Turn on debugging info
  --host HOST           specify API root URI
  --dryrun, -d          Show the resulting POST without actually issuing the
                        request

Metadata Provenance Ontology project
$
```
* get the users in the database

```
# get the uuids of the users
#
$ mpo get user
['ddc315a1-6310-41e7-a84d-886bc904f3b2', 'f223db41-d1c5-41db-b8af-fde6c0a16f76']

```

```
# get the users full records as nicely formatted json
#
$ mpo --format pretty get user 
[
    {
        "username":"mpoadmin",
        "dn":null,
        "uid":"ddc315a1-6310-41e7-a84d-886bc904f3b2",
        "firstname":null,
        "lastname":null,
        "phone":null,
        "time":"2015-06-10 12:17:03.192294",
        "organization":null,
        "email":null
    },
    {
        "username":"mpodemo",
        "dn":"emailAddress=jas@psfc.mit.edu,CN=MPO Demo User,OU=PSFC,O=c21f969b5f03d33d43e04f8f136e7682,O=MIT,L=Cambridge,ST=Massachusetts,C=US",
        "uid":"f223db41-d1c5-41db-b8af-fde6c0a16f76",
        "firstname":"MPO",
        "lastname":"Demo User",
        "phone":null,
        "time":"2015-06-10 12:17:03.193528",
        "organization":"MIT",
        "email":"jas@psfc.mit.edu"
    },
]
 
```
