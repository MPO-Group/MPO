drop table if exists users;
create table users
(
  name text,
  uuid integer
);

insert into users values ('romosan',1000);

drop table if exists workflow;
create table workflow
(
  W_GUID char(36),
  name text,
  WS_GUID char(36),
  description text,
  U_GUID integer,
  start_time date,
  end_time date,
  completion_status text,
  status_explanation text
);

insert into workflow values ('38303f82-7608-11e2-8033-001b213ce30d', 'EFIT', '', 'test', 1000, timestamp '2013-02-13 10:00',  timestamp '2013-02-13 11:54', '','');

drop table if exists data_object;
create table data_object
(
  DO_GUID char(36),
  name text,
  DOV_GUID char(36),
  W_GUID char(36),
  description text,
  URI text
);

insert into data_object values ('a91f50e6-760a-11e2-8033-001b213ce30d','shot','','38303f82-7608-11e2-8033-001b213ce30d','Plasma shot number','150335');
insert into data_object values ('2de2b5e8-760b-11e2-8033-001b213ce30d','Snap file','','38303f82-7608-11e2-8033-001b213ce30d','EFIT input file','\\efit01:namelist');
insert into data_object values ('e4429024-760b-11e2-8033-001b213ce30d','Green''s Table','','38303f82-7608-11e2-8033-001b213ce30d','Green''s table files','/link/efit/rpf[01-12].d3d');
insert into data_object values ('108c148a-7610-11e2-8033-001b213ce30d','Plasma Current','','38303f82-7608-11e2-8033-001b213ce30d','Plasma current in MA','\magnetics::ip');
insert into data_object values ('420712a8-7610-11e2-8033-001b213ce30d','PTDATA','','38303f82-7608-11e2-8033-001b213ce30d','Point Data','???');
insert into data_object values ('305a71be-7613-11e2-8033-001b213ce30d','A File','','38303f82-7608-11e2-8033-001b213ce30d','A EQDSK File','\\efit01::results:aeqdsk');
insert into data_object values ('56a690d2-7613-11e2-8033-001b213ce30d','G File','','38303f82-7608-11e2-8033-001b213ce30d','G EQDSK File','\\efit01::results:geqdsk');

drop table if exists activity;
create table activity
(
  A_GUID char(36),
  name text,
  AV_GUID char(36),
  W_GUID char(36),
  description text,
  URI text,
  start_time date,
  end_time date,
  completion_status text,
  status_explanation text
);

insert into activity values ('773296c8-760b-11e2-8033-001b213ce30d','Read Input Files','','38303f82-7608-11e2-8033-001b213ce30d','Read shot number, snap file etc...','EFIT',timestamp '2013-02-13 10:05',timestamp '2013-02-13 10:06','','');
insert into activity values ('c5b38ffa-7610-11e2-8033-001b213ce30d','Read PTDATA','','38303f82-7608-11e2-8033-001b213ce30d','Read PTDATA and Plasma Current','EFIT',timestamp '2013-02-13 10:06',timestamp '2013-02-13 10:09','','');
insert into activity values ('6c8f7c08-7611-11e2-8033-001b213ce30d','Calibrate Data','','38303f82-7608-11e2-8033-001b213ce30d','Calibrate input to EFIT','EFIT',timestamp '2013-02-13 10:09',timestamp '2013-02-13 10:15','','');
insert into activity values ('0576b314-7612-11e2-8033-001b213ce30d','EFIT Data averaging','','38303f82-7608-11e2-8033-001b213ce30d','Average EFIT Data','EFIT',timestamp '2013-02-15 10:09',timestamp '2013-02-13 10:21','','');
insert into activity values ('6d17163a-7612-11e2-8033-001b213ce30d','Run PTDATA','','38303f82-7608-11e2-8033-001b213ce30d','Run the EFIT code to FIT the equilibria','EFIT',timestamp '2013-02-15 10:21',timestamp '2013-02-13 11:43','','');
insert into activity values ('cce36500-7612-11e2-8033-001b213ce30d','Write EFIT Outputs','','38303f82-7608-11e2-8033-001b213ce30d','Write the EFIT output files','EFIT',timestamp '2013-02-15 11:43',timestamp '2013-02-13 11:51','','');

drop table if exists workflow_connectivity;
create table workflow_connectivity
(
  WC_GUID char(36),
  W_GUID char(36),
  parent_GUID char(36),
  parent_type text,
  child_GUID char(36),
  child_type text
);

