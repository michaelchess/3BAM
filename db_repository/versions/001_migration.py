from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
mutation = Table('mutation', pre_meta,
    Column('chr', String),
    Column('id', Integer, primary_key=True, nullable=False),
    Column('var_ID', String),
    Column('base_pos', String),
    Column('ref_alt_allele', String),
    Column('sample_file_identifier', String),
    Column('num_samples_obs_in', String),
    Column('user_id', Integer),
)

mutation = Table('mutation', post_meta,
    Column('chromasome', String(length=200)),
    Column('id', Integer, primary_key=True, nullable=False),
    Column('var_ID', String(length=200)),
    Column('base_pos', String(length=200)),
    Column('ref_alt_allele', String(length=200)),
    Column('sample_file_identifier', String(length=200)),
    Column('num_samples_observed_in', String(length=200)),
    Column('user_id', Integer),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['mutation'].columns['chr'].drop()
    pre_meta.tables['mutation'].columns['num_samples_obs_in'].drop()
    post_meta.tables['mutation'].columns['chromasome'].create()
    post_meta.tables['mutation'].columns['num_samples_observed_in'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['mutation'].columns['chr'].create()
    pre_meta.tables['mutation'].columns['num_samples_obs_in'].create()
    post_meta.tables['mutation'].columns['chromasome'].drop()
    post_meta.tables['mutation'].columns['num_samples_observed_in'].drop()
