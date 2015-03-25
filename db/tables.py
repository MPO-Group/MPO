from sqlalchemy import *
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship


Base = declarative_base()

class MPOUser(Base):
    __tablename__ = 'mpousers_test'

    username = Column(Text,unique=True,nullable=False)
    uuid = Column(UUID,primary_key=True)
    firstname = Column(Text)
    lastname = Column(Text)
    email = Column(Text)
    organization = Column(Text)
    phone = Column(Text)
    dn = Column(Text)


class Collection(Base):
    __tablename__ = 'collection_test'

    c_guid = Column(UUID,primary_key=True)
    name = Column(Text)
    description = Column(Text)
    u_guid = Column(UUID,ForeignKey('mpousers_test.uuid'))
    creation_time = Column(DateTime, default=func.now())
    user = relationship(MPOUser)


class CollectionEllement(Base):
    __tablename__ = 'collection_elements_test'

    c_guid = Column(UUID,ForeignKey('collection_test.c_guid'),primary_key=True)
    e_guid = Column(UUID)
    u_guid = Column(UUID,ForeignKey('mpousers_test.uuid'))
    creation_time = Column(DateTime, default=func.now())
    user = relationship(MPOUser)


class Workflow(Base):
    __tablename__ = 'workflow_test'

    w_guid = Column(UUID,primary_key=True)
    name = Column(Text)
    ws_guid = Column(UUID)
    u_guid = Column(UUID,ForeignKey('mpousers_test.uuid'))
    comp_seq = Column(Integer)
    creation_time = Column(DateTime, default=func.now())
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    completion_status = Column(Text)
    status_explanation = Column(Text)
    user = relationship(MPOUser)


class DataObject(Base):
    __tablename__ = 'dataobject_test'

    do_guid = Column(UUID,primary_key=True)
    name = Column(Text)
    description = Column(Text)
    uri = Column(Text)
    source_guid = Column(UUID)
    creation_time = Column(DateTime, default=func.now())
    u_guid = Column(UUID,ForeignKey('mpousers_test.uuid'))
    user = relationship(MPOUser)


class DataObjectInstance(Base):
    __tablename__ = 'dataobject_instance_test'

    doi_guid = Column(UUID,primary_key=True)
    do_guid = Column(UUID,ForeignKey('dataobject_test.do_guid'))
    w_guid = Column(UUID,ForeignKey('workflow_test.w_guid'))
    creation_time = Column(DateTime, default=func.now())
    u_guid = Column(UUID,ForeignKey('mpousers_test.uuid'))
    user = relationship(MPOUser)


class Activity(Base):
    __tablename__ = 'activity_test'

    a_guid = Column(UUID,primary_key=True)
    name = Column(Text)
    av_guid = Column(UUID)
    w_guid = Column(UUID,ForeignKey('workflow_test.w_guid'))
    description = Column(Text)
    uri = Column(Text)
    creation_time = Column(DateTime, default=func.now())
    u_guid = Column(UUID,ForeignKey('mpousers_test.uuid'))
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    completion_status = Column(Text)
    status_explanation = Column(Text)
    user = relationship(MPOUser)


class Comment(Base):
    __tablename__ = 'comment_test'

    cm_guid = Column(UUID,primary_key=True)
    content = Column(Text)
    uri = Column(Text)
    creation_time = Column(DateTime, default=func.now())
    u_guid = Column(UUID,ForeignKey('mpousers_test.uuid'))
    comment_type = Column(Text)
    parent_guid = Column(UUID)
    parent_type = Column(Text)
    user = relationship(MPOUser)


class WorkflowConnectivity(Base):
    __tablename__ = 'workflow_connectivity_test'

    wc_guid = Column(UUID,primary_key=True)
    w_guid = Column(UUID,ForeignKey('workflow_test.w_guid'))
    parent_guid = Column(UUID)
    parent_type = Column(Text)
    child_guid = Column(UUID)
    child_type = Column('child_type',Text)
    creation_time = Column(DateTime, default=func.now())


class Metadata(Base):
    __tablename__ = 'metadata_test'

    md_guid = Column(UUID,primary_key=True)
    name = Column(Text)
    value = Column(Text)
    type = Column(Text)
    uri = Column(Text)
    parent_guid = Column(UUID)
    parent_type = Column(Text)
    creation_time = Column(DateTime, default=func.now())
    u_guid = Column(UUID,ForeignKey('mpousers_test.uuid'))
    user = relationship(MPOUser)


class OntologyClass(Base):
    __tablename__ = 'ontology_classes_test'

    oc_guid = Column(UUID,primary_key=True)
    name = Column(Text)
    description = Column(Text)
    parent_guid = Column(UUID)
    added_by = Column(UUID)
    date_added = Column(DateTime, default=func.now())
    reviewed_by = Column(UUID)
    date_reviewed = Column(DateTime)


class OntologyTerm(Base):
    __tablename__ = 'ontology_terms_test'

    ot_guid = Column(UUID,primary_key=True)
    oc_guid = Column(UUID,ForeignKey('ontology_classes_test.oc_guid'))
    name = Column(Text)
    description = Column(Text)
    parent_guid = Column(UUID)
    value_type = Column(Text)
    units = Column(Text)
    specified = Column(Boolean)
    added_by = Column(UUID,ForeignKey('mpousers_test.uuid'))
    date_added = Column(DateTime, default=func.now())
    reviewed_by = Column('reviewed_by',UUID)
    date_reviewed = Column(DateTime)
    user = relationship(MPOUser)


class OntologyInstance(Base):
    __tablename__ = 'ontology_instances_test'

    oi_guid = Column(UUID,primary_key=True)
    target_guid = Column(UUID)
    term_guid = Column(UUID,ForeignKey('ontology_terms_test.ot_guid'))
    value = Column(Text)
    creation_time = Column(DateTime, default=func.now())
    u_guid = Column(UUID,ForeignKey('mpousers_test.uuid'))
    user = relationship(MPOUser)


def tables():
    engine = create_engine('postgresql://mpoadmin:mpo213@localhost/mpoDB')

    Base.metadata.create_all(engine)
