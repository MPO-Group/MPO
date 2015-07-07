drop table if exists mpoauth cascade;
create table mpoauth
(
  u_guid uuid primary key,
  read boolean,
  write boolean
);
inert into mpoauth (u_guid, read, write) values ('bc789de3-7484-49dc-a498-3b5a3aad3c80', true, true)
inert into mpoauth (u_guid, read, write) values ('f223db41-d1c5-41db-b8af-fde6c0a16f76', true, true)
alter table mpoauth OWNER TO mpoadmin;
alter table mpoauth add constraint mpoauth_u_guid_fkey FOREIGN KEY (u_guid) REFERENCES mpousers(uuid);

insert into mpoauth (u_guid) select uuid from mpousers;
