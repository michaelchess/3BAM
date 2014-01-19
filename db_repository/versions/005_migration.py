from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
mutation = Table('mutation', pre_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('ref_alt_allele', String),
    Column('sample_file_identifier', String),
    Column('user_id', Integer),
    Column('num_samples_observed_in', String),
    Column('chromosome', String),
    Column('variant_ID', String),
    Column('base_position', String),
)

mutation = Table('mutation', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('user_id', Integer),
    Column('locus', String(length=200)),
    Column('geneLoci', String(length=200)),
    Column('gene', String(length=200)),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['mutation'].columns['base_position'].drop()
    pre_meta.tables['mutation'].columns['chromosome'].drop()
    pre_meta.tables['mutation'].columns['num_samples_observed_in'].drop()
    pre_meta.tables['mutation'].columns['ref_alt_allele'].drop()
    pre_meta.tables['mutation'].columns['sample_file_identifier'].drop()
    pre_meta.tables['mutation'].columns['variant_ID'].drop()
    post_meta.tables['mutation'].columns['gene'].create()
    post_meta.tables['mutation'].columns['geneLoci'].create()
    post_meta.tables['mutation'].columns['locus'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['mutation'].columns['base_position'].create()
    pre_meta.tables['mutation'].columns['chromosome'].create()
    pre_meta.tables['mutation'].columns['num_samples_observed_in'].create()
    pre_meta.tables['mutation'].columns['ref_alt_allele'].create()
    pre_meta.tables['mutation'].columns['sample_file_identifier'].create()
    pre_meta.tables['mutation'].columns['variant_ID'].create()
    post_meta.tables['mutation'].columns['gene'].drop()
    post_meta.tables['mutation'].columns['geneLoci'].drop()
    post_meta.tables['mutation'].columns['locus'].drop()
