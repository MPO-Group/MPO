# CLIENT INSTALLATION

For commandline and scripting tools, only the mpo_arg.py class
is needed. The only non standard python dependencies of this are requests.py and urllib3.py
These dependencies are provided in a virtual environment. For installation, 
the requirements are system installed python2.7 and the virtualenv package for python.
To install virtualenv, 
```
sudo pip install virtualenv
```
Alternatively, grab a known working copy from the mpo repo:
```
svn export https://www.psfc.mit.edu/mposvn/trunk/virtualenv.py
```
Then to install the client:

* setting up python environment

```    
cd $INSTALL_DIR
virtualenv mpo_env
source mpo_env/bin/activate
rm -rf mpo_env/bin/pip* mpo_env/lib/python2.7/site-packages/pip*
easy_install pip
pip install requests urllib3
``` 
* create user preferences directory
```
mkdir $HOME/.mpo
chown $USER:$USER $HOME/mpo
chmod 700 $HOME/.mpo
pushd $HOME/.mpo
svn export https://www.psfc.mit.edu/mposvn/trunk/mpo.conf
```
* add your certificate
```
cp path_to_key/my_key.pem .
```
* edit mpo.conf to specify your certificate and other preferences:
```
vim mpo.conf
```
* retrieve client (svn or copy from existing checkout) note, using export below does not create .svn and keep the pointer but allows retrieval of single files.
```
svn export https://www.psfc.mit.edu/mposvn/trunk/mpo.py
svn export https://www.psfc.mit.edu/mposvn/trunk/client/python/mpo_arg.py
```
* retrieve the python archive classes
```
svn export https://www.psfc.mit.edu/mposvn/trunk/client/python/mpo_ar_dataobject.py
svn export https://www.psfc.mit.edu/mposvn/trunk/client/python/mpo_ar_filesys.py
svn export https://www.psfc.mit.edu/mposvn/trunk/client/python/mpo_ar_mdsplus.py
svn export https://www.psfc.mit.edu/mposvn/trunk/client/python/mpo_ar_ptdata.py
svn export https://www.psfc.mit.edu/mposvn/trunk/client/python/mpo_ar_rsync.py
svn export https://www.psfc.mit.edu/mposvn/trunk/client/python/mpo_ar_wos.py
```
* should be done
```
alias mpo='/home/jwright/bin/mpo.py'
```
* Change the first line of mpo.py to point to your new python copy
 First line eg:   #!/usr/local/bin/mpo_env/bin/python
 you may also set mpo environment defaults here. Especially the
 default MPO api server and your MPO authorization.
```
vi mpo.py
```
* Try it out.  
* help on the mpo command

```
\$ mpo --help
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
\$
```
* get the users in the database

```
\# get the uuids of the users
\#
\$ mpo get user
\['ddc315a1-6310-41e7-a84d-886bc904f3b2', 'f223db41-d1c5-41db-b8af-fde6c0a16f76'\]

```

```
\# get the users full records as nicely formatted json
\#
\$ mpo --format pretty get user 
\[
    \{
        "username":"mpoadmin",
        "dn":null,
        "uid":"ddc315a1-6310-41e7-a84d-886bc904f3b2",
        "firstname":null,
        "lastname":null,
        "phone":null,
        "time":"2015-06-10 12:17:03.192294",
        "organization":null,
        "email":null
    \},
    \{
        "username":"mpodemo",
        "dn":"emailAddress=jas@psfc.mit.edu,CN=MPO Demo User,OU=PSFC,O=c21f969b5f03d33d43e04f8f136e7682,O=MIT,L=Cambridge,ST=Massachusetts,C=US",
        "uid":"f223db41-d1c5-41db-b8af-fde6c0a16f76",
        "firstname":"MPO",
        "lastname":"Demo User",
        "phone":null,
        "time":"2015-06-10 12:17:03.193528",
        "organization":"MIT",
        "email":"jas@psfc.mit.edu"
    \},
\]
\$ 
```
