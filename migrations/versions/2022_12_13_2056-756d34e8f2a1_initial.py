"""initial

Revision ID: 756d34e8f2a1
Revises: 
Create Date: 2022-12-13 20:56:24.998937

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '756d34e8f2a1'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('images',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('path', sa.String(length=1024), nullable=False),
    sa.Column('height', sa.Integer(), nullable=False),
    sa.Column('width', sa.Integer(), nullable=False),
    sa.Column('orientation', sa.String(length=10), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    sa.Column('shown_times', sa.Integer(), nullable=False),
    sa.Column('elo_rating', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('path'),
    sqlite_autoincrement=True
    )
    op.create_index(op.f('ix_images_elo_rating'), 'images', ['elo_rating'], unique=False)
    op.create_index(op.f('ix_images_shown_times'), 'images', ['shown_times'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_images_shown_times'), table_name='images')
    op.drop_index(op.f('ix_images_elo_rating'), table_name='images')
    op.drop_table('images')
    # ### end Alembic commands ###
