from sqlalchemy import DateTime, func
from sqlalchemy import BigInteger, String, Integer, ForeignKey, DateTime, func
from sqlalchemy.orm import mapped_column, relationship
from .base import Base

class User(Base):
    __tablename__ = "users"

    id = mapped_column(BigInteger, primary_key=True)
    first_name = mapped_column(String(50))
    last_name = mapped_column(String(50))
    referral_code = mapped_column(String(20), unique=True)

    # Referrals – bu user taklif qilganlar
    referrals = relationship("Referral", back_populates="referrer", foreign_keys="Referral.referrer_id")

    # referred_by orqali userni kim taklif qilgani
    referred_by = mapped_column(BigInteger, ForeignKey("users.id"), nullable=True)


class Referral(Base):
    __tablename__ = "referrals"

    id = mapped_column(Integer, primary_key=True)
    user_id = mapped_column(BigInteger, ForeignKey("users.id"))  # taklif qilingan user
    referrer_id = mapped_column(BigInteger, ForeignKey("users.id"))  # taklif qilgan user
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())
    timestamp = mapped_column(DateTime, server_default=func.now())  # qachon taklif qilgan

    referrer = relationship("User", back_populates="referrals", foreign_keys=[referrer_id])
