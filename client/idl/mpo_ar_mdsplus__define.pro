;+
; NAME:
;      MPO_AR_MDSPLUS class
;
; PURPOSE:
;      Dynamically constructed objects to operate on mdsplus protocol data objects
;
;argument layout for mpo_ar_mdsplus:
;archive
;ls
;restore
;
; CATEGORY:
;      database, provenance, webtools
;
; CALLING SEQUENCE:
;      Not user callable, called by mpo->archive('mdsplus', {server:'server', tree:'tree', shot:shot-number, path:'mdsplus-path'})
;                                or archive_mdsplus(mpo-object, server, tree, shot, path)
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
; IDL> print, archive_mdsplus(m, 'alcdata.psfc.mit.edu', 'cmod', 1090909009, '\ip')
; mdsplus://alcdata.psfc.mit.edu/cmod/1090909009&path=\ip
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
FUNCTION mpo_ar_mdsplus::archive
  return, string(self.server, self.tree, $
                self.shot, self.path, $ 
                format='(%"mdsplus://%s/%s/%d&path=%s")') 
end

;+
; initialize the mdsplus archive object.
;
; save away the arguments in arg_struct. 
; should complain if their is a problem
;-
FUNCTION mpo_ar_mdsplus::init, arg_struct
  self.tree=arg_struct.tree
  self.server=arg_struct.server
  self.shot=arg_struct.shot
  self.path=strjoin(strsplit(arg_struct.path,'\',/extract, /preserve), '\\')
  return, 1
end

;This needs to go last so other methods are loaded.
PRO mpo_ar_mdsplus__define
  void = { mpo_ar_mdsplus, server:'', tree:'' , shot:'', path:''}
end
