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
    """Simulates a secure ingestion run processing data into AWS infrastructure."""
    log.info("system_boot", message="Initializing Secure Ingestion Vessel with AWS S3 Engine")
    
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

  # 5. THE INFRASTRUCTURE INSPECTOR & VISUALISER
        log.info("aws_s3_inventory_scan", message="Scanning virtual S3 bucket contents")
        
        s3_client = boto3.client("s3", region_name="eu-west-1")
        
        # List all objects inside our mocked bucket
        bucket_objects = s3_client.list_objects_v2(Bucket=BUCKET_NAME)
        
        for obj in bucket_objects.get('Contents', []):
            file_key = obj['Key']
            print(f"\n📁 [VIRTUAL S3 BUCKET] Found File: s3://{BUCKET_NAME}/{file_key}")
            
            # Fetch the actual file content
            file_response = s3_client.get_object(Bucket=BUCKET_NAME, Key=file_key)
            raw_body = file_response['Body'].read().decode('utf-8')
            
            # Pretty-print the JSON payload sitting in the cloud
            parsed_json = json.loads(raw_body)
            print("📄 [FILE CONTENT ON AWS]:")
            print(json.dumps(parsed_json, indent=4))
            print("-" * 50)

    except ValidationError:
        
        # Pull the streaming bytes back out of the virtual bucket and parse the JSON
        uploaded_content = json.loads(response['Body'].read().decode('utf-8'))
        
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