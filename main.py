# main.py
import json

import boto3
from moto import mock_aws
from pydantic import BaseModel, ValidationError

from logger import log
from storage import CloudStorageEngine
from validators import SecureToken

BUCKET_NAME = "datavant-patient-tokens-prod"

class PatientRecord(BaseModel):
    patient_id: str
    patient_name_token: SecureToken 
    diagnosis_code: str

@mock_aws
def run_pipeline():
    """Simulates a secure ingestion run processing data into AWS."""
    log.info(
        "system_boot", 
        message="Initializing Secure Ingestion Vessel with AWS S3 Engine"
    )
    
    # 1. Setup our mocked cloud infrastructure locally
    s3_resource = boto3.resource("s3", region_name="eu-west-1")
    s3_resource.create_bucket(
        Bucket=BUCKET_NAME,
        CreateBucketConfiguration={'LocationConstraint': 'eu-west-1'}
    )
    
    # Initialize our application storage interface
    storage = CloudStorageEngine(bucket_name=BUCKET_NAME)

    try:
        # 2. Ingest and Tokenize raw data incoming at the edge
        log.info("processing_record", patient_id="P-101")
        record = PatientRecord(
            patient_id="P-101", 
            patient_name_token="Martin", 
            diagnosis_code="Z00.0"
        )
        
        # 3. Formulate the secure cloud payload
        payload = {
            "patient_id": record.patient_id,
            "token": record.patient_name_token,
            "diagnosis": record.diagnosis_code
        }
        
        # 4. Hand off the cargo to the storage engine
        storage.upload_patient_record(packet_id=record.patient_id, data=payload)

        # 5. THE INFRASTRUCTURE INSPECTOR: Verify the cloud destination state
        log.info("aws_s3_verification_start", target_bucket=BUCKET_NAME)
        
        s3_client = boto3.client("s3", region_name="eu-west-1")
        response = s3_client.get_object(
            Bucket=BUCKET_NAME,
            Key=f"ingested/{record.patient_id}.json"
        )
        
        # Pull streaming bytes back out of the virtual bucket & parse JSON
        uploaded_content = json.loads(response['Body'].read().decode('utf-8'))
        
        # Explicit print statement to see the full raw un-sliced hash data
        print("\n🔍 [RAW DE-IDENTIFIED CLOUD DATA] Inspecting full S3 Object:")
        print(f"🔒 Full SHA-256 Patient Token: {uploaded_content['token']}")
        print(f"📋 Full Payload JSON:\n{json.dumps(uploaded_content, indent=2)}\n")

        log.info(
            "aws_s3_verification_success",
            verified_patient_id=uploaded_content["patient_id"],
            verified_token_preview=f"{uploaded_content['token'][:8]}...",
            status="MATCHED_AND_SECURE"
        )

    except ValidationError as e:
        log.error("validation_failure", errors=e.errors())
    except Exception as e:
        log.critical("infrastructure_corruption", error=str(e))

if __name__ == "__main__":
    run_pipeline()