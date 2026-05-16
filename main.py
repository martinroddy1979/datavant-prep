from typing import Annotated

from pydantic import AfterValidator, BaseModel

from validators import (
    generate_secure_token,
)

# This type will automatically turn any string into a hash
SecureToken = Annotated[str, AfterValidator(generate_secure_token)]


class PatientRecord(BaseModel):
    patient_id: str
    # When we assign a name here, it will be stored as a hash!
    patient_name_token: SecureToken 
    diagnosis_code: str

# --- THE ACTION ---
print("\n--- TEST: Tokenizing Patient Data ---")
record = PatientRecord(
    patient_id="P-101", 
    patient_name_token="Martin", 
    diagnosis_code="Z00.0"
)

print("Original Name: 'Martin'")
print(f"Stored Token:  {record.patient_name_token}")

# class PatientRecord(BaseModel):
#     patient_id: str
#     # When we assign a name here, it will be stored as a hash!
#     patient_name_token: SecureToken 
#     diagnosis_code: str

# class DataPacket(BaseModel):
#     """Data packet model with reusable validated fields."""
#     packet_id: PacketId
#     provider_name: ProviderName
#     records_count: RecordsCount
#     department_code: UppercaseString
#     received_at: datetime = datetime.now()
#     tags: list[str] = []
#     username: SanitizedString = "  default_user  "

# # --- Test the Logic ---
# try:
#     # This will fail (wrong ID format, lowercase name, and lowercase department code)
#     bad_data = DataPacket(
#         packet_id="123", 
#         provider_name="hospitals_inc", 
#         records_count=0, 
#         department_code="hrm"
#     )
# except Exception as e:
#     print(f"\n❌ Validation Caught Error: \n{e}")

# # This will succeed
# good_data = DataPacket(
#     packet_id="DV-9999", 
#     provider_name="Mayo Clinic", 
#     records_count=500, 
#     department_code="CARDIO"
# )# Fix for line 35 (image_27e291.png)
# print(
#     f"\n✅ Success! Packet {good_data.packet_id} "
#     f"verified for {good_data.provider_name} in "
#     f"department {good_data.department_code}."
# )

# # Another successful example
# good_data2 = DataPacket(
#     packet_id="DV-0001",
#     provider_name="Fonegal Clinic",
#     records_count=500,
#     department_code="ONCOLOGY",
#     tags=["priority", "verified",
#     ],
#     username="  alice_smith  "
# )
# print(
#     f"Success! {good_data2.provider_name} "
#     f"({good_data2.department_code}) at {good_data2.received_at} "
#     f"for {good_data2.username}. Tags: {good_data2.tags}"
# )