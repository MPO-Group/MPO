/* uncomment to wipe out the whole database and recreate

drop database if exists mpodbdev; */

drop role if exists mpoadmin;
create user mpoadmin with password 'mpo2013';

/* create database mpodbdev OWNER mpoadmin; */


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
/*  creation_time timestamp */
);
/*insert into mpousers values ('romosan','bc789de3-7484-49dc-a498-3b5a3aad3c80', 'Alexander', 'Romosan', 'romosan@opteron05@lbl.gov','LBL','555-555-1234','xxx' );*/
insert into mpousers values ('mdsadmin', 'a8bc7b5a-b4f5-49ec-87fb-20e5bddfa1af');
insert into mpousers values ('mpoadmin', 'ddc315a1-6310-41e7-a84d-886bc904f3b2');
insert into mpousers values ('mpodemo', 'f223db41-d1c5-41db-b8af-fde6c0a16f76', 'MPO', 'Demo User', 'jas@psfc.mit.edu', 'MIT', '', '/C=US/ST=Massachusetts/L=Cambridge/O=MIT/O=c21f969b5f03d33d43e04f8f136e7682/OU=PSFC/CN=MPO Demo User/emailAddress=jas@psfc.mit.edu');
alter table mpousers OWNER TO mpoadmin;

drop table if exists collection
create table collection
(
  c_guid uuid,
  name text,
  description text,
  u_guid uuid,
  creation_time timestamp
);
alter table collection owner to mpoadmin;

drop table if exists collection_elements
create table collection_elements
(
  c_guid uuid,
  e_uuid uuid
);
alter table collection_elements owner to mpoadmin;

drop table if exists workflow;
create table workflow
(
  W_GUID uuid,
  name text,
  WS_GUID uuid,
  description text,
  U_GUID uuid,
  comp_seq integer,
  creation_time timestamp,
  start_time timestamp,
  end_time timestamp,
  completion_status text,
  status_explanation text
);
alter table workflow OWNER TO mpoadmin;

drop table if exists dataobject;
create table dataobject
(
  DO_GUID uuid,
  name text,
  DOV_GUID uuid,
  W_GUID uuid,
  creation_time timestamp,
  U_GUID  uuid,
  description text,
  URI text
);

alter table dataobject OWNER TO mpoadmin;

drop table if exists activity;
create table activity
(
  A_GUID uuid,
  name text,
  AV_GUID uuid,
  W_GUID uuid,
  description text,
  URI text,
  creation_time timestamp,
  U_GUID  uuid,
  start_time timestamp,
  end_time timestamp,
  completion_status text,
  status_explanation text
);
ALTER TABLE activity OWNER to mpoadmin;

drop table if exists comment;
create table comment
(
  CM_GUID uuid,
  content text,
  URI text,
  creation_time timestamp,
  U_GUID  uuid,
  comment_type text,
  parent_GUID uuid,
  parent_type text
);
ALTER TABLE comment OWNER to mpoadmin;

drop table if exists workflow_connectivity;
create table workflow_connectivity
(
  WC_GUID uuid,
  W_GUID uuid,
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
  md_guid uuid,
  name text,
  value text,
  type text,
  uri text,
  parent_guid uuid,
  parent_type text,
  creation_time timestamp,
  U_GUID  uuid
);
ALTER TABLE metadata OWNER TO mpoadmin;

drop table if exists ontology_classes;
create table ontology_classes
(
  oc_uid uuid,
  name text,
  description text,
  parent_guid uuid,
  added_by uuid,
  date_added timestamp,
  reviewd_by uuid,
  date_reviewed timestamp
);

drop table if exists ontology_terms;
create table ontology_terms
(
  ot_uid uuid,
  class uuid,
  name text,
  description text,
  parent_guid uuid,
  added_by uuid,
  date_added timestamp,
  reviewd_by uuid,
  date_reviewed timestamp
);

drop table if exists ontology_instance;
create table ontology_instance
(
  oi_uid uuid,
  target_uid uuid,
  term_uid uuid,
  creation_time timestamp,
  u_guid uuid
);
