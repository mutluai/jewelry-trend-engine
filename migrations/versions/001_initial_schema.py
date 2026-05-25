"""Initial schema — all tables

Revision ID: 001
Revises:
Create Date: 2026-05-25
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    op.create_table(
        "brands",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), unique=True, nullable=False),
        sa.Column("market", sa.String(500)),
        sa.Column("style_focus", sa.String(500)),
        sa.Column("target_customer", sa.Text),
        sa.Column("price_min", sa.Float),
        sa.Column("price_max", sa.Float),
        sa.Column("categories", sa.Text),
        sa.Column("report_language", sa.String(10), server_default="tr"),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "competitors",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("brand_id", UUID(as_uuid=True), sa.ForeignKey("brands.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("website_url", sa.String(500)),
        sa.Column("etsy_shop_id", sa.String(100)),
        sa.Column("market_position", sa.String(100)),
        sa.Column("price_range_min", sa.Float),
        sa.Column("price_range_max", sa.Float),
        sa.Column("product_count", sa.Integer, server_default="0"),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "sources",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.String(100), unique=True, nullable=False),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("connector_class", sa.String(100), nullable=False),
        sa.Column("legal_status", sa.String(50), nullable=False),
        sa.Column("is_enabled", sa.Boolean, server_default="true"),
        sa.Column("rate_limit_seconds", sa.Float, server_default="3.0"),
        sa.Column("description", sa.Text),
        sa.Column("docs_url", sa.String(500)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "source_runs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("source_id", UUID(as_uuid=True), sa.ForeignKey("sources.id"), nullable=False),
        sa.Column("status", sa.String(20), server_default="running"),
        sa.Column("records_fetched", sa.Integer, server_default="0"),
        sa.Column("records_saved", sa.Integer, server_default="0"),
        sa.Column("records_failed", sa.Integer, server_default="0"),
        sa.Column("error_message", sa.Text),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("duration_seconds", sa.Float),
        sa.Column("meta", JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "categories",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.String(100), unique=True, nullable=False),
        sa.Column("name_tr", sa.String(100)),
        sa.Column("slug", sa.String(100), unique=True, nullable=False),
        sa.Column("parent_id", sa.String(36)),
        sa.Column("sort_order", sa.Integer, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "materials",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.String(100), unique=True, nullable=False),
        sa.Column("name_tr", sa.String(100)),
        sa.Column("slug", sa.String(100), unique=True, nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "stones",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.String(100), unique=True, nullable=False),
        sa.Column("name_tr", sa.String(100)),
        sa.Column("slug", sa.String(100), unique=True, nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "colors",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.String(100), unique=True, nullable=False),
        sa.Column("name_tr", sa.String(100)),
        sa.Column("hex_code", sa.String(7)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "style_tags",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.String(100), unique=True, nullable=False),
        sa.Column("name_tr", sa.String(100)),
        sa.Column("slug", sa.String(100), unique=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "products",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("source_id", UUID(as_uuid=True), sa.ForeignKey("sources.id")),
        sa.Column("brand_id", UUID(as_uuid=True), sa.ForeignKey("brands.id")),
        sa.Column("competitor_id", UUID(as_uuid=True), sa.ForeignKey("competitors.id")),
        sa.Column("category_id", UUID(as_uuid=True), sa.ForeignKey("categories.id")),
        sa.Column("external_id", sa.String(255)),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("source_url", sa.String(1000)),
        sa.Column("image_url", sa.String(1000)),
        sa.Column("price", sa.Float),
        sa.Column("currency", sa.String(10)),
        sa.Column("price_usd", sa.Float),
        sa.Column("review_count", sa.Integer, server_default="0"),
        sa.Column("review_rating", sa.Float),
        sa.Column("sales_count", sa.Integer, server_default="0"),
        sa.Column("favorites_count", sa.Integer, server_default="0"),
        sa.Column("target_gender", sa.String(50)),
        sa.Column("price_tier", sa.String(50)),
        sa.Column("theme", sa.String(255)),
        sa.Column("status", sa.String(20), server_default="raw"),
        sa.Column("is_mock", sa.Boolean, server_default="false"),
        sa.Column("collected_at", sa.DateTime(timezone=True)),
        sa.Column("ai_attributes", JSONB),
        sa.Column("ai_analyzed_at", sa.DateTime(timezone=True)),
        sa.Column("ai_model_used", sa.String(100)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # Junction tables
    op.create_table(
        "product_materials",
        sa.Column("product_id", UUID(as_uuid=True), sa.ForeignKey("products.id"), primary_key=True),
        sa.Column("material_id", UUID(as_uuid=True), sa.ForeignKey("materials.id"), primary_key=True),
    )
    op.create_table(
        "product_stones",
        sa.Column("product_id", UUID(as_uuid=True), sa.ForeignKey("products.id"), primary_key=True),
        sa.Column("stone_id", UUID(as_uuid=True), sa.ForeignKey("stones.id"), primary_key=True),
    )
    op.create_table(
        "product_colors",
        sa.Column("product_id", UUID(as_uuid=True), sa.ForeignKey("products.id"), primary_key=True),
        sa.Column("color_id", UUID(as_uuid=True), sa.ForeignKey("colors.id"), primary_key=True),
    )
    op.create_table(
        "product_style_tags",
        sa.Column("product_id", UUID(as_uuid=True), sa.ForeignKey("products.id"), primary_key=True),
        sa.Column("style_tag_id", UUID(as_uuid=True), sa.ForeignKey("style_tags.id"), primary_key=True),
    )

    op.create_table(
        "product_snapshots",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("product_id", UUID(as_uuid=True), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("price", sa.Float),
        sa.Column("price_usd", sa.Float),
        sa.Column("review_count", sa.Integer, server_default="0"),
        sa.Column("review_rating", sa.Float),
        sa.Column("sales_count", sa.Integer, server_default="0"),
        sa.Column("favorites_count", sa.Integer, server_default="0"),
        sa.Column("is_available", sa.Boolean, server_default="true"),
        sa.Column("snapshot_data", JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "image_assets",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("product_id", UUID(as_uuid=True), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("source_url", sa.String(1000)),
        sa.Column("storage_path", sa.String(500)),
        sa.Column("storage_url", sa.String(1000)),
        sa.Column("width", sa.Integer),
        sa.Column("height", sa.Integer),
        sa.Column("file_size_bytes", sa.Integer),
        sa.Column("content_type", sa.String(100)),
        sa.Column("is_primary", sa.Boolean, server_default="false"),
        sa.Column("ai_visual_tags", JSONB),
        sa.Column("ai_style_description", sa.Text),
        sa.Column("ai_material_guess", sa.String(255)),
        sa.Column("ai_analyzed_at", sa.String(50)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "trend_signals",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("signal_type", sa.String(100), nullable=False),
        sa.Column("keyword", sa.String(255)),
        sa.Column("category", sa.String(100)),
        sa.Column("material", sa.String(100)),
        sa.Column("style", sa.String(100)),
        sa.Column("interest_value", sa.Float),
        sa.Column("trend_direction", sa.String(20)),
        sa.Column("velocity_score", sa.Float),
        sa.Column("confidence", sa.Float),
        sa.Column("source_name", sa.String(100)),
        sa.Column("geo", sa.String(10)),
        sa.Column("period_start", sa.DateTime(timezone=True)),
        sa.Column("period_end", sa.DateTime(timezone=True)),
        sa.Column("ai_analysis", JSONB),
        sa.Column("raw_data", JSONB),
        sa.Column("is_mock", sa.Boolean, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "trend_signal_products",
        sa.Column("trend_signal_id", UUID(as_uuid=True), sa.ForeignKey("trend_signals.id"), primary_key=True),
        sa.Column("product_id", UUID(as_uuid=True), sa.ForeignKey("products.id"), primary_key=True),
    )

    op.create_table(
        "opportunity_scores",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("product_id", UUID(as_uuid=True), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("total_score", sa.Float, nullable=False),
        sa.Column("trend_velocity_score", sa.Float),
        sa.Column("cross_source_score", sa.Float),
        sa.Column("competition_density_score", sa.Float),
        sa.Column("novelty_score", sa.Float),
        sa.Column("brand_fit_score", sa.Float),
        sa.Column("review_signal_score", sa.Float),
        sa.Column("score_version", sa.String(20), server_default="1.0"),
        sa.Column("score_breakdown", JSONB),
        sa.Column("ai_opportunity_narrative", sa.Text),
        sa.Column("ai_recommendation", sa.Text),
        sa.Column("ai_risk_notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "reports",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("report_type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("language", sa.String(10), server_default="tr"),
        sa.Column("content_markdown", sa.Text),
        sa.Column("storage_path", sa.String(500)),
        sa.Column("storage_url", sa.String(1000)),
        sa.Column("period_start", sa.String(50)),
        sa.Column("period_end", sa.String(50)),
        sa.Column("product_count", sa.Integer, server_default="0"),
        sa.Column("signal_count", sa.Integer, server_default="0"),
        sa.Column("ai_model_used", sa.String(100)),
        sa.Column("ai_tokens_used", sa.Integer, server_default="0"),
        sa.Column("email_sent", sa.Boolean, server_default="false"),
        sa.Column("slack_sent", sa.Boolean, server_default="false"),
        sa.Column("meta", JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "alerts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("alert_type", sa.String(100), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("message", sa.Text),
        sa.Column("severity", sa.String(20), server_default="info"),
        sa.Column("threshold_value", sa.Float),
        sa.Column("actual_value", sa.Float),
        sa.Column("is_sent", sa.Boolean, server_default="false"),
        sa.Column("sent_via_email", sa.Boolean, server_default="false"),
        sa.Column("sent_via_slack", sa.Boolean, server_default="false"),
        sa.Column("resolved", sa.Boolean, server_default="false"),
        sa.Column("meta", JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "connector_configs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.String(100), unique=True, nullable=False),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("is_enabled", sa.Boolean, server_default="true"),
        sa.Column("rate_limit_seconds", sa.Float, server_default="3.0"),
        sa.Column("max_records_per_run", sa.Integer),
        sa.Column("legal_status", sa.String(50), nullable=False),
        sa.Column("legal_notes", sa.Text),
        sa.Column("config_json", JSONB),
        sa.Column("last_run_at", sa.String(50)),
        sa.Column("last_run_status", sa.String(20)),
        sa.Column("last_error", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "app_settings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("key", sa.String(100), unique=True, nullable=False),
        sa.Column("value", sa.Text),
        sa.Column("value_type", sa.String(20), server_default="string"),
        sa.Column("description", sa.Text),
        sa.Column("category", sa.String(50)),
        sa.Column("is_secret", sa.Boolean, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # Indexes
    op.create_index("ix_products_status", "products", ["status"])
    op.create_index("ix_products_is_mock", "products", ["is_mock"])
    op.create_index("ix_products_collected_at", "products", ["collected_at"])
    op.create_index("ix_opportunity_scores_total_score", "opportunity_scores", ["total_score"])
    op.create_index("ix_trend_signals_direction", "trend_signals", ["trend_direction"])
    op.create_index("ix_trend_signals_keyword", "trend_signals", ["keyword"])
    op.create_index("ix_source_runs_source_id", "source_runs", ["source_id"])
    op.create_index("ix_reports_report_type", "reports", ["report_type"])


def downgrade() -> None:
    tables = [
        "app_settings", "connector_configs", "alerts", "reports",
        "opportunity_scores", "trend_signal_products", "trend_signals",
        "image_assets", "product_snapshots", "product_style_tags",
        "product_colors", "product_stones", "product_materials",
        "products", "style_tags", "colors", "stones", "materials",
        "categories", "source_runs", "sources", "competitors", "brands",
    ]
    for table in tables:
        op.drop_table(table)
