m=obj_new('mpo',host='https://mpo.psfc.mit.edu/api',version='v0')
;m=obj_new('mpo',host='https://charon.psfc.mit.edu:8080/api',version='v0')

;Start method takes name, description, workflow type
wf=m->start('GYRO-prep','idl test-final','Gyro' )

;Add method takes workflow id, parent id, name, description, uri
obj1=m->add(wf.uid,wf.uid,'Transp_Shot','Transp simulation number','12345')

;Step method takes workflow id, parent id, name, description, 
act1=m->step(wf.uid,obj1.uid,'Export','Save equilibrium','Transp-Export')

;Meta method takes target id, type, value
tmp=m->meta(wf.uid,'format','ascii')

;Comment method takes target id, text
tmp=m->comment(wf.uid,'A workflow created from IDL')

obj_destroy,m
end

