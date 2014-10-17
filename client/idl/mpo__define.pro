;+
; NAME:
;      MPO class
;
; PURPOSE:
;      Interface with the MPO RESTful API
;
;IDL implementation of mpo interface to RESTful API
;argument layout for mpo:
;post
;get
;add
;step
;start
;comment
;meta
;archive
;restore
;ls
;
; CATEGORY:
;      database, provenance, webtools
;
; CALLING SEQUENCE:
;      mpo=obj_new('mpo')
;
; INPUTS:
;      Per method.
;
;
; OPTIONAL INPUTS:
;
; KEYWORD PARAMETERS:
;
; OUTPUTS:
;
; OPTIONAL OUTPUTS:
;
; COMMON BLOCKS:
;      None
;
; SIDE EFFECTS:
;      None
;      chatty because procedures made by json converter continually
;      compiled, recommend setting !quiet=1 before running
;   
;
; RESTRICTIONS:
;      Needs web connection to server
;
; PROCEDURE:
;
; EXAMPLE:
;
; mpo=obj_new('mpo',host='mpo-dev.psfc.mit.edu',port='8080',version='v0')
;
; wf=mpo->start('Transp run','idl test', 'Transp')
;
; obj1=mpo->add(wf['uid'],wf['uid'],'Transp_Shot','Transp simulation number','12345')
;
; act1=mpo->step(wf['uid'],obj1['uid'],'Export','Save equilibrium','Transp-Export')
;
; tmp=mpo->meta(act1['uid'],'format','ascii')
;
; tmp=mpo->comment(wf['uid'],'A workflow created from IDL')
;
;
; MODIFICATION HISTORY:
;     J. Wright, March 2013 , MIT.
;        Initial version
;-



;Viewing contents of file '../idllib/astron/contrib/bhill/readstring.pro'
PRO READSTRING,Filename,Array,MAXLINE=maxline
;+
; NAME:                 readstring
;       
; PURPOSE:  Read text file into a string array.
;
; CATEGORY: Text processing
;
; CALLING SEQUENCE: readstring,filename,array
;
; INPUT ARGUMENTS:  
;       filename - input file name
;
; OUTPUT ARGUMENTS:
;       array - string array with contents of file
;
; INPUT KEYWORD PARAMETER:
;       maxline - maximum number of lines allowed; default=1000
;
; MODIFICATION HISTORY:
;   30 Jun. 1997 - Written.  RSH/HSTX
;   28 Jun. 2000 - Square bracket subscripts.  RSH
;-
IF n_elements(maxline) LT 1 THEN maxline=1000
array = strarr(maxline)
openr,lun,filename,/get_lun
line = ''
i=0
WHILE NOT eof(lun) DO BEGIN
    readf,lun,line
    array[i] = line
    i = i + 1
ENDWHILE
i = i - 1
array = array[0:i]
free_lun,lun
RETURN
END

