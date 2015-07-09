; NAME:
;      archive_mdsplus.pro
;
; PURPOSE:
;      Return the URI for an MDSplus dataobject
;
; CATEGORY:
;      database, provenance, webtools
;
; CALLING SEQUENCE:
;      archive_mdsplus(mpo-object, 'mdsplus-server', 'tree-name', shot-number, 'tree-path')
;
; INPUTS:
;      mpo_object - the mpo-object (mpo__define.pro) that this filesys archive will be associated with.
;      server - the name of the MDSplus server that serves this tree
;      tree - the name of the MDSplus tree
;      shot - the shot number.
;      path - the MDSplus path for this data object
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
; MODIFICATION HISTORY:
;     Josh Stillerman, October 2014 , MIT.
;        Initial version
;-
function archive_mdsplus, mpo, server, tree, shot, path, name=name, description=description
  return, mpo->archive('mdsplus', {server:server, tree:tree, shot:shot, path:path, name:name, description:description})
end
