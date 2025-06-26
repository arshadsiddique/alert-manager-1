"""Complete JSM schema - alerts and cron_config tables

Revision ID: 0001
Revises: 
Create Date: 2025-06-26 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create alerts table with all JSM fields
    op.create_table('alerts',
        # Basic alert fields
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('alert_id', sa.String(), nullable=True),
        sa.Column('alert_name', sa.String(), nullable=True),
        sa.Column('cluster', sa.String(), nullable=True),
        sa.Column('pod', sa.String(), nullable=True),
        sa.Column('severity', sa.String(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('generator_url', sa.String(), nullable=True),
        sa.Column('grafana_status', sa.String(), nullable=True, default='active'),
        sa.Column('labels', sa.JSON(), nullable=True),
        sa.Column('annotations', sa.JSON(), nullable=True),
        
        # Legacy Jira fields (for backward compatibility)
        sa.Column('jira_status', sa.String(), nullable=True, default='open'),
        sa.Column('jira_issue_key', sa.String(), nullable=True),
        sa.Column('jira_issue_id', sa.String(), nullable=True),
        sa.Column('jira_issue_url', sa.String(), nullable=True),
        sa.Column('jira_assignee', sa.String(), nullable=True),
        sa.Column('jira_assignee_email', sa.String(), nullable=True),
        
        # Acknowledgment and resolution tracking
        sa.Column('acknowledged_by', sa.String(), nullable=True),
        sa.Column('acknowledged_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_by', sa.String(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        
        # JSM integration fields
        sa.Column('jsm_alert_id', sa.String(), nullable=True),
        sa.Column('jsm_tiny_id', sa.String(), nullable=True),
        sa.Column('jsm_status', sa.String(), nullable=True),
        sa.Column('jsm_acknowledged', sa.Boolean(), nullable=True, default=False),
        sa.Column('jsm_owner', sa.String(), nullable=True),
        sa.Column('jsm_priority', sa.String(), nullable=True),
        sa.Column('jsm_alias', sa.String(), nullable=True),
        sa.Column('jsm_integration_name', sa.String(), nullable=True),
        sa.Column('jsm_source', sa.String(), nullable=True),
        sa.Column('jsm_count', sa.Integer(), nullable=True, default=1),
        sa.Column('jsm_tags', sa.JSON(), nullable=True),
        sa.Column('jsm_last_occurred_at', sa.DateTime(), nullable=True),
        sa.Column('jsm_created_at', sa.DateTime(), nullable=True),
        sa.Column('jsm_updated_at', sa.DateTime(), nullable=True),
        
        # Alert matching metadata
        sa.Column('match_type', sa.String(), nullable=True),
        sa.Column('match_confidence', sa.Float(), nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for alerts table
    op.create_index('ix_alerts_alert_id', 'alerts', ['alert_id'], unique=True)
    op.create_index('ix_alerts_alert_name', 'alerts', ['alert_name'], unique=False)
    op.create_index('ix_alerts_id', 'alerts', ['id'], unique=False)
    op.create_index('ix_alerts_cluster', 'alerts', ['cluster'])
    op.create_index('ix_alerts_severity', 'alerts', ['severity'])
    op.create_index('ix_alerts_grafana_status', 'alerts', ['grafana_status'])
    op.create_index('ix_alerts_jira_status', 'alerts', ['jira_status'])
    
    # JSM-specific indexes
    op.create_index('ix_alerts_jsm_alert_id', 'alerts', ['jsm_alert_id'])
    op.create_index('ix_alerts_jsm_tiny_id', 'alerts', ['jsm_tiny_id'])
    op.create_index('ix_alerts_jsm_status', 'alerts', ['jsm_status'])
    op.create_index('ix_alerts_jsm_acknowledged', 'alerts', ['jsm_acknowledged'])
    op.create_index('ix_alerts_match_type', 'alerts', ['match_type'])
    
    # Composite indexes for performance
    op.create_index('ix_alerts_status_created', 'alerts', ['grafana_status', 'created_at'])
    op.create_index('ix_alerts_jsm_status_created', 'alerts', ['jsm_status', 'created_at'])
    op.create_index('ix_alerts_match_confidence', 'alerts', ['match_type', 'match_confidence'])
    
    # Create cron_config table
    op.create_table('cron_config',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_name', sa.String(), nullable=True),
        sa.Column('cron_expression', sa.String(), nullable=True),
        sa.Column('is_enabled', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('job_name')
    )
    
    # Insert default cron jobs for JSM alert synchronization
    op.execute("""
        INSERT INTO cron_config (job_name, cron_expression, is_enabled, created_at, updated_at)
        VALUES 
            ('grafana-jsm-sync', '*/5 * * * *', true, NOW(), NOW()),
            ('jsm-status-sync', '*/2 * * * *', true, NOW(), NOW())
    """)


def downgrade() -> None:
    # Drop cron_config table
    op.drop_table('cron_config')
    
    # Drop alerts indexes
    op.drop_index('ix_alerts_match_confidence', table_name='alerts')
    op.drop_index('ix_alerts_jsm_status_created', table_name='alerts')
    op.drop_index('ix_alerts_status_created', table_name='alerts')
    op.drop_index('ix_alerts_match_type', table_name='alerts')
    op.drop_index('ix_alerts_jsm_acknowledged', table_name='alerts')
    op.drop_index('ix_alerts_jsm_status', table_name='alerts')
    op.drop_index('ix_alerts_jsm_tiny_id', table_name='alerts')
    op.drop_index('ix_alerts_jsm_alert_id', table_name='alerts')
    op.drop_index('ix_alerts_jira_status', table_name='alerts')
    op.drop_index('ix_alerts_grafana_status', table_name='alerts')
    op.drop_index('ix_alerts_severity', table_name='alerts')
    op.drop_index('ix_alerts_cluster', table_name='alerts')
    op.drop_index('ix_alerts_id', table_name='alerts')
    op.drop_index('ix_alerts_alert_name', table_name='alerts')
    op.drop_index('ix_alerts_alert_id', table_name='alerts')
    
    # Drop alerts table
    op.drop_table('alerts')