;+
; NAME:
;    struct_to_json
;
; PURPOSE:
;    Convert a structure to JSON notation, & return it as a string.
;
; CALLING SEQUENCE
;    json = struct_to_json(structure,[map=map],[oned=oned])
;
; INPUTS:
;    structure - A single structure or an array of structures.
;
; OPTIONAL INPUTS:
;    map  - A two-dimensional string array.  This can be used to override
;           the default output tag names. For example, if you need
;           a mixed-case tag name in the output map=[['SQUARE','Square']]
;    oned - A one-dimensional string array. This is used to force
;           named substructures to be printed as arrays, even if they only
;           contain one element.
;
; OUTPUTS:
;    json - A string in JSON notation, or an array of strings, one for
;           each element of the input structure. Structure tags will be
;           converted to lowercase, unless overridden by the map input.
;
; NOTES:
;    There is an ambiguity in IDL for substructures, since structures are
;    never scalar.  So substructures that have only one element are converted
;    to sub-objects, rather than an array of sub-objects with one element.
;    This behaviour can be overridden with the oned keyword.
;
; PROCEDURES CALLED:
;
; REVISION HISTORY:
;    2011-06-07 Initial version by B. A. Weaver, NYU
;
; VERSION:
;    $Id$
;
;-
FUNCTION struct_to_json, structure, map=map, oned=oned
    ;
    ; Check the type
    ;
    IF SIZE(structure,/TYPE) NE 8 THEN $
        MESSAGE, 'Input structure must be of type STRUCT.'
    IF KEYWORD_SET(map) THEN BEGIN
        IF SIZE(map,/TYPE) NE 7 THEN $
            MESSAGE, 'map keyword must be of type STRING.'
        IF SIZE(map,/N_DIMENSIONS) NE 2 THEN $
            MESSAGE, 'map keyword must be a 2d STRING array.'
    ENDIF
    IF KEYWORD_SET(oned) THEN BEGIN
        IF SIZE(oned,/TYPE) NE 7 THEN $
            MESSAGE, 'oned keyword must be of type STRING.'
        IF SIZE(oned,/N_DIMENSIONS) NE 1 THEN $
            MESSAGE, 'oned keyword must be a 1d STRING array.'
    ENDIF
    ;
    ; Create the return array
    ;
    json = STRARR(N_ELEMENTS(structure))
    ;
    ; Create a meta-structure containing all the tag information
    ; name holds the tag name
    ; type holds the IDL type
    ; isobject is true (1B) if the tag appears to be some sort of object
    ; isarray is true (1B) if the tag is an array (1d only, please!)
    ; shape holds the length of the array
    ; delim holds the delimiter to use if the tag is an array
    ;
    names = TAG_NAMES(structure)
    n = N_TAGS(structure)
    meta = REPLICATE({name:'', type:0L, isobject:0B, isarray:0B, shape:0L, delim:''}, $
        N_TAGS(structure))
    FOR k = 0, n - 1 DO BEGIN
        meta[k].name = STRLOWCASE(names[k])
        IF KEYWORD_SET(map) THEN BEGIN
            wmap = WHERE(STRMATCH(map[0,*],names[k]),nmap)
            IF nmap GT 0 THEN meta[k].name = map[1,wmap]
        ENDIF
        IF STREGEX(meta[k].name,'_\$.+',/BOOLEAN) THEN meta[k].name = STRMID(meta[k].name,1)
        meta[k].type = SIZE(structure[0].(k),/TYPE)
        IF meta[k].type EQ 6 OR meta[k].type EQ 9 THEN $
            MESSAGE, 'Complex types are not supported!'
        IF meta[k].type EQ 10 OR meta[k].type EQ 11 THEN $
            MESSAGE, 'Pointer and object types are not supported!'
        ndim = SIZE(structure[0].(k),/N_DIMENSIONS)
        IF ndim GT 1 THEN $
            MESSAGE, 'Multi-dimensional structure tags are not (yet) supported!'
        IF ndim EQ 1 THEN BEGIN
            meta[k].shape = SIZE(structure[0].(k),/N_ELEMENTS)
            IF meta[k].type EQ 8 AND meta[k].shape EQ 1 THEN BEGIN
                IF KEYWORD_SET(oned) THEN BEGIN
                    woned = WHERE(STRMATCH(oned,names[k]),noned)
                    IF noned GT 0 THEN meta[k].isarray = 1B
                ENDIF
            ENDIF ELSE meta[k].isarray = 1B
            IF meta[k].type EQ 7 THEN BEGIN
                ;
                ; Is this an 'object'?
                ;
                IF STREGEX((structure[0].(k))[0],'^[a-z_]+\(',/BOOLEAN,/FOLD_CASE) THEN BEGIN
                    meta[k].delim = ','
                    meta[k].isobject = 1B
                ENDIF ELSE meta[k].delim = '","'
            ENDIF ELSE meta[k].delim = ','
        ENDIF ELSE BEGIN
            IF meta[k].type EQ 7 THEN BEGIN
                IF STREGEX(structure[0].(k),'^[a-z_]+\(',/BOOLEAN,/FOLD_CASE) THEN meta[k].isobject = 1B
            ENDIF
        ENDELSE
    ENDFOR
    ;
    ; Loop over structure
    ;
    FOR k = 0, N_ELEMENTS(structure) - 1 DO BEGIN
        json[k] = '{'
        FOR tag = 0, n - 1 DO BEGIN
            ;
            ; Add the tag name
            ;
            json[k] += '"'+meta[tag].name+'":'
            IF meta[tag].isarray THEN json[k] += '['
            IF meta[tag].type EQ 8 THEN BEGIN
                jj = struct_to_json(structure[k].(tag),map=map,oned=oned)
                IF meta[tag].isarray THEN jj = STRJOIN(jj,',')
                json[k] += jj
            ENDIF ELSE BEGIN
                IF meta[tag].type EQ 7 AND ~meta[tag].isobject THEN json[k] += '"'
                IF meta[tag].isarray THEN $
                    json[k] += STRJOIN(STRTRIM(STRING(structure[k].(tag)),2),meta[tag].delim) $
                ELSE $
                    json[k] += STRTRIM(STRING(structure[k].(tag)),2)
                IF meta[tag].type EQ 7 AND ~meta[tag].isobject THEN json[k] += '"'
            ENDELSE
            IF meta[tag].isarray THEN json[k] += ']'
            IF tag LT n-1 THEN json[k] += ','
        ENDFOR
        json[k] += '}'
    ENDFOR
    ;
    ; And finish
    ;
    RETURN, json
