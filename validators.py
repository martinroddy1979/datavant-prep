"""Reusable validators for DataPacket using Pydantic v2 
with Annotated and AfterValidator."""

import hashlib
import os
import re
from typing import Annotated

from dotenv import load_dotenv
from pydantic import AfterValidator

load_dotenv()


def validate_packet_id(value: str) -> str:
    """Validate packet ID format: DV-XXXX where X is a digit."""
    if not re.match(r"^DV-\d{4}$", value):
        raise ValueError("Packet ID must match format DV-XXXX (e.g., DV-0001)")
    return value


def validate_provider_name(value: str) -> str:
    """Validate provider name is in Title Case."""
    if not value.istitle():
        raise ValueError("Provider name must be in Title Case")
    return value


def validate_records_count(value: int) -> int:
    """Validate records count is between 1 and 1000."""
    if not (1 <= value <= 1000):
        raise ValueError("Records count must be between 1 and 1000")
    return value


def validate_uppercase(value: str) -> str:
    """Validate string is all uppercase."""
    if not value.isupper():
        raise ValueError("Value must be all uppercase")
    return value



def generate_token(v: str) -> str:
    """
    The Anonymizer: Turns a string into a 64-character hex token.
    In the real world, we'd add a 'salt' (a secret key) here.
    """
    # We encode the string to bytes, then hash it
    return hashlib.sha256(v.encode()).hexdigest()

SHARED_SECRET_SALT = os.getenv("SHARED_SECRET_SALT")
if SHARED_SECRET_SALT is None:
    raise RuntimeError("SHARED_SECRET_SALT must be set in the environment or .env file")


def generate_secure_token(v: str) -> str:
    """Standardized Datavant-style tokenization."""
    combined = f"{v.strip().lower()}{SHARED_SECRET_SALT}"
    return hashlib.sha256(combined.encode()).hexdigest()


# Type aliases using Annotated for reusability
PacketId = Annotated[str, AfterValidator(validate_packet_id)]
ProviderName = Annotated[str, AfterValidator(validate_provider_name)]
RecordsCount = Annotated[int, AfterValidator(validate_records_count)]
UppercaseString = Annotated[str, AfterValidator(validate_uppercase)]
SanitizedString = Annotated[str, AfterValidator(lambda x: x.strip())]
