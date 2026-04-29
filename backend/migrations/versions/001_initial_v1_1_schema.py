"""Initial v1.1 schema migration

Revision ID: 001
Revises:
Create Date: 2026-04-28 21:30:00.000000

Initial database schema capturing v1.1 state.
Tables: audit_requests, audit_violations, agent_executions, tool_calls, tool_approvals
"""
from alembic import op
import sqlalchemy as sa


revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create audit_requests table
    op.create_table(
        'audit_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('prompt', sa.Text(), nullable=True),
        sa.Column('response', sa.Text(), nullable=True),
        sa.Column('model_used', sa.String(), nullable=True),
        sa.Column('tokens_in', sa.Integer(), nullable=True),
        sa.Column('tokens_out', sa.Integer(), nullable=True),
        sa.Column('cost_usd', sa.Float(), nullable=True),
        sa.Column('policy_decision', sa.String(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_audit_requests_timestamp', 'audit_requests', ['timestamp'])
    op.create_index('ix_audit_requests_user_id', 'audit_requests', ['user_id'])

    # Create audit_violations table
    op.create_table(
        'audit_violations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('violation_reason', sa.String(), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_audit_violations_timestamp', 'audit_violations', ['timestamp'])
    op.create_index('ix_audit_violations_user_id', 'audit_violations', ['user_id'])

    # Create agent_executions table
    op.create_table(
        'agent_executions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.String(), nullable=True),
        sa.Column('request_id', sa.String(), nullable=True),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('goal', sa.Text(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('final_response', sa.Text(), nullable=True),
        sa.Column('execution_trace', sa.JSON(), nullable=True),
        sa.Column('tools_called', sa.JSON(), nullable=True),
        sa.Column('total_cost_usd', sa.Float(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('request_id')
    )
    op.create_index('ix_agent_executions_agent_id', 'agent_executions', ['agent_id'])
    op.create_index('ix_agent_executions_request_id', 'agent_executions', ['request_id'])
    op.create_index('ix_agent_executions_user_id', 'agent_executions', ['user_id'])
    op.create_index('ix_agent_executions_timestamp', 'agent_executions', ['timestamp'])

    # Create tool_calls table
    op.create_table(
        'tool_calls',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('execution_id', sa.Integer(), nullable=True),
        sa.Column('tool_name', sa.String(), nullable=True),
        sa.Column('args', sa.JSON(), nullable=True),
        sa.Column('result', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_tool_calls_execution_id', 'tool_calls', ['execution_id'])
    op.create_index('ix_tool_calls_timestamp', 'tool_calls', ['timestamp'])

    # Create tool_approvals table
    op.create_table(
        'tool_approvals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('tool_name', sa.String(), nullable=True),
        sa.Column('args', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('decided_at', sa.DateTime(), nullable=True),
        sa.Column('decision_by', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_tool_approvals_user_id', 'tool_approvals', ['user_id'])
    op.create_index('ix_tool_approvals_created_at', 'tool_approvals', ['created_at'])


def downgrade():
    op.drop_index('ix_tool_approvals_created_at', 'tool_approvals')
    op.drop_index('ix_tool_approvals_user_id', 'tool_approvals')
    op.drop_table('tool_approvals')

    op.drop_index('ix_tool_calls_timestamp', 'tool_calls')
    op.drop_index('ix_tool_calls_execution_id', 'tool_calls')
    op.drop_table('tool_calls')

    op.drop_index('ix_agent_executions_timestamp', 'agent_executions')
    op.drop_index('ix_agent_executions_user_id', 'agent_executions')
    op.drop_index('ix_agent_executions_request_id', 'agent_executions')
    op.drop_index('ix_agent_executions_agent_id', 'agent_executions')
    op.drop_table('agent_executions')

    op.drop_index('ix_audit_violations_user_id', 'audit_violations')
    op.drop_index('ix_audit_violations_timestamp', 'audit_violations')
    op.drop_table('audit_violations')

    op.drop_index('ix_audit_requests_user_id', 'audit_requests')
    op.drop_index('ix_audit_requests_timestamp', 'audit_requests')
    op.drop_table('audit_requests')