END


;+
; NAME:
;    json_to_struct
;
; PURPOSE:
;    Convert a string or array of strings JSON notation, & return it as
;    an IDL structure.
;
; CALLING SEQUENCE
;    structure = json_to_struct(json,[/nodelete])
;
; INPUTS:
;    json - A string or array of strings in JSON notation.
;
; OPTIONAL INPUTS:
;    nodelete - Do not remove any temporary files created.
;
; OUTPUTS:
;    structure - An IDL structure or array of structures.
;
; NOTES:
;    JSON keywords beginning with '$' (e.g., "$oid":) will be replaced with
;    '_$'.
;
;    Named structures cannot contain anonymous sub-structures, so we will not
;    attempt to create a named structure.
;
;    Integer and real values get converted to INT & FLOAT respectively,
;    which may result in loss of precision.
;
; PROCEDURES CALLED:
;
; REVISION HISTORY:
;    2011-06-07 Initial version by B. A. Weaver, NYU
;
; VERSION:
;    $Id$
;
;-
FUNCTION json_to_struct, json, nodelete=nodelete
    ;
    ; Check the type
    ;
    IF SIZE(json,/TYPE) NE 7 THEN $
        MESSAGE, 'Input JSON must be of type STRING'
    FOR k = 0, N_ELEMENTS(json) - 1 DO BEGIN
        ;
        ; Create a working copy of the string
        ;
        ; jj = STRCOMPRESS(STRTRIM(json[k],2))
       ;print,'json length',k
        jj = json[k]
        ;
        ; Search for (possibly hex) numbers in quotes.  IDL doesn't like
        ; hex numbers in double quotes, but is ok with them in single quotes
        ;
        WHILE STREGEX(jj,'"[0-9a-f]+"',/FOLD_CASE,/BOOLEAN) DO BEGIN
            o = STREGEX(jj,'"[0-9a-f]+"',/FOLD_CASE,LENGTH=l)
            STRPUT, jj, "'", o
            STRPUT, jj, "'", o+l-1
         ENDWHILE
        ;account for UUIDs with dashes - JCW 2013
        WHILE STREGEX(jj,'"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}"',/FOLD_CASE,/BOOLEAN) DO BEGIN
           o = STREGEX(jj,'"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}"',/FOLD_CASE,LENGTH=l)
           STRPUT, jj, "'", o
           STRPUT, jj, "'", o+l-1
        ENDWHILE
        ;
        ; Remove spaces between keywords & colons.
        ;
        WHILE STREGEX(jj, '"[^"]+" +:',/BOOLEAN) DO BEGIN
            o = STREGEX(jj, '"[^"]+" +:',LENGTH=l)
            nq = STRPOS(jj,'"',o+1)
            jj = STRMID(jj,0,nq+1)+STRMID(jj,STRPOS(jj,':',nq))
        ENDWHILE
        ;
        ; Find keywords of the form $foo.  These will be converted to _$foo
        ;
        WHILE STREGEX(jj, '"\$[^"]+":',/BOOLEAN) DO BEGIN
            o = STREGEX(jj, '"\$[^"]+":',LENGTH=l)
            jj = STRMID(jj,0,o+1)+'_'+STRMID(jj,o+1)
        ENDWHILE
        ;
        ; Search for keywords & remove quotes around them.
        ;
        WHILE STREGEX(jj, '"[^"]+":',/BOOLEAN) DO BEGIN
           o = STREGEX(jj, '"[^"]+":',LENGTH=l)
           STRPUT, jj, " ", o
           STRPUT, jj, " ", o+l-2
        ENDWHILE

                                ; apparently IDL is also unhappy with
                                ; date strings, so just convert all
                                ; double quotes
        jj=strjoin(strsplit(jj, '"', /extract), "'")
        ;
        ; Now we have string containing a valid IDL structure (in theory).
        ; Normally we would just EXECUTE() it, but EXECUTE() has a limit of
        ; 131 characters.
        ;
        ; PRINT, jj
        ; r = EXECUTE('str='+jj)
        ; IF r THEN BEGIN
        ;     IF ~KEYWORD_SET(structure) THEN structure = REPLICATE(str,N_ELEMENTS(json))
        ;     structure[k] = str
        ; ENDIF ELSE BEGIN
        ;     MESSAGE, 'Error converting string '+jj+' to structure!'
        ; ENDELSE
        ;
        ; Instead, we will write the data to a temporary function, then
        ; evaluate that function.
        ;
        ; First, modify the !PATH
        ;
        IF k EQ 0 THEN BEGIN
            dirsep = PATH_SEP()
            tmp = '/tmp'+dirsep+GETENV('USER')+dirsep+'pro'
            IF STRPOS(!PATH,tmp) LT 0 THEN BEGIN
                FILE_MKDIR, tmp
                IF ~FILE_TEST(tmp+dirsep+'IDL_NOCACHE') THEN $
                    SPAWN, ['touch', tmp+dirsep+'IDL_NOCACHE'], /NOSHELL
                pathsep = PATH_SEP(/SEARCH_PATH)
                !PATH = tmp + pathsep + !PATH
            ENDIF
            fname = 'jts_'+STRTRIM(STRING(ULONG64(SYSTIME(1))),2)
            filelist = FILE_SEARCH(tmp+dirsep+fname+'.pro',COUNT=nfile)
            WHILE nfile GT 0 DO BEGIN
                fname += 'x'
                filelist = FILE_SEARCH(tmp+dirsep+fname+'.pro',COUNT=nfile)
            ENDWHILE
            OPENW, unit,tmp+dirsep+fname+'.pro',/GET_LUN
            PRINTF, unit, 'FUNCTION '+fname
            PRINTF, unit, '    structure = [ $'
        ENDIF
        IF k EQ N_ELEMENTS(json) - 1 THEN eol = ']' ELSE eol = ', $'
        PRINTF, unit, jj+eol
    ENDFOR
    PRINTF, unit, '    RETURN, structure'
    PRINTF, unit, 'END'
    FREE_LUN, unit
    RESOLVE_ROUTINE, fname, /IS_FUNCTION
    structure = CALL_FUNCTION(fname)
    IF KEYWORD_SET(nodelete) THEN $
        MESSAGE, 'Created temporary file '+tmp+dirsep+fname+'.pro', /INF $
        ELSE FILE_DELETE, tmp+dirsep+fname+'.pro'
    RETURN, structure
