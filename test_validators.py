import hashlib
import os

import pytest
from pydantic import BaseModel

from validators import (
    PacketId,
    ProviderName,
    RecordsCount,
    SanitizedString,
    UppercaseString,
    generate_secure_token,
    validate_packet_id,
    validate_provider_name,
    validate_records_count,
    validate_uppercase,
)


class SampleModel(BaseModel):
    packet_id: PacketId
    provider_name: ProviderName
    records_count: RecordsCount
    uppercase_code: UppercaseString
    sanitized_text: SanitizedString


def test_validate_packet_id_accepts_valid_format():
    assert validate_packet_id("DV-1234") == "DV-1234"


def test_validate_packet_id_rejects_invalid_format():
    with pytest.raises(ValueError, match="Packet ID must match format DV-XXXX"):
        validate_packet_id("1234")


def test_validate_provider_name_rejects_lowercase_name():
    with pytest.raises(ValueError, match="Provider name must be in Title Case"):
        validate_provider_name("not title case")


def test_validate_records_count_rejects_out_of_range():
    with pytest.raises(ValueError, match="Records count must be between 1 and 1000"):
        validate_records_count(0)


def test_validate_uppercase_rejects_non_uppercase():
    with pytest.raises(ValueError, match="Value must be all uppercase"):
        validate_uppercase("MixedCase")


def test_sanitized_string_strips_whitespace():
    model = SampleModel(
        packet_id="DV-0001",
        provider_name="Mayo Clinic",
        records_count=10,
        uppercase_code="ABC",
        sanitized_text="  trimmed  ",
    )
    assert model.sanitized_text == "trimmed"


def test_uppercase_string_validates_uppercase():
    model = SampleModel(
        packet_id="DV-0001",
        provider_name="Mayo Clinic",
        records_count=10,
        uppercase_code="XYZ",
        sanitized_text="hello",
    )
    assert model.uppercase_code == "XYZ"


def test_generate_secure_token_is_consistent():
    source = "TestValue"
    
    # Dynamically get whatever salt the system is currently using
    current_salt = os.environ.get("SHARED_SECRET_SALT", "donegal-fortress-2026")
    
    # Calculate the expected hash using the dynamic salt
    combined = f"{source.strip().lower()}{current_salt}"
    expected = hashlib.sha256(combined.encode()).hexdigest()
    
    assert generate_secure_token(source) == expected

def test_token_determinism():
    # Rule: Same input must ALWAYS yield same output
    input_name = "  Martin  "
    token1 = generate_secure_token(input_name)
    token2 = generate_secure_token(input_name)
    assert token1 == token2
    # Rule: It should not be the raw name
    assert "Martin" not in token1

def test_token_consistency():
    # Ensure 'martin' and 'MARTIN' result in same token (Sanitization)
    assert generate_secure_token("martin") == generate_secure_token("MARTIN")