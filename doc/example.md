This file uses [markdown](http://en.wikipedia.org/wiki/Markdown) light weight markup language. A good
[reference](https://daringfireball.net/projects/markdown/basics) explains the basics. This file may be
converted to `html` with

     markdown2 api_doc.md > api_doc.html

Here is an example workflow image generated with `![a nice DAG image](./workflow.png "Example workflow"){: .scenter}`

![a nice DAG image](./workflow.png "Example workflow"){: .scenter}

The syntax, `![a nice DAG image](./workflow.png "Example workflow"){: .scenter}` is a looks a bit complicated,
but is just the optional text only view, the image and mouse over text and style. We could just use 
`(./workflow.png)` if we didnt want to style it.

This image is provided by the webserver and can be retrieved with

     GET <web_server>/graph/<work_uid>/png

or explicitly:

     curl -k --cert ../MPO\ Demo\ User.pem https://mpo.gat.com/mpo/graph/<work_uid>/png > workflow.png


Some support routes are

* `workflow`
* `dataobject`
* `activity`

This `html` file was generated with `python md_css_generator.py example.md mpo_doc.css example.html` and
requires markdown to be installed: `pip install markdown`.