END


Function debug_req, StatusInfo, ProgressInfo,    CallbackData
 print,statusinfo
 print,progressinfo
return, 1
end


Function get_payload,v1,v2,v3,v4,v5,v6,v7,v8,v9,v10,v11,v12,v13,v14,v15,v16,v17,v18,v19,v20
  ;hash and create_struct will ignore !NULL/{} but not <Undefined>
  ;but this doesn't work in 7.0, so do something ugly
                                ;note, the whole point of this routine
                                ;is to choose hash or create_struct
                                ;base on version. If we could just
                                ;depend on 8.2, it'd be easier
;we create a structure with repeated calls to create_struct, and
;convert to hash if we are using 8.2

  if n_elements(v1) eq 0 or n_elements(v2) eq 0 then begin
     print,"Must provide at least 2 arguments: 1 key and 1 value"
     return, create_struct(pay,'error',-1)
  endif
  pay=create_struct(v1,v2)
;a bit sloppy here. should do a return after each endif
  if n_elements(v3) ne 0 and n_elements(v4) ne 0 then begin
     pay=create_struct(pay,v3,v4)
  endif
  if n_elements(v5) ne 0 and n_elements(v6) ne 0 then begin
     pay=create_struct(pay,v5,v6)
  endif
  if n_elements(v7) ne 0 and n_elements(v8) ne 0 then begin
     pay=create_struct(pay,v7,v8)
  endif
  if n_elements(v9) ne 0 and n_elements(v10) ne 0 then begin
     pay=create_struct(pay,v9,v10)
  endif
  if n_elements(v11) ne 0 and n_elements(v12) ne 0 then begin
     pay=create_struct(pay,v11,v12)
  endif
  if n_elements(v13) ne 0 and n_elements(v14) ne 0 then begin
     pay=create_struct(pay,v13,v14)
  endif
  if n_elements(v15) ne 0 and n_elements(v16) ne 0 then begin
     pay=create_struct(pay,v15,v16)
  endif
  if n_elements(v17) ne 0 and n_elements(v18) ne 0 then begin
     pay=create_struct(pay,v17,v18)
  endif
  if n_elements(v19) ne 0 and n_elements(v20) ne 0 then begin
     pay=create_struct(pay,v19,v20)
  endif

  if float(!VERSION.release) ge 8.2 then pay=hash(pay)
  
  return, pay
