import hashlib
import secrets
import string
from datetime import datetime


def generate_certificate_id(course_code: str = "GEN", year: int = None) -> str:
    """Generate unique certificate ID like ACV-2026-IT-A3F9B2"""
    if year is None:
        year = datetime.now().year
    rand_part = secrets.token_hex(3).upper()
    return f"ACV-{year}-{course_code.upper()}-{rand_part}"


def compute_certificate_hash(cert_data: dict) -> str:
    """Compute SHA-256 hash of certificate canonical string."""
    canonical = (
        f"{cert_data['certificate_id']}|"
        f"{cert_data['student_id']}|"
        f"{cert_data['student_name']}|"
        f"{cert_data['course']}|"
        f"{cert_data['branch']}|"
        f"{cert_data['grade']}|"
        f"{cert_data['issue_date']}|"
        f"{cert_data['institution_name']}"
    )
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()


def verify_certificate_hash(cert_data: dict, stored_hash: str) -> bool:
    """Verify whether computed hash matches stored hash."""
    computed = compute_certificate_hash(cert_data)
    return computed == stored_hash
