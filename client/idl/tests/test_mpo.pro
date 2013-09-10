mpo=obj_new('mpo',host='mpo-dev.psfc.mit.edu',port='8080',version='v0')

wf=mpo->start('Transp','idl test')

obj1=mpo->add(wf.uid,wf.uid,'Transp_Shot','Transp simulation number','12345')

act1=mpo->step(wf.uid,obj1.uid,'Export','Save equilibrium','Transp-Export')

tmp=mpo->meta(wf.uid,'format','ascii')

tmp=mpo->comment(wf.uid,'A workflow created from IDL')

obj_destroy,mpo
end

