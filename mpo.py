#!flask/bin/python
if __name__ == '__main__':
    import os, sys, inspect
 # realpath() with make your script run, even if you symlink it :)
 #cmd_folder = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0]))
 #if cmd_folder not in sys.path:
 #    sys.path.insert(0, cmd_folder)

 # use this if you want to include modules from a subforder
    cmd_subfolder = os.path.realpath(os.path.abspath(os.path.join(os.path.split(inspect.getfile( inspect.currentframe() ))[0],"client/python")))
    if cmd_subfolder not in sys.path:
        sys.path.insert(0, cmd_subfolder)

    from mpo_arg import mpo_cli

    mpo_version    = os.getenv('MPO_VERSION','v0')
    mpo_api_url    = os.getenv('MPO_HOST', 'https://localhost:8080/') #API_URL
    mpo_cert       = os.getenv('MPO_AUTH', '~/.mpo/mpo_cert')
    archive_host   = os.getenv('MPO_ARCHIVE_HOST', 'psfcstor1.psfc.mit.edu')
    archive_user   = os.getenv('MPO_ARCHIVE_USER', 'psfcmpo')
    archive_key    = os.getenv('MPO_ARCHIVE_KEY', '~/.mporsync/id_rsa')
    archive_prefix = os.getenv('MPO_ARCHIVE_PREFIX', 'mpo-persistent-store/')

    cli_app=mpo_cli(version=mpo_version, api_url=mpo_api_url, 
                    archive_host=archive_host, archive_user=archive_user, 
                    archive_key=archive_key, archive_prefix=archive_prefix, 
                    mpo_cert=mpo_cert)    
    result=cli_app.cli()

    print(result)
    

