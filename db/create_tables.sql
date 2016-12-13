/* uncomment to wipe out the whole database and recreate

drop database if exists mpodbdev; */

create extension if not exists "pgcrypto";

drop role if exists mpoadmin;
create user mpoadmin with password 'mpo2013';

/* create database mpodbdev OWNER mpoadmin; */


drop table if exists mpousers cascade;
create table mpousers
(
  username text unique not null,
  uuid uuid primary key,
  firstname text,
  lastname text,
  email text,
  organization text,
  phone text,
  dn text,
  creation_time timestamp
);
/*insert into mpousers values ('romosan','bc789de3-7484-49dc-a498-3b5a3aad3c80', 'Alexander', 'Romosan', 'romosan@opteron05@lbl.gov','LBL','555-555-1234','xxx' );*/
/*insert into mpousers values ('mdsadmin', 'a8bc7b5a-b4f5-49ec-87fb-20e5bddfa1af'); */
insert into mpousers (username,uuid,creation_time) values ('mpoadmin', gen_random_uuid(),now());
insert into mpousers (username,uuid,firstname,lastname,email,organization,dn,creation_time) values ('mpodemo', gen_random_uuid(), 'MPO', 'Demo User', 'jas@psfc.mit.edu', 'MIT', 'emailAddress=jas@psfc.mit.edu,CN=MPO Demo User,OU=PSFC,O=c21f969b5f03d33d43e04f8f136e7682,O=MIT,L=Cambridge,ST=Massachusetts,C=US',now());
alter table mpousers OWNER TO mpoadmin;

drop table if exists mpoauth cascade;
create table mpoauth
(
  u_guid uuid primary key,
  read boolean,
  write boolean
);
insert into mpoauth (u_guid, read, write) values (gen_random_uuid(), true, true);
insert into mpoauth (u_guid, read, write) values (gen_random_uuid(), true, true);
alter table mpoauth OWNER TO mpoadmin;

drop table if exists collection cascade;
create table collection
(
  c_guid uuid primary key,
  name text,
  description text,
  u_guid uuid references mpousers,
  creation_time timestamp
);
alter table collection owner to mpoadmin;

drop table if exists collection_elements;
create table collection_elements
(
  c_guid uuid references collection,
  e_guid uuid,
  u_guid uuid references mpousers,
  creation_time timestamp
);
alter table collection_elements owner to mpoadmin;

drop table if exists workflow cascade;
create table workflow
(
  W_GUID uuid primary key,
  name text,
  WS_GUID uuid,
  description text,
  U_GUID uuid references mpousers,
  comp_seq integer,
  creation_time timestamp,
  start_time timestamp,
  end_time timestamp,
  completion_status text,
  status_explanation text
);
alter table workflow OWNER TO mpoadmin;

drop table if exists dataobject cascade;
create table dataobject
(
  DO_GUID uuid primary key,
  name text,
  description text,
  URI text,
  source_guid uuid,
  creation_time timestamp,
  U_GUID  uuid references mpousers
);

alter table dataobject OWNER TO mpoadmin;

drop table if exists dataobject_instance cascade;
create table dataobject_instance
(
  DOI_GUID uuid primary key,
  DO_GUID uuid references dataobject,
  W_GUID uuid references workflow,
  creation_time timestamp,
  U_GUID  uuid references mpousers
);

alter table dataobject_instance OWNER TO mpoadmin;

drop table if exists activity;
create table activity
(
  A_GUID uuid primary key,
  name text,
  AV_GUID uuid,
  W_GUID uuid references workflow,
  description text,
  URI text,
  creation_time timestamp,
  U_GUID  uuid references mpousers,
  start_time timestamp,
  end_time timestamp,
  completion_status text,
  status_explanation text
);
ALTER TABLE activity OWNER to mpoadmin;

drop table if exists comment;
create table comment
(
  CM_GUID uuid primary key,
  content text,
  URI text,
  creation_time timestamp,
  U_GUID  uuid references mpousers,
  comment_type text,
  parent_GUID uuid,
  parent_type text
);
ALTER TABLE comment OWNER to mpoadmin;

drop table if exists workflow_connectivity;
create table workflow_connectivity
(
  WC_GUID uuid primary key,
  W_GUID uuid references workflow,
  parent_GUID uuid,
  parent_type text,
  child_GUID uuid,
  child_type text,
  creation_time timestamp
);
ALTER TABLE workflow_connectivity OWNER TO mpoadmin;

drop table if exists metadata;
create table metadata
(
  md_guid uuid primary key,
  name text,
  value text,
  type text,
  uri text,
  parent_guid uuid,
  parent_type text,
  creation_time timestamp,
  U_GUID  uuid references mpousers
);
ALTER TABLE metadata OWNER TO mpoadmin;

