A list of example usages of the API. Examples below will quote the command line
syntax beginning with `mpo` and give the full response. The url field indicates the api 
route used. Note that using the command line option `--format=pretty` will produce nice
json output to the screen. In scripts, this option is generally not used and the default 
behavior is to return the bare UUID value or an error code.

* Adding a type to the ontology for use in a creating a workflow for a new code.

    ##GET uuid of workflow types in the ontology.
    term_id=\`mpo get ontology/term -p path=Workflow/Type\`

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

    ##POST a new type of workflow
    mpo define TORLH -p $term_id -s -d "code for fullwave lower hybrid simulations" -t string


* Setting the 'ratings' quality of a work flow.

	##GET uuid of quality status.
	term_id = \`mpo get ontology/term -p path=Generic/Status/quality\`

    Result:
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

	Previous step shows the entry, but is not needed to actually set
    the value, you can just use the path. You do need the uuid of the
    workflow.

	wid=\`mpo get workflow alias=jwright/EFIT/4\`

    ##POST a rating
	`mpo --format=pretty ontology_instance -p vocabulary=/Generic/Status/quality 1`


* Get the controlled vocabulary for a term.
  For example, to see valid values for a tracked code input or Status
  attribute, or to see what inputs can be tracked for a given code.

  
 	term_id = \`mpo get ontology/term -p path=Generic/Status/quality\`
	`mpo --format=pretty get ontology/term/$term_id/vocabulary`
	
