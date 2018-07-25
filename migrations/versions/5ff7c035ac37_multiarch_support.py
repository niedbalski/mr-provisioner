"""Multiarch support

Revision ID: 5ff7c035ac37
Revises: 25be6fb1804a
Create Date: 2017-11-29 14:39:17.075985

"""
from alembic import op
import sqlalchemy as sa
from flask import current_app
from datetime import datetime

from sqlalchemy.orm import sessionmaker
import logging

logger = logging.getLogger('alembic.env')

Session = sessionmaker()


# revision identifiers, used by Alembic.
revision = '5ff7c035ac37'
down_revision = '25be6fb1804a'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()

    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('arch',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('description', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('subarch',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('arch_id', sa.Integer(), nullable=False),
    sa.Column('bootloader_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['arch_id'], ['arch.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['bootloader_id'], ['image.id'], ),
    sa.PrimaryKeyConstraint('id')
    )

    op.create_index('subarch_arch_name_uniq', 'subarch', ['arch_id', 'name'], unique=True)

    op.add_column('image', sa.Column('arch_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'image', 'arch', ['arch_id'], ['id'])

    op.add_column('machine', sa.Column('arch_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'machine', 'arch', ['arch_id'], ['id'])

    op.add_column('machine', sa.Column('subarch_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'machine', 'subarch', ['subarch_id'], ['id'])
    # ### end Alembic commands ###

    session = Session(bind=bind)
    s = sa.sql.text('INSERT INTO arch(name, description) VALUES(:name, :description) RETURNING *')
    result = session.execute(s, {'name': 'default', 'description': 'Default architecture'})
    arch_id = result.fetchone()['id']
    session.commit()

    image_id = None
    bootfile = current_app.config.get('DHCP_DEFAULT_BOOTFILE')

    if bootfile and bootfile != '':
        session = Session(bind=bind)
        s = sa.sql.text('INSERT INTO image(filename, description, file_type, arch_id, known_good, public, date) VALUES(:filename, :description, :file_type, :arch_id, :known_good, :public, :date) RETURNING *')
        result = session.execute(s, {'filename': bootfile, 'description': 'Default bootloader', 'arch_id': arch_id,
            'file_type': 'bootloader', 'known_good': True, 'public': True, 'date': datetime.utcnow()})
        image_id = result.fetchone()['id']
        session.commit()

    session = Session(bind=bind)
    s = sa.sql.text('INSERT INTO subarch(name, description, arch_id, bootloader_id) VALUES(:name, :description, :arch_id, :bootloader_id) RETURNING *')
    result = session.execute(s, {'name': 'default', 'description': 'Default sub-architecture', 'arch_id': arch_id,
                                 'bootloader_id': image_id})
    subarch_id = result.fetchone()['id']
    session.commit()

    session = Session(bind=bind)
    s = sa.sql.text('UPDATE machine SET arch_id=:arch_id WHERE arch_id IS NULL')
    session.execute(s, {'arch_id': arch_id})

    s = sa.sql.text('UPDATE machine SET subarch_id=:subarch_id WHERE subarch_id IS NULL')
    session.execute(s, {'subarch_id': subarch_id})

    s = sa.sql.text('UPDATE image SET arch_id=:arch_id WHERE arch_id IS NULL')
    session.execute(s, {'arch_id': arch_id})

    session.commit()

    op.alter_column('machine', 'arch_id', nullable=False)
    op.alter_column('image', 'arch_id', nullable=False)


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'machine', type_='foreignkey')
    op.drop_constraint(None, 'machine', type_='foreignkey')
    op.drop_column('machine', 'subarch_id')
    op.drop_column('machine', 'arch_id')
    op.drop_constraint(None, 'image', type_='foreignkey')
    op.drop_column('image', 'arch_id')
    op.drop_index('subarch_arch_name_uniq', table_name='subarch')
    op.drop_table('subarch')
    op.drop_table('arch')
    # ### end Alembic commands ###