insert into workflow_connectivity values ('9b7f4432-760f-11e2-8033-001b213ce30d', '38303f82-7608-11e2-8033-001b213ce30d', '', '', 'a91f50e6-760a-11e2-8033-001b213ce30d','data_object');
insert into workflow_connectivity values ('b71e915c-760f-11e2-8033-001b213ce30d', '38303f82-7608-11e2-8033-001b213ce30d', '', '', '2de2b5e8-760b-11e2-8033-001b213ce30d', 'data_object');
insert into workflow_connectivity values ('e1caa76a-760f-11e2-8033-001b213ce30d', '38303f82-7608-11e2-8033-001b213ce30d', '', '', 'e4429024-760b-11e2-8033-001b213ce30d', 'data_object');
insert into workflow_connectivity values ('5a31e5ae-760d-11e2-8033-001b213ce30d', '38303f82-7608-11e2-8033-001b213ce30d', 'a91f50e6-760a-11e2-8033-001b213ce30d','data_object','773296c8-760b-11e2-8033-001b213ce30d','activity');
insert into workflow_connectivity values ('36247b70-760f-11e2-8033-001b213ce30d','38303f82-7608-11e2-8033-001b213ce30d', '2de2b5e8-760b-11e2-8033-001b213ce30d', 'data_object','773296c8-760b-11e2-8033-001b213ce30d','activity');
insert into workflow_connectivity values ('574042bc-760f-11e2-8033-001b213ce30d','38303f82-7608-11e2-8033-001b213ce30d', 'e4429024-760b-11e2-8033-001b213ce30d', 'data_object','773296c8-760b-11e2-8033-001b213ce30d','activity');
insert into workflow_connectivity values ('732f6cea-7610-11e2-8033-001b213ce30d','38303f82-7608-11e2-8033-001b213ce30d', '', '', '108c148a-7610-11e2-8033-001b213ce30d', 'data_object');
insert into workflow_connectivity values ('a45c6138-7610-11e2-8033-001b213ce30d','38303f82-7608-11e2-8033-001b213ce30d', '', '', '420712a8-7610-11e2-8033-001b213ce30d', 'data_object');
insert into workflow_connectivity values ('19a5358c-7611-11e2-8033-001b213ce30d','38303f82-7608-11e2-8033-001b213ce30d','108c148a-7610-11e2-8033-001b213ce30d', 'data_object','c5b38ffa-7610-11e2-8033-001b213ce30d','activity');
insert into workflow_connectivity values ('3a531b1e-7611-11e2-8033-001b213ce30d','38303f82-7608-11e2-8033-001b213ce30d','420712a8-7610-11e2-8033-001b213ce30d', 'data_object','c5b38ffa-7610-11e2-8033-001b213ce30d','activity');
insert into workflow_connectivity values ('ab96a390-7611-11e2-8033-001b213ce30d','38303f82-7608-11e2-8033-001b213ce30d','c5b38ffa-7610-11e2-8033-001b213ce30d','activity','6c8f7c08-7611-11e2-8033-001b213ce30d','activity');
insert into workflow_connectivity values ('cd671e00-7611-11e2-8033-001b213ce30d','38303f82-7608-11e2-8033-001b213ce30d','773296c8-760b-11e2-8033-001b213ce30d','activity','6c8f7c08-7611-11e2-8033-001b213ce30d','activity');
insert into workflow_connectivity values ('41656b68-7612-11e2-8033-001b213ce30d','6c8f7c08-7611-11e2-8033-001b213ce30d','activity','0576b314-7612-11e2-8033-001b213ce30d','activity');
insert into workflow_connectivity values ('acc02510-7612-11e2-8033-001b213ce30d','38303f82-7608-11e2-8033-001b213ce30d','0576b314-7612-11e2-8033-001b213ce30d','activity','6d17163a-7612-11e2-8033-001b213ce30d','activity');
insert into workflow_connectivity values ('0614a50a-7613-11e2-8033-001b213ce30d','38303f82-7608-11e2-8033-001b213ce30d','6d17163a-7612-11e2-8033-001b213ce30d','activity','cce36500-7612-11e2-8033-001b213ce30d','activity');
insert into workflow_connectivity values ('80ea7dcc-7613-11e2-8033-001b213ce30d','38303f82-7608-11e2-8033-001b213ce30d','cce36500-7612-11e2-8033-001b213ce30d','activity','305a71be-7613-11e2-8033-001b213ce30d','data_object');
insert into workflow_connectivity values ('80ea7dcc-7613-11e2-8033-001b213ce30d','38303f82-7608-11e2-8033-001b213ce30d','cce36500-7612-11e2-8033-001b213ce30d','activity','56a690d2-7613-11e2-8033-001b213ce30d','data_object');
insert into workflow_connectivity values ('ca860852-7613-11e2-8033-001b213ce30d','38303f82-7608-11e2-8033-001b213ce30d','305a71be-7613-11e2-8033-001b213ce30d','data_object','','');
insert into workflow_connectivity values ('de1e0676-7613-11e2-8033-001b213ce30d','38303f82-7608-11e2-8033-001b213ce30d','56a690d2-7613-11e2-8033-001b213ce30d','data_object');