end

FUNCTION mpo::get, route, args
 if n_elements(route) eq 0 then return,self.error.get_route
 sargs='?'
 if self.debug eq 1 then print,'GET', n_elements(args), args
 if n_elements(args) eq 0 then begin
    args='' 
 endif else begin
    ;add arguments
   for i = 0,n_elements(args)-1 do begin
       sargs=sargs+args[i]
       if i lt n_elements(args)-1 then sargs=sargs+'&'
    endfor
 endelse

 url=self.mpo_host+'/'+self.mpo_version+'/'+route

 ;self.req->SetProperty, URL_QUERY=args ;wants a scalar?
 ;self.req->SetProperty, URL_PATH= url  

 url=url+sargs

;make query
 ;resp=string(self.req->GET(/BUFFER))
 ;Close your eyes, this is ugly. IDL cannot use personal certificates
 ;print,'Making query GET ',url
 a='""'
 b='"Null"' 
 q="curl -s -k  --cert '" +self.MPO_AUTH+ "' " + url 
 q=q+' --header "ACCEPT : application/json" '
 ;replace null records and empty strings with "Null"
 q=q+ "| sed 's/"+a+"/"+b+"/g' |sed 's/null/"+b+"/g' "

 if self.debug eq 1 then print,'MPO.GET, curl query',q
 spawn,q,str_resp
