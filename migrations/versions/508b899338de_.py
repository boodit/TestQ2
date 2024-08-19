"""empty message

Revision ID: 508b899338de
Revises: 
Create Date: 2024-08-19 22:28:05.081775

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '508b899338de'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('player',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(), nullable=False),
    sa.Column('hashed_password', sa.String(), nullable=False),
    sa.Column('active', sa.Enum('in_game', 'out_game', name='active'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('username')
    )
    op.create_table('game',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('first_player_id', sa.Integer(), nullable=False),
    sa.Column('second_player_id', sa.Integer(), nullable=False),
    sa.Column('first_player_board', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('second_player_board', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('game_end', sa.Boolean(), nullable=False),
    sa.Column('winner_id', sa.Integer(), nullable=True),
    sa.Column('end_data', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['first_player_id'], ['player.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['second_player_id'], ['player.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['winner_id'], ['player.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('game')
    op.drop_table('player')
    # ### end Alembic commands ###
