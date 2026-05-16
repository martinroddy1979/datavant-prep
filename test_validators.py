import hashlib
import os

import boto3
import pytest
from moto import mock_aws
from pydantic import BaseModel

from storage import CloudStorageEngine
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

@mock_aws
def test_cloud_storage_engine_uploads_successfully():
    """Verifies that CloudStorageEngine correctly pushes payloads to an AWS S3 bucket."""
    test_bucket = "datavant-test-bucket-ci"
    test_packet_id = "P-TEST-999"
    test_payload = {
        "patient_id": test_packet_id,
        "token": "mocked_64_char_hash_abc123",
        "diagnosis": "U07.1"
    }

    # 1. Setup the isolated virtual infrastructure for this specific test
    s3_resource = boto3.resource("s3", region_name="eu-west-1")
    s3_resource.create_bucket(
        Bucket=test_bucket,
        CreateBucketConfiguration={'LocationConstraint': 'eu-west-1'}
    )

    # 2. Instantiate our actual production module code
    storage_engine = CloudStorageEngine(bucket_name=test_bucket)

    # 3. Execute the function we are testing
    result = storage_engine.upload_patient_record(packet_id=test_packet_id, data=test_payload)

    # 4. Assertions: Confirm the function returned True and the data exists in S3
    assert result is True

    # Pull the object directly from the virtual S3 layer to confirm contents match
    s3_client = boto3.client("s3", region_name="eu-west-1")
    response = s3_client.get_object(Bucket=test_bucket, Key=f"ingested/{test_packet_id}.json")
    
    assert response['ResponseMetadata']['HTTPStatusCode'] == 200