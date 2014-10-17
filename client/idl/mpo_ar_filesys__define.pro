;+
; NAME:
;      MPO_AR_FILESYS class
;
; PURPOSE:
;      Dynamically constructed objects to operate on filesys protocol data objects
;
;argument layout for mpo_ar_filesys:
;archive
;ls
;restore
;
; CATEGORY:
;      database, provenance, webtools
;
; CALLING SEQUENCE:
;      Not user callable, called by mpo->archive('filesys', {filespec:'file-specification'})
;                                or archive_filesys(mpo-object, 'file-specification')
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
;+
; method: archive
;
; description: Generate the URI given the values provided on construction
;-
FUNCTION mpo_ar_filesys::archive
  return, string(self.filespec, format='(%"filesys:///%s")') 
end

;+
; initialize the filesys archive object.
;
; save away the arguments in arg_struct. 
; should complain if their is a problem
;-
FUNCTION mpo_ar_filesys::init, arg_struct
  self.filespec=arg_struct.filespec
  return, 1
end

PRO mpo_ar_filesys__define
  void = { mpo_ar_filesys, filespec:''}
end