drop table if exists ontology_classes;
create table ontology_classes
(
  oc_guid uuid,
  name text,
  description text,
  parent_guid uuid,
  added_by uuid,
  date_added timestamp,
  reviewed_by uuid,
  date_reviewed timestamp
);
ALTER TABLE ontology_classes OWNER TO mpoadmin;

drop table if exists ontology_terms cascade;
create table ontology_terms
(
  ot_guid uuid primary key,
  class uuid,
  name text,
  description text,
  parent_guid uuid,
  value_type text,
  units text,
  specified boolean,
  added_by uuid references mpousers,
  date_added timestamp,
  reviewed_by uuid,
  date_reviewed timestamp
);
/* create top level nodes*/
insert into ontology_terms (ot_guid,name,description,added_by,date_added) values( gen_random_uuid(),'Workflow', 'Ontology terms for workflow entries',getAdminUid(),now());
insert into ontology_terms (ot_guid,name,description,parent_guid,value_type,specified,added_by,date_added) values (gen_random_uuid(),'Type','Terms that describe the workflow types',getTermUidByPath('/Workflow'),'string',true,getAdminUid(),now());
insert into ontology_terms (ot_guid,name,description,parent_guid,value_type,specified,added_by,date_added) values (gen_random_uuid(),'Status','Indicate status of a workflow',getTermUidByPath('/Workflow'),'string',true,getAdminUid(),now());
insert into ontology_terms (ot_guid,name,description,parent_guid,value_type,specified,added_by,date_added) values (gen_random_uuid(),'State','Indicate state of progress of a workflow',getTermUidByPath('/Workflow/Status'),'string',true,getAdminUid(),now());
insert into ontology_terms (ot_guid,name,description,parent_guid,value_type,added_by,date_added) values (gen_random_uuid(),'In Progress','Workflow has started but has not completed',getTermUidByPath('/Workflow/Status/State'),'string',getAdminUid(),now());
insert into ontology_terms (ot_guid,name,description,parent_guid,value_type,added_by,date_added) values (gen_random_uuid(),'Complete','Workflow has completed',getTermUidByPath('/Workflow/Status/State'),'string',getAdminUid(),now());
insert into ontology_terms (ot_guid,name,description,parent_guid,value_type,added_by,date_added) values (gen_random_uuid(),'Non Standard Completion','Workflow has failed or completed with errors',getTermUidByPath('/Workflow/Status/State'),'string',getAdminUid(),now());
insert into ontology_terms (ot_guid,name,description,parent_guid,value_type,added_by,date_added) values (gen_random_uuid(),'Ready for Review','Workflow is ready for review',getTermUidByPath('/Workflow/Status/State'),'string',getAdminUid(),now());
insert into ontology_terms (ot_guid,name,description,added_by,date_added) values( gen_random_uuid(),'Activity', 'Ontology terms for activity entries',getAdminUid(),now());
insert into ontology_terms (ot_guid,name,description,parent_guid,value_type,specified,added_by,date_added) values (gen_random_uuid(),'Status','Indicate status of an activity',getTermUidByPath('/Activity'),'string',true,getAdminUid(),now());
insert into ontology_terms (ot_guid,name,description,parent_guid,value_type,specified,added_by,date_added) values (gen_random_uuid(),'State','Indicate state of progress of an activity',getTermUidByPath('/ActivityStatus'),'string',true,getAdminUid(),now());
insert into ontology_terms (ot_guid,name,description,parent_guid,value_type,added_by,date_added) values (gen_random_uuid(),'In Progress','Activity has started but has not completed',getTermUidByPath('/Activity/Status/State'),'string',getAdminUid(),now());
insert into ontology_terms (ot_guid,name,description,parent_guid,value_type,added_by,date_added) values (gen_random_uuid(),'Complete','Activity has completed',getTermUidByPath('/Activity/Status/State'),'string',getAdminUid(),now());
insert into ontology_terms (ot_guid,name,description,parent_guid,value_type,added_by,date_added) values (gen_random_uuid(),'Non Standard Completion','Activity has failed or completed with errors',getTermUidByPath('/Activity/Status/State'),'string',getAdminUid(),now());
insert into ontology_terms (ot_guid,name,description,added_by,date_added) values( gen_random_uuid(),'Dataobject', 'Ontology terms for dataobject entries',getAdminUid(),now());
insert into ontology_terms (ot_guid,name,description,parent_guid,value_type,specified,added_by,date_added) values (gen_random_uuid(),'Status','Indicate status of a dataobject',getTermUidByPath('/Dataobject'),'string',true,getAdminUid(),now());
insert into ontology_terms (ot_guid,name,description,parent_guid,value_type,specified,added_by,date_added) values (gen_random_uuid(),'State','Indicate state of progress of a dataobject',getTermUidByPath('/Dataobject/Status'),'string',true,getAdminUid(),now());
insert into ontology_terms (ot_guid,name,description,parent_guid,value_type,added_by,date_added) values (gen_random_uuid(),'Ready for Review','Data object is ready for review',getTermUidByPath('/Dataobject/Status/State'),'string',getAdminUid(),now());
insert into ontology_terms (ot_guid,name,description,parent_guid,value_type,added_by,date_added) values (gen_random_uuid(),'Review Complete','Data object review is complete',getTermUidByPath('/Dataobject/Status/State'),'string',getAdminUid(),now());
insert into ontology_terms (ot_guid,name,description,added_by,date_added) values( gen_random_uuid(),'Generic', 'Ontology terms for generic entries',getAdminUid(),now());
insert into ontology_terms (ot_guid,name,description,parent_guid,value_type,specified,added_by,date_added) values (gen_random_uuid(),'Status','Generic status terms',getTermUidByPath('/Generic'),'string',true,getAdminUid(),now());
insert into ontology_terms (ot_guid,name,description,parent_guid,value_type,specified,added_by,date_added) values (gen_random_uuid(),'quality','Fitness of an object for a particular purpose',getTermUidByPath('/Generic/Status'),'string',true,getAdminUid(),now());
insert into ontology_terms (ot_guid,name,description,parent_guid,value_type,added_by,date_added) values (gen_random_uuid(),'1','Low quality: Object should not be used for additional purposes',getTermUidByPath('/Generic/Status/quality'),'int',getAdminUid(),now());
insert into ontology_terms (ot_guid,name,description,parent_guid,value_type,added_by,date_added) values (gen_random_uuid(),'2','Medium quality: Object may be useful for some purposes',getTermUidByPath('/Generic/Status/quality'),'int',getAdminUid(),now());
insert into ontology_terms (ot_guid,name,description,parent_guid,value_type,added_by,date_added) values (gen_random_uuid(),'3','High quality: Object is broadly useful',getTermUidByPath('/Generic/Status/quality'),'int',getAdminUid(),now());
insert into ontology_terms (ot_guid,name,description,parent_guid,value_type,added_by,date_added) values (gen_random_uuid(),'4','Notable quality: Object is of special importance or interest',getTermUidByPath('/Generic/Status/quality'),'int',getAdminUid(),now());
ALTER TABLE ontology_terms OWNER TO mpoadmin;

