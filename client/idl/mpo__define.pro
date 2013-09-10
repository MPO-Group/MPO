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
; wf=mpo->start('Transp','idl test')
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
  if !VERSION.release ge 8.2 then begin
     pay=hash(v1,v2,v3,v4,v5,v6,v7,v8,v9,v10,v11,v12,v13,v14,v15,v16,v7,v18,v19,v20)
  endif else pay=create_struct(v1,v2,v3,v4,v5,v6,v7,v8,v9,v10,v11,v12,v13,v14,v15,v16,v17,v18,v19,v20)
  return, pay
end

FUNCTION mpo::get, route, args
 if n_elements(args) eq 0 then args=''
 if n_elements(route) eq 0 then return,self.error.get_route
 self.req->SetProperty, URL_QUERY=args
 self.req->SetProperty, URL_PATH= self.mpo_version+'/'+route

;return a structure or list of structures even when using hashes internally
;Convert json response to an idl structure
 if !VERSION.release ge 8.2 then begin
    res=JSON_PARSE( string(self.req->GET(/BUFFER)) ) ;, /TOSTRUCT )
    if typename(res) eq 'LIST' then begin
        for i=0,n_elements(res)-1 do begin
            res[i]=res[i].tostruct()
        endfor
    endif else res = res.tostruct()
    ;print,'get',string(self.req->GET(/BUFFER))
 endif else res=json_to_struct(string(self.req->GET(/BUFFER)))
 
 return, res
end

FUNCTION mpo::post, route, payload
 if n_elements(payload) eq 0 then return,self->error('post_payload')
 if n_elements(route) eq 0 then return,self->error('post_route')
;route is a string
;payload should be a IDL STRUCT

 self.req->SetProperty, URL_PATH= self.mpo_version+'/'+route
 self.req->SetProperty, HEADERS=self.POSTheaders

;problem with structures, tags are always upper case 
; print,'post ',payload
; help,/st,payload
;Convert json response to an idl structure
 if !VERSION.release ge 8.2 then begin
    json=JSON_SERIALIZE(payload)
 endif else json=struct_to_json(payload)

 r=self.req->PUT(json,/BUFFER,/POST)
 readstring,r,res

;return a structure or list of structures even when using hashes internally
 if !VERSION.release ge 8.2 then begin ;was 8.2
    res = JSON_PARSE(res);,/tostruct)
    if typename(res) eq 'LIST' then begin
        for i=0,n_elements(res)-1 do begin
            res[i]=res[i].tostruct()
        endfor
    endif else res = res.tostruct()
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


FUNCTION mpo::start, name, description ;because IDL uses 'init' for class initialization
  payload = get_payload("name",name,"description",description)

  Res = self->post(self.workflow_rt, payload)
  return, res
end

FUNCTION mpo::add , workflow_uid, parent_uid, name, description, uri

 payload =   get_payload($
                                  self.workid,workflow_uid,$
                                  self.parentid,parent_uid,$
                                  "name",name,"description",description,$
                                  "uri",uri   )
 res = self->post(self.dataobject_rt, payload)
 return, res
end

FUNCTION mpo::step , workflow_uid, parent_uid, name, description, uri
;todo add additional inputs to parent_uid
 payload =   get_payload($
                                  self.workid,workflow_uid,$
                                  self.parentid,[parent_uid],$
                                  "name",name,"description",description,$
                                  "uri",uri   )
 res = self->post(self.activity_rt, payload)
 return, res
end

FUNCTION mpo::comment, parent_uid, text
 payload =   get_payload($
                                  self.parentid,parent_uid,$
                                  "text",text)
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
              'post_payload','{"error":"3", "message":"Payload missing"}'$
                          )
  tnames=tag_names(errorstr)
  tindex=where( strcmp(tnames,strupcase(key) ) eq 1)
  return, errorstr.(tindex[0])
end

PRO mpo::cleanup
 obj_destroy,self.req
 return
end

FUNCTION mpo::init , host=host, port=port, version=version

 if not keyword_set(host)    then host='mpo.psfc.mit.edu'
 if not keyword_set(port)    then port='8080'
 if not keyword_set(version) then version='v0'

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

; self.ERROR.get_route='{"error":"1", "message":"Invalid Route"}'
 self.req=OBJ_NEW('IDLnetUrl')
; uncomment for debugging
; self.req->SetProperty, CALLBACK_FUNCTION='debug_req'
 self.req->SetProperty, URL_PORT=port
 self.req->SetProperty, URL_SCHEME='http' ;important
 self.req->SetProperty, HEADERS=self.POSTheaders
 self.req->Setproperty, URL_HOST=host
; For when authentication is implemented
; self.req->Setproperty, URL_PASSWORD=''
; self.req->Setproperty, URL_USERNAME=''

 return,1
end


;This needs to go last so other methods are loaded.
PRO mpo__define
 void = { mpo, req:OBJ_NEW(), $
          POSTheaders:"", GETheaders:"",ID:'',WORKID:'',PARENTID:'',$
          MPO_VERSION:'',WORKFLOW_RT:'', COMMENT_RT:'',METADATA_RT:'', $
          DATAOBJECT_RT:'',ACTIVITY_RT:'' $
        }

 return
end

;          { $
;        get_route:'{"error":"1", "message":"Invalid Route"}',$
;        post_route:'{"error":"2", "message":"Invalid Route"}',$
;        post_payload:'{"error":"3", "message":"Payload missing"}'$
;          }$
