;+
; NAME:
;      archive_filesys.pro
;
; PURPOSE:
;      Return the URI for a filesys dataobject
;
; CATEGORY:
;      database, provenance, webtools
;
; CALLING SEQUENCE:
;      archive_filesys(mpo-object, 'file-specification')
;
; INPUTS:
;      mpo_object - the mpo-object (mpo__define.pro) that this filesys archive will be associated with.
;      filespec  - the filename to generate the URL for
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
;
; PROCEDURE:
;
; EXAMPLE:
;
; mpo=obj_new('mpo',host='mpo-dev.psfc.mit.edu',port='8080',version='v0')
;
; IDL> print, archive_filesys(m, '/some/file/specification')
; filesys:///some/file/specification
;
;
; MODIFICATION HISTORY:
;     Josh Stillerman, October 2014 , MIT.
;        Initial version
;-
function archive_filesys, mpo, filespec
  return, mpo->archive('filesys', {filespec:filespec})
end
