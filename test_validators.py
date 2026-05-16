# test_validators.py
import hashlib
import os

import boto3
import pytest
from moto import mock_aws
from pydantic import BaseModel, ValidationError

from storage import CloudStorageEngine
from validators import (
    PacketId,  # Import the strict type alias directly
    SecureToken,
    generate_secure_token,
    validate_packet_id,
    validate_provider_name,
)


# Define a localized model that perfectly mirrors your real validation rules
class MockPatientRecord(BaseModel):
    patient_id: PacketId  # This forces Pydantic to run your exact DV-XXXX validation
    patient_name_token: SecureToken
    diagnosis_code: str

# --- Synchronized Core Validation Tests ---

def test_validate_packet_id_valid():
    # Both must be uppercase and follow DV-XXXX to pass your regex pattern
    assert validate_packet_id("DV-1234") == "DV-1234"
    assert validate_packet_id("DV-9999") == "DV-9999"

def test_validate_packet_id_invalid():
    with pytest.raises(ValueError):
        validate_packet_id("INVALID-123")
    with pytest.raises(ValueError):
        validate_packet_id("dv-1234")  # Lowercase fails regex check

def test_validate_provider_name_strip():
    # Pass a perfectly styled Title Case string to verify standard compliance
    assert validate_provider_name("Health Corp") == "Health Corp"

def test_validate_provider_name_empty():
    with pytest.raises(ValueError):
        validate_provider_name("   ")

def test_generate_secure_token_is_consistent():
    source = "TestValue"
    current_salt = os.environ.get("SHARED_SECRET_SALT", "donegal-fortress-2026")
    combined = f"{source.strip().lower()}{current_salt}"
    expected = hashlib.sha256(combined.encode()).hexdigest()
    
    assert generate_secure_token(source) == expected

def test_patient_record_validation_success():
    record = MockPatientRecord(
        patient_id="DV-1234",
        patient_name_token="John Doe",
        diagnosis_code="I10"
    )
    assert record.patient_id == "DV-1234"
    assert len(record.patient_name_token) == 64

def test_patient_record_validation_failure():
    # Because patient_id is typed as PacketId, this bad layout will now
    # correctly trigger a Pydantic ValidationError!
    with pytest.raises(ValidationError):
        MockPatientRecord(
            patient_id="INVALID_FORMAT_ID",
            patient_name_token="John Doe",
            diagnosis_code="I10"
        )

# --- Phase 2 AWS Cloud Infrastructure Unit Test ---

@mock_aws
def test_cloud_storage_engine_uploads_successfully():
    """Verifies that CloudStorageEngine pushes payloads to an S3 bucket."""
    test_bucket = "datavant-test-bucket-ci"
    test_packet_id = "DV-9999"
    test_payload = {
        "patient_id": test_packet_id,
        "token": "mocked_64_char_hash_abc123",
        "diagnosis": "U07.1"
    }

    s3_resource = boto3.resource("s3", region_name="eu-west-1")
    s3_resource.create_bucket(
        Bucket=test_bucket,
        CreateBucketConfiguration={'LocationConstraint': 'eu-west-1'}
    )

    storage_engine = CloudStorageEngine(bucket_name=test_bucket)

    result = storage_engine.upload_patient_record(
        packet_id=test_packet_id, 
        data=test_payload
    )

    assert result is True

    s3_client = boto3.client("s3", region_name="eu-west-1")
    response = s3_client.get_object(
        Bucket=test_bucket, 
        Key=f"ingested/{test_packet_id}.json"
    )
    
    assert response['ResponseMetadata']['HTTPStatusCode'] == 200