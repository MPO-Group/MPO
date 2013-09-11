alter table mpousers OWNER TO mpoadmin;
alter table workflow OWNER TO mpoadmin;
alter table dataobject OWNER TO mpoadmin;
ALTER TABLE activity OWNER to mpoadmin;
ALTER TABLE comment OWNER to mpoadmin;
ALTER TABLE workflow_connectivity OWNER TO mpoadmin;
ALTER TABLE metadata OWNER TO mpoadmin;


alter table workflow  ADD column comp_seq integer;
alter table dataobject ADD column u_guid uuid;
alter table comment    ADD column u_guid uuid;
alter table metadata   ADD column u_guid uuid;
alter table activity   ADD column u_guid uuid;
alter table workflow drop column u_guid;
alter table workflow add column u_guid uuid;
update workflow set u_guid='bc789de3-7484-49dc-a498-3b5a3aad3c80';
alter table workflow  ALTER column w_guid TYPE uuid using CAST(regexp_replace(w_guid, '([A-Z0-9]{4})([A-Z0-9]{12})', E'\\1-\\2') as uuid);
alter table workflow  ALTER column ws_guid TYPE uuid using CAST(regexp_replace(ws_guid, '([A-Z0-9]{4})([A-Z0-9]{12})', E'\\1-\\2') as uuid);
alter table dataobject ALTER column do_guid TYPE uuid using CAST(regexp_replace(do_guid, '([A-Z0-9]{4})([A-Z0-9]{12})', E'\\1-\\2') as uuid);
alter table dataobject ALTER column dov_guid TYPE uuid using CAST(regexp_replace(dov_guid, '([A-Z0-9]{4})([A-Z0-9]{12})', E'\\1-\\2') as uuid);
alter table dataobject ALTER column w_guid TYPE uuid using CAST(regexp_replace(w_guid, '([A-Z0-9]{4})([A-Z0-9]{12})', E'\\1-\\2') as uuid);
alter table activity ALTER column a_guid TYPE uuid using CAST(regexp_replace(a_guid, '([A-Z0-9]{4})([A-Z0-9]{12})', E'\\1-\\2') as uuid);
alter table activity ALTER column av_guid TYPE uuid using CAST(regexp_replace(av_guid, '([A-Z0-9]{4})([A-Z0-9]{12})', E'\\1-\\2') as uuid);
alter table activity ALTER column w_guid TYPE uuid using CAST(regexp_replace(w_guid, '([A-Z0-9]{4})([A-Z0-9]{12})', E'\\1-\\2') as uuid);
alter table comment ALTER column wc_guid TYPE uuid using CAST(regexp_replace(wc_guid, '([A-Z0-9]{4})([A-Z0-9]{12})', E'\\1-\\2') as uuid);
alter table comment ALTER column cm_guid TYPE uuid using CAST(regexp_replace(cm_guid, '([A-Z0-9]{4})([A-Z0-9]{12})', E'\\1-\\2') as uuid);
alter table comment ALTER column w_guid TYPE uuid using CAST(regexp_replace(w_guid, '([A-Z0-9]{4})([A-Z0-9]{12})', E'\\1-\\2') as uuid);
alter table comment ALTER column parent_guid TYPE uuid using CAST(regexp_replace(parent_guid, '([A-Z0-9]{4})([A-Z0-9]{12})', E'\\1-\\2') as uuid);
alter table comment ALTER column child_guid TYPE uuid using CAST(regexp_replace(child_guid, '([A-Z0-9]{4})([A-Z0-9]{12})', E'\\1-\\2') as uuid);
alter table metadata ALTER column md_guid TYPE uuid using CAST(regexp_replace(md_guid, '([A-Z0-9]{4})([A-Z0-9]{12})', E'\\1-\\2') as uuid);
alter table metadata ALTER column parent_guid TYPE uuid using CAST(regexp_replace(parent_guid, '([A-Z0-9]{4})([A-Z0-9]{12})', E'\\1-\\2') as uuid);


drop table if exists mpousers;
create table mpousers
(
  username text,
  uuid uuid,
  firstname text, 
  lastname text, 
  email text, 
  organization text, 
  phone text,
  dn text
);
insert into mpousers values ('romosan','bc789de3-7484-49dc-a498-3b5a3aad3c80');
insert into mpousers values ('mdsadmin', 'a8bc7b5a-b4f5-49ec-87fb-20e5bddfa1af');
insert into mpousers values ('mpoadmin', 'ddc315a1-6310-41e7-a84d-886bc904f3b2');
insert into mpousers values ('mpodemo', 'f223db41-d1c5-41db-b8af-fde6c0a16f76', 'MPO', 'Demo User', 'jas@psfc.mit.edu', 'MIT', '', '/C=US/ST=Massachusetts/L=Cambridge/O=MIT/O=c21f969b5f03d33d43e04f8f136e7682/OU=PSFC/CN=MPO Demo User/emailAddress=jas@psfc.mit.edu');
alter table mpousers OWNER TO mpoadmin;


