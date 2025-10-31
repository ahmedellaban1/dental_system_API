from django.core.exceptions import ValidationError
import re
from datetime import datetime, date


def validate_password_strength(password):
    """
    Validates that the password meets required strength:
    - At least 8 characters
    - At least one lowercase letter
    - At least one uppercase letter
    - At least one digit
    - At least one special character
    """
    pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'

    if not re.match(pattern, password):
        raise ValidationError(
            "Password must be at least 8 characters long and include at least one uppercase letter, "
            "one lowercase letter, one digit, and one special character (@$!%*?&)."
        )


def validate_egyptian_phone(phone):
    """
    Validates Egyptian phone numbers:
    - Must start with +20 or 01
    - Must be 11 digits (without +20) or 13 digits (with +20)
    """
    pattern = r'^(\+20|0)?1[0125]\d{8}$'
    
    if not re.match(pattern, phone):
        raise ValidationError(
            "Phone number must be a valid Egyptian number (e.g., 01012345678 or +201012345678)."
        )


def validate_national_id(national_id):
    """
    Validates Egyptian National ID:
    - Must be exactly 14 digits
    - First digit must be 2 or 3
    """
    pattern = r'^[23]\d{13}$'
    
    if not re.match(pattern, str(national_id)):
        raise ValidationError(
            "National ID must be exactly 14 digits and start with 2 or 3."
        )


def validate_age(birth_date):
    """
    Validates that age is reasonable (between 0 and 150 years)
    """
    if isinstance(birth_date, str):
        birth_date = datetime.strptime(birth_date, '%Y-%m-%d').date()
    
    today = date.today()
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    
    if age < 0:
        raise ValidationError("Birth date cannot be in the future.")
    
    if age > 150:
        raise ValidationError("Age cannot be more than 150 years.")


def validate_future_date(appointment_date):
    """
    Validates that appointment date is in the future
    """
    if isinstance(appointment_date, str):
        appointment_date = datetime.strptime(appointment_date, '%Y-%m-%d %H:%M:%S')
    
    if appointment_date <= datetime.now():
        raise ValidationError("Appointment date must be in the future.")


def validate_medical_license(license_number):
    """
    Validates medical license number format
    - Must be alphanumeric
    - Between 6 and 20 characters
    """
    pattern = r'^[A-Z0-9]{6,20}$'
    
    if not re.match(pattern, license_number.upper()):
        raise ValidationError(
            "Medical license must be 6-20 alphanumeric characters."
        )


def validate_file_size(file):
    """
    Validates file size (max 5MB)
    """
    max_size = 5 * 1024 * 1024  # 5MB
    
    if file.size > max_size:
        raise ValidationError(
            f"File size must not exceed 5MB. Current size: {file.size / (1024 * 1024):.2f}MB"
        )


def validate_image_file(file):
    """
    Validates that file is an image
    """
    valid_extensions = ['.jpg', '.jpeg', '.png', '.gif']
    ext = file.name.lower().split('.')[-1]
    
    if f'.{ext}' not in valid_extensions:
        raise ValidationError(
            f"Only image files are allowed: {', '.join(valid_extensions)}"
        )


def validate_pdf_file(file):
    """
    Validates that file is a PDF
    """
    if not file.name.lower().endswith('.pdf'):
        raise ValidationError("Only PDF files are allowed.")


def validate_working_hours(start_time, end_time):
    """
    Validates working hours:
    - Start time must be before end time
    - Both must be within 24 hours
    """
    if start_time >= end_time:
        raise ValidationError("Start time must be before end time.")
    
    time_diff = (datetime.combine(date.today(), end_time) - 
                 datetime.combine(date.today(), start_time)).seconds / 3600
    
    if time_diff > 12:
        raise ValidationError("Working hours cannot exceed 12 hours per shift.")


def validate_salary(salary):
    """
    Validates salary amount
    """
    if salary < 0:
        raise ValidationError("Salary cannot be negative.")
    
    if salary > 1000000:
        raise ValidationError("Salary seems unreasonably high. Please verify.")


def validate_percentage(value):
    """
    Validates percentage values (0-100)
    """
    if value < 0 or value > 100:
        raise ValidationError("Value must be between 0 and 100.")


def validate_positive_number(value):
    """
    Validates that number is positive
    """
    if value < 0:
        raise ValidationError("Value must be positive.")


def validate_prescription_dosage(dosage):
    """
    Validates prescription dosage format
    - Must contain number and unit (e.g., "500mg", "2 tablets")
    """
    pattern = r'^\d+(\.\d+)?\s*(mg|g|ml|tablets?|capsules?|drops?|units?)$'
    
    if not re.match(pattern, dosage.lower()):
        raise ValidationError(
            "Dosage must include amount and unit (e.g., '500mg', '2 tablets')."
        )


def validate_blood_type(blood_type):
    """
    Validates blood type
    """
    valid_types = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
    
    if blood_type not in valid_types:
        raise ValidationError(
            f"Invalid blood type. Must be one of: {', '.join(valid_types)}"
        )


def validate_email_domain(email):
    """
    Validates email domain (optional: restrict to specific domains)
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(pattern, email):
        raise ValidationError("Invalid email format.")


def validate_arabic_text(text):
    """
    Validates that text contains Arabic characters
    """
    pattern = r'[\u0600-\u06FF]'
    
    if not re.search(pattern, text):
        raise ValidationError("Text must contain Arabic characters.")


def validate_appointment_duration(duration_minutes):
    """
    Validates appointment duration
    """
    valid_durations = [15, 30, 45, 60, 90, 120]
    
    if duration_minutes not in valid_durations:
        raise ValidationError(
            f"Duration must be one of: {', '.join(map(str, valid_durations))} minutes."
        )


def validate_room_number(room_number):
    """
    Validates room number format (e.g., "101", "A-205")
    """
    pattern = r'^[A-Z]?-?\d{1,4}$'
    
    if not re.match(pattern, room_number.upper()):
        raise ValidationError(
            "Room number must be in format: 101 or A-205"
        )


def validate_emergency_contact(phone):
    """
    Same as phone validation but specifically for emergency contacts
    """
    validate_egyptian_phone(phone)