;return a structure or list of structures even when using hashes internally
;Convert json response to an idl structure
 if float(!VERSION.release) ge 8.2 then begin
    res=JSON_PARSE( str_resp  ) ;, /TOSTRUCT )
    if typename(res) eq 'LIST' then begin
        for i=0,n_elements(res)-1 do begin
            res[i]=res[i].tostruct;() ;uncomment for 8.2
        endfor
    endif else res = res.tostruct;() ;uncomment for 8.2
    ;print,'get',string(self.req->GET(/BUFFER))
 endif else res=json_to_struct(str_resp)
 
 return, res
end

FUNCTION mpo::post, route, payload
 if n_elements(payload) eq 0 then return,self->error('post_payload')
 if n_elements(route) eq 0 then return,self->error('post_route')
;route is a string
;payload should be a IDL STRUCT
 url=self.mpo_host+'/'+self.mpo_version+'/'+route
 self.req->SetProperty, URL_PATH= self.mpo_version+'/'+route
 self.req->SetProperty, HEADERS=self.POSTheaders

;problem with structures, tags are always upper case 
 if self.debug eq 1 then help,/st,payload
;Convert json response to an idl structure
 if (!VERSION.release) ge 8.2 then begin
    json=JSON_SERIALIZE(payload)
 endif else json=struct_to_json(payload)

 ;r=self.req->PUT(json,/BUFFER,/POST)  ;puts it into file 'r'

 q="curl -s -k -X 'POST' --cert '" +self.MPO_AUTH+ "' " + url 
 q=q+ " -d '"+json+"'"
 q=q+ ' --header "content-type: application/json" '
 if self.debug eq 1  then print,'MPO.POST, curl query',q
 spawn,q,r

 ;readstring,r,res
 res=r

;return a structure or list of structures even when using hashes internally
 if float(!VERSION.release) ge 8.2 then begin ;was 8.2
    res = JSON_PARSE(res);,/tostruct)
    if typename(res) eq 'LIST' then begin
        for i=0,n_elements(res)-1 do begin
            res[i]=res[i].tostruct;() ;uncomment for 8.2
        endfor
    endif else res = res.tostruct;()  ;uncomment for 8.2
 endif else  res=json_to_struct(res)

 return, res 
end

;+
; NAME:
;      mpo::start
;
; PURPOSE:
;      Interface with the MPO RESTful API
;
;        The INIT method starts a workflow.
;        It returns the server response for a new workflow.
;        URL should be the host root.
;        Syntactic sugar, alias for post
;        args are <url>,--name,--description

;-


FUNCTION mpo::start, name, description, type ;because IDL uses 'init' for class initialization
  payload = get_payload("name",name,"description",description,"type",type)

  
  Res = self->post(self.workflow_rt, payload)
  return, res
end

FUNCTION mpo::add , workflow_uid, parent_uid, name, description, uri

 parent_uid = [parent_uid]
 payload =   get_payload($
                                  self.workid,workflow_uid,$
                                  self.parentid,parent_uid,$
                                  "name",name,"description",description,$
                                  "uri",uri   )
 res = self->post(self.dataobject_rt, payload)
 return, res
end

FUNCTION mpo::step , workflow_uid, parent_uid, name, description, uri, inputs=inputs

 input_objs=[parent_uid]
 if keyword_set(inputs) ne 0 then input_objs = [ inputs, input_objs ]

 payload =   get_payload($
                                  self.workid,workflow_uid,$
                                  self.parentid,[input_objs],$
                                  "name",name,"description",description,$
                                  "uri",uri   )
 res = self->post(self.activity_rt, payload)
 return, res
end

FUNCTION mpo::comment, parent_uid, text
 payload =   get_payload($
                                  self.parentid,parent_uid,$
                                  "content",text)
 res = self->post(self.comment_rt, payload)
 return, res
end

FUNCTION mpo::meta , parent_uid, key, value
 payload =   get_payload($
                                  self.parentid,parent_uid,$
                                  "key",key, "value",value) 
 res = self->post(self.metadata_rt, payload)
 return, res
end


