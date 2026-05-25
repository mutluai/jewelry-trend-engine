from sqlalchemy import String, Text, Integer, Table, Column, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from .base import Base, UUIDMixin, TimestampMixin


product_materials = Table(
    "product_materials",
    Base.metadata,
    Column("product_id", UUID(as_uuid=True), ForeignKey("products.id"), primary_key=True),
    Column("material_id", UUID(as_uuid=True), ForeignKey("materials.id"), primary_key=True),
)

product_stones = Table(
    "product_stones",
    Base.metadata,
    Column("product_id", UUID(as_uuid=True), ForeignKey("products.id"), primary_key=True),
    Column("stone_id", UUID(as_uuid=True), ForeignKey("stones.id"), primary_key=True),
)

product_colors = Table(
    "product_colors",
    Base.metadata,
    Column("product_id", UUID(as_uuid=True), ForeignKey("products.id"), primary_key=True),
    Column("color_id", UUID(as_uuid=True), ForeignKey("colors.id"), primary_key=True),
)

product_style_tags = Table(
    "product_style_tags",
    Base.metadata,
    Column("product_id", UUID(as_uuid=True), ForeignKey("products.id"), primary_key=True),
    Column("style_tag_id", UUID(as_uuid=True), ForeignKey("style_tags.id"), primary_key=True),
)


class Category(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "categories"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name_tr: Mapped[str | None] = mapped_column(String(100))
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    parent_id: Mapped[str | None] = mapped_column(String(36))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    products: Mapped[list["Product"]] = relationship(back_populates="category")


class Material(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "materials"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name_tr: Mapped[str | None] = mapped_column(String(100))
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    products: Mapped[list["Product"]] = relationship(
        secondary=product_materials, back_populates="materials"
    )


class Stone(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "stones"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name_tr: Mapped[str | None] = mapped_column(String(100))
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    products: Mapped[list["Product"]] = relationship(
        secondary=product_stones, back_populates="stones"
    )


class Color(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "colors"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name_tr: Mapped[str | None] = mapped_column(String(100))
    hex_code: Mapped[str | None] = mapped_column(String(7))

    products: Mapped[list["Product"]] = relationship(
        secondary=product_colors, back_populates="colors"
    )


class StyleTag(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "style_tags"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name_tr: Mapped[str | None] = mapped_column(String(100))
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    products: Mapped[list["Product"]] = relationship(
        secondary=product_style_tags, back_populates="style_tags"
    )
