m=obj_new('mpo',host='https://mpo.psfc.mit.edu/api',version='v0',/debug)

;Start method takes name, description, workflow type
wf=m->start('GYRO-prep','idl test-final','Gyro' )

;Add method takes workflow id, parent id, name, description, uri
obj1=m->add(wf.uid,wf.uid,'Transp_Shot','Transp simulation number','12345')

;Make a URI for a filesys object so we can use it to create a data object
uri = archive_filesys(m, "/a/file/in/the/filesystem")

;Add method takes workflow id, parent id, name, description, uri
obj2=m->add(wf.uid,wf.uid,'EQDSK_params',uri)

;Make a URI for an mdsplus object so we can use it to create a data object
uri = archive_mdsplus(m, "alcdata.psfc.mit.edu", "cmod", 1090909009, '\IP')

;Add method takes workflow id, parent id, name, description, uri
obj2=m->add(wf.uid,wf.uid,'Plasma Current',uri)


;Step method takes workflow id, parent id, name, description, 
act1=m->step(wf.uid,obj1.uid,'Export','Save equilibrium','Transp-Export',inputs=[obj2.uid])

;Meta method takes target id, type, value
tmp=m->meta(wf.uid,'format','ascii')

;Comment method takes target id, text
tmp=m->comment(wf.uid,'A workflow created from IDL')

obj_destroy,m
end

