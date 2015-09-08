# Description of the MPO API version 1.0

## A list of example usages of the API
Examples below will quote the command line
syntax beginning with `mpo` and give the full response. The url field indicates the api 
route used. Note that using the command line option `--format=pretty` will produce nice
json output to the screen. In scripts, this option is generally not used and the default 
behavior is to return the bare UUID value or an error code.

* Getting a workflow UUID from an alias and vice-versa

     `mpo --format=pretty get workflow -p uid=37d86ba6-d4ad-4437-87a0-c62e3ba0263e`
   The response contains the composite sequence, type, and
   user. Together these form the composite id, /user/type/composite_seq

    ```json
     [
     {
        "username":"john",
        "description":"EFIT equilbrium. Testing mode coupling for COMSOL.  Resolving singular behavior near edges",
        "composite_seq":1,
        "user":{
            "username":"john",
            "lastname":"Wright",
            "userid":"6f0b016c-2952-4d8c-9876-a86f73a04808",
            "firstname":"John"
        },
        "time":"2014-11-07 16:19:27.646942",
        "uid":"37d86ba6-d4ad-4437-87a0-c62e3ba0263e",
        "type":"TORIC",
        "name":"r505"
     }
     ]
    ```

    The user does not have to construct the composite sequence (or alias)
    themselves though; the `alias` subroute of `workflow` will do that.
    `mpo --format=pretty get workflow/37d86ba6-d4ad-4437-87a0-c62e3ba0263e/alias `

    ```json
    {
    "alias":"john/TORIC/1",
    "uid":"37d86ba6-d4ad-4437-87a0-c62e3ba0263e"
    }
    ```

    Finally, if your friend told you the alias, you can use that to
    retrieve the workflow id.
   `mpo --format=pretty get workflow -p alias=john/TORIC/1`