drop table if exists ontology_instances;
create table ontology_instances
(
  oi_guid uuid primary key,
  target_guid uuid,
  term_guid uuid references ontology_terms,
  value text,
  creation_time timestamp,
  u_guid uuid references mpousers
);
ALTER TABLE ontology_instances OWNER TO mpoadmin;

create or replace function getWID(cid uuid) returns uuid as $$
declare
  parent_guid uuid;
  parent_type text;
  wid uuid;
begin
  execute 'select parent_guid, parent_type from comment where cm_guid=''' || cid || ''' union select parent_guid, parent_type from metadata where md_guid=''' || cid || '''' into parent_guid,parent_type;
  while (parent_type = 'comment' or parent_type = 'metadata')
  loop
    execute 'select parent_guid, parent_type from comment where cm_guid=''' || parent_guid || ''' union select parent_guid, parent_type from metadata where md_guid=''' || parent_guid || '''' into parent_guid, parent_type;
  end loop;
  if parent_type = 'activity' then
    execute 'select w_guid from ' || parent_type || ' where a_guid=''' || parent_guid || '''' into wid;
  elsif parent_type = 'dataobject_instance' then
    execute 'select w_guid from ' || parent_type || ' where doi_guid=''' || parent_guid || '''' into wid;
  elsif parent_type = 'workflow' then
    execute 'select w_guid from ' || parent_type || ' where w_guid=''' || parent_guid || '''' into wid;
  end if;

  return wid;
end;
$$ LANGUAGE plpgsql;
alter function getWID(cid uuid) OWNER TO mpoadmin;

create or replace function getAdminUid() returns uuid as $$
declare
  auid uuid;
begin
  select uuid from mpousers where username='mpoadmin' into auid;

  return auid;
end;
$$ LANGUAGE plpgsql;

create or replace function getTermUidByPath(text) returns uuid as $$
declare
  tuid uuid;
  puid uuid;
  i text;
begin
  for i in select * from unnest(string_to_array($1, '/'))
  where unnest!=''
  loop
    if (puid is not null) then
      select ot_guid from ontology_terms where name= i and parent_guid=puid into puid;
    else
      select ot_guid from ontology_terms where name=i and parent_guid is null into puid;
    end if;
  end loop;

  return puid;

end;
$$ LANGUAGE plpgsql;
alter function getTermUidByPath(text) OWNER TO mpoadmin;
