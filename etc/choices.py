# User Types
USER_TYPE_CHOICES = [
    ('admin', 'مدير النظام'),
    ('patient', 'مريض'),
    ('doctor', 'طبيب'),
    ('receptionist', 'موظف استقبال'),
    ('medical_rep', 'مندوب طبي'),
]

# Gender
GENDER_CHOICES = [
    ('male', 'ذكر'),
    ('female', 'أنثى'),
]

# Media Types
MEDIA_TYPE_CHOICES = [
    ('image', 'صورة'),
    ('video', 'فيديو'),
    ('audio', 'صوت'),
    ('document', 'مستند'),
    ('xray', 'أشعة'),
    ('other', 'أخرى'),
]

# Disease Categories
CATEGORY_CHOICES = [
    ('chronic', 'مزمن'),
    ('infectious', 'معدي'),
    ('genetic', 'وراثي'),
    ('other', 'أخرى'),
]

# Booking Status
BOOKING_STATUS_CHOICES = [
    ('pending', 'قيد الانتظار'),
    ('confirmed', 'مؤكد'),
    ('completed', 'مكتمل'),
    ('cancelled', 'ملغي'),
]

# Operation Status
OPERATION_STATUS_CHOICES = [
    ('scheduled', 'مجدول'),
    ('in_progress', 'جاري التنفيذ'),
    ('completed', 'مكتمل'),
    ('cancelled', 'ملغي'),
]

# Medicine Forms
FORM_CHOICES = [
    ('tablet', 'قرص'),
    ('capsule', 'كبسولة'),
    ('syrup', 'شراب'),
    ('injection', 'حقن'),
    ('cream', 'كريم'),
]

# Payment Status
PAYMENT_STATUS_CHOICES = [
    ('unpaid', 'غير مدفوع'),
    ('partial', 'مدفوع جزئياً'),
    ('paid', 'مدفوع بالكامل'),
]

# Payment Methods
PAYMENT_METHOD_CHOICES = [
    ('cash', 'نقدي'),
    ('card', 'بطاقة ائتمان'),
    ('vodafone_cash', 'فودافون كاش'),
    ('instapay', 'إنستا باي'),
    ('transfer', 'تحويل بنكي'),
]

# Salary Status
SALARY_STATUS_CHOICES = [
    ('pending', 'قيد الانتظار'),
    ('partial', 'جزئي'),
    ('paid', 'مدفوع'),
]

# Advance Status
ADVANCE_STATUS_CHOICES = [
    ('pending', 'قيد الانتظار'),
    ('approved', 'موافق عليه'),
    ('rejected', 'مرفوض'),
    ('paid', 'مدفوع'),
]