A list of example usages of the API. Examples below will quote the command line
syntax beginning with `mpo` and give the full response. The url field indicates the api 
route used. Note that using the command line option `--format=pretty` will produce nice
json output to the screen. In scripts, this option is generally not used and the default 
behavior is to return the bare UUID value or an error code.

* Adding a type to the ontology for use in a creating a workflow for a new code.

    ##GET uuid of workflow types in the ontology.
    term_id=\`mpo get -r ontology/term -p path=Workflow/Type\`

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
     "url":"https://mpo.psfc.mit.edu/api/ontology/term?path=Workflow/Type"
    }

    ##POST a new type of workflow
    mpo define TORLH -p $term_id -s -d "code for fullwave lower hybrid simulations" -t string


