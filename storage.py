# storage.py
import json

import boto3

from logger import log


class CloudStorageEngine:
    def __init__(self, bucket_name: str):
        self.bucket_name = bucket_name
        # Initialize a standard AWS S3 client pointing to a default production region
        self.s3_client = boto3.client("s3", region_name="eu-west-1")

    def upload_patient_record(self, packet_id: str, data: dict) -> bool:
        """Serializes and uploads a secure data packet to an Amazon S3 bucket."""
        try:
            object_key = f"ingested/{packet_id}.json"
            json_data = json.dumps(data)

            log.info("aws_s3_upload_start", bucket=self.bucket_name, key=object_key)
            
            # Write the data packet directly to the S3 bucket surface
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=object_key,
                Body=json_data,
                ContentType="application/json"
            )
            
            log.info("aws_s3_upload_success", bucket=self.bucket_name, key=object_key)
            return True
            
        except Exception as e:
            log.error("aws_s3_upload_failure", error=str(e), packet_id=packet_id)
            return False