* Adding a type to the ontology for use in a creating a workflow for a new code.

    GET uuid of workflow types in the ontology.
    term_id=\`mpo get ontology/term -p path=Workflow/Type\`

    ```json
    {
     "username":"mpodemo",
     "user_uid":"f223db41-d1c5-41db-b8af-fde6c0a16f76",
     "description":"Terms that describe the workflow types",
     "name":"Type",
     "specified":true,
     "units":null,
     "date_added":"2014-07-09 17:38:26.506827",
     "type":"string",
     "parent_uid":"58c19102-b1b7-4f8d-8202-18fde0a88bad",
     "uid":"ee39ae67-139e-433e-b666-441437faa413",
     "url":"https://mpo.psfc.mit.edu/api/v0/ontology/term?path=Workflow/Type"
    }
    ```

    POST a new type of workflow
    `mpo define TORLH -p $term_id -s -d "code for fullwave lower hybrid simulations" -t string`


* Setting the 'ratings' quality of a work flow.

    GET uuid of quality status.
    term_id=\`mpo get ontology/term -p path=Generic/Status/quality\`

    Result:
    ```json
    {
     "username":"mpodemo",
     "user_uid":"f223db41-d1c5-41db-b8af-fde6c0a16f76",
     "description":"Fitness of an object for a particular purpose",
     "name":"quality",
     "specified":true,
     "units":null,
     "date_added":"2014-09-04 14:22:44.350747",
     "type":"string",
     "parent_uid":"34f6f31b-45d2-460e-b557-7363107d8e93",
     "uid":"29a8a81a-a7f8-45ea-ac55-c960786ed5d6",
     "url":"https://mpo.psfc.mit.edu/api/v0/ontology/term?path=Generic/Status/quality"
    }
    ```


    Previous step shows the entry, but is not needed to actually set
    the value, you can just use the path. You do need the uuid of the
    workflow.

     wid=\`mpo get workflow -p alias=jwright/EFIT/4\`

    POST a rating
     `mpo --format=pretty ontology_instance $wid /Generic/Status/quality 1`


* Get the controlled vocabulary for a term.
  For example, to see valid values for a tracked code input or Status
  attribute, or to see what inputs can be tracked for a given code. We
  first pass the `path` argument to the `ontology/term` route to get
  the ID of that term.

  
     term_id=\`mpo get ontology/term -p path=Generic/Status/quality\`

     `mpo --format=pretty get ontology/term/$term_id/vocabulary`

* Data objects.
  Dataobjects have both their own entry as well as references to them
  in workflows known as instances. Given one, the other can be
  retrieved. It can be easy to get confused about them, though.

     `mpo --format=pretty get dataobject`

  Will retrieve a formatted list of all dataobjects in the database.

     `mpo --format=pretty get dataobject?instance`

  Will retrieve a formatted list of all dataobject instances in the database.


     `mpo add workflow_id parent_id --name=name --desc=desc --uri=uri`

  Is the way to add a dataobject to a workflow. If dataobjects are the
  first item added to a workflow then the parent_id is the same as the
  workflow_id. The uri is a resource identifier to retrieve the
  dataobject for future inspection. The uri may be whatever you want,
  but must be unique. An archive command which is extensible is
  provide to store dataobject and create persistent uri's for them.

     
* Grouping requests.
  Most routes support grouped requests by uid.

        mpo --format=pretty get metadata/c87ba801-8c0f-4cdd-bd2c-968849b03d19,a0168813-a75f-4bd7-89c3-358e909d8a15
  rather than two separate requests. The response is a dictionary of dictionaries keyed by `uuid`:


    ```json
    {
      "a0168813-a75f-4bd7-89c3-358e909d8a15":{
        "username":"d3dauto",
        "key_uid":"text",
        "user_uid":"84dd4463-23e0-4f85-b1d4-06d7aa7b36a9",
        "uid":"a0168813-a75f-4bd7-89c3-358e909d8a15",
        "parent_type":"activity",
        "value":"2013-06-05",
        "key":"compilation_date",
        "time":"2014-07-31 11:01:19.320238",
        "parent_uid":"8cca7ccd-bdd9-4df5-8bf1-1976a61b8db2"
    },
      "c87ba801-8c0f-4cdd-bd2c-968849b03d19":{
        "username":"d3dauto",
        "key_uid":"text",
        "user_uid":"84dd4463-23e0-4f85-b1d4-06d7aa7b36a9",
        "uid":"c87ba801-8c0f-4cdd-bd2c-968849b03d19",
        "parent_type":"dataobject",
        "value":"/link/efit/fitweight.dat",
        "key":"Fitting weight data",
        "time":"2014-07-31 11:01:16.925728",
        "parent_uid":"3be0813a-5f89-47d0-8f1b-4b932b824534"
     }
    }
    ```


     The ontology/instance route instead groups along the parent_uid query argument so that one may get a group 
     of ontology instances attached to different objects.



Some examples for language specific interfaces.

* python interface
  All command line methods have equivalents in the mpo_methods class found in mpo_arg.py:

    ```python
    #Setup mpo instance
    cert='/Users/jwright/Codes/mposvn/trunk/MPO Demo User.pem'
    api='https://mpo.psfc.mit.edu/test-api'
    m=mpo_arg.mpo_methods(api_url=api,cert=cert,debug=True)
    m.debug=False
    m.filter='json'
    #Use mpo methods with return object being a python dictionary
    #Omitting the filter will return Response object,r. Then dict is
    #gotten with r.json()
    wf=m.init(name="JCW Test Run",desc="example of using python interface to API.", wtype='EFIT')
    do_uid=m.add(wf['uid'],wf['uid'],name='input.txt', desc='An important input file', uri='file://my/home/dir/input.txt')
    step_uid=m.step(wf['uid'],do_uid['uid'],name='MonteCarlo',desc='do mc simulation')
    m.comment(step_uid['uid'],'A very good code')
    
    ```

* matlab interface

* idl interface

* c/c++ interface

* fortran interface
