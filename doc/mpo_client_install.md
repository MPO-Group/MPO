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