FUNCTION mpo::error, key

  ERRORSTR = create_struct($
              'get_route','{"error":"1", "message":"Invalid Route"}',$
              'post_route','{"error":"2", "message":"Invalid Route"}',$
              'post_payload','{"error":"3", "message":"Payload missing"}',$
              'unsupported_archive_protocol', $
	      '{"error":"4", "message":"The archive protocol must be one of (mdsplus,filesys)"}'$
                          )
  tnames=tag_names(errorstr)
  tindex=where( strcmp(tnames,strupcase(key) ) eq 1)
  return, errorstr.(tindex[0])
end

PRO mpo::cleanup
 obj_destroy,self.req
 return
end

FUNCTION mpo::archive_mdsplus, server, tree, shot, path
  return, self->archive('mdsplus', {server:server, tree:tree, shot:shot, path:path})
end

FUNCTION mpo::archive_filesys, filespec
  return, self->archive('filesys', {filespec:filespec})
end

FUNCTION mpo::archive, protocol, arg_struct
  if protocol eq 'mdsplus' then begin
    return, string(arg_struct.server, arg_struct.tree, $
		arg_struct.shot, arg_struct.path, $ 
		format='(%"mdsplus://%s/%s/%d&path=%s")') 
  endif else if protocol eq 'filesys' then begin
      return, string(arg_struct.filespec, format='(%"filesys:///%s")')
  endif else begin
    return, self->error('unsupported_archive_protocol')
  endelse
end

FUNCTION mpo::init , host=host, version=version, cert=cert, debug=debug

 if not keyword_set(host)    then host='mpo.psfc.mit.edu'
;;just put port in host name; if not keyword_set(port)    then port='443'
 if not keyword_set(version) then version='v0'
 if not keyword_set(cert) then cert='./MPO Demo User.pem'
 self.debug=0
 if keyword_set(debug) then self.debug=1

 self.POSTheaders = "content-type:application/json"
 self.GETheaders= "ACCEPT:application/json"
 self.ID='uid'
 self.WORKID='work_uid'
 self.PARENTID='parent_uid'
 self.MPO_VERSION=version
 self.WORKFLOW_RT = 'workflow'
 self.COMMENT_RT  = 'comment'
 self.METADATA_RT = 'metadata'
 self.DATAOBJECT_RT='dataobject'
 self.ACTIVITY_RT=  'activity'
 self.MPO_HOST=host
 self.MPO_AUTH=cert

; self.ERROR.get_route='{"error":"1", "message":"Invalid Route"}'
 self.req=OBJ_NEW('IDLnetUrl')
; uncomment for debugging
 self.req->SetProperty, CALLBACK_FUNCTION='debug_req'
 self.req->SetProperty, URL_PORT=port
 self.req->SetProperty, URL_SCHEME='https' ;important
 self.req->SetProperty, HEADERS=self.POSTheaders
 self.req->Setproperty, URL_HOST=host
 self.req->Setproperty, SSL_VERSION=3

;; For when authentication is implemented
 self.req->Setproperty, SSL_CERTIFICATE_FILE=cert
 self.req->Setproperty, SSL_VERIFY_HOST=0
 self.req->Setproperty, SSL_VERIFY_PEER=0
; self.req->Setproperty, URL_PASSWORD=''
; self.req->Setproperty, URL_USERNAME=''

 return,1
end


;This needs to go last so other methods are loaded.
PRO mpo__define
 void = { mpo, req:OBJ_NEW(), $
          POSTheaders:'', GETheaders:'',ID:'',WORKID:'',PARENTID:'',$
          MPO_VERSION:'',WORKFLOW_RT:'', COMMENT_RT:'',METADATA_RT:'', $
          DATAOBJECT_RT:'',ACTIVITY_RT:'',MPO_HOST:'',MPO_AUTH:'', $
          DEBUG:0 $
        }

 return
end

;          { $
;        get_route:'{"error":"1", "message":"Invalid Route"}',$
;        post_route:'{"error":"2", "message":"Invalid Route"}',$
;        post_payload:'{"error":"3", "message":"Payload missing"}'$
;          }$
