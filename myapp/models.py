from django.contrib.auth.models import User
from django.db import models
from django.utils.timezone import now
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
import random
import string
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver

class Department(models.Model):
    head_of_department = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return self.name


class Class_of_study(models.Model):
    name = models.CharField(max_length=50)  # Form 1, Form 2, etc.
    stream = models.CharField(max_length=50)  # Stream A, B, C, etc.

    def __str__(self):
        return f"{self.name} - {self.stream}"

class Subject(models.Model):
    name = models.CharField(max_length=100, unique=True)  # Math, English, etc.
    code = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return self.name

class Student(models.Model):
    name = models.CharField(max_length=100)
    admission_number = models.CharField(max_length=20, unique=True)
    date_of_birth = models.DateField()
    current_class = models.ForeignKey(Class_of_study, on_delete=models.SET_NULL, null=True, related_name='students')
    
    # Personal Information
    gender = models.CharField(max_length=10, choices=[('M', 'Male'), ('F', 'Female')], null=True, blank=True)
    admission_date = models.DateField(null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    profile_image = models.ImageField(upload_to="students_profiles/", default="profile.png" ,  null=True, blank=True)
    
    # Parent/Guardian Information
    father_name = models.CharField(max_length=100, null=True, blank=True)
    father_phone = models.CharField(max_length=15, null=True, blank=True)
    father_occupation = models.CharField(max_length=100, null=True, blank=True)
    
    mother_name = models.CharField(max_length=100, null=True, blank=True)
    mother_phone = models.CharField(max_length=15, null=True, blank=True)
    mother_occupation = models.CharField(max_length=100, null=True, blank=True)
    
    # Guardian Information (if different from parents)
    guardian_name = models.CharField(max_length=100, null=True, blank=True)
    guardian_phone = models.CharField(max_length=15, null=True, blank=True)
    guardian_relationship = models.CharField(max_length=50, null=True, blank=True)
    guardian_address = models.TextField(null=True, blank=True)
    
    # Emergency Contact
    emergency_contact_name = models.CharField(max_length=100, null=True, blank=True)
    emergency_contact_phone = models.CharField(max_length=15, null=True, blank=True)
    emergency_contact_relationship = models.CharField(max_length=50, null=True, blank=True)
    
    # Additional Information
    blood_group = models.CharField(max_length=5, null=True, blank=True)
    medical_conditions = models.TextField(null=True, blank=True)
    previous_school = models.CharField(max_length=200, null=True, blank=True)

    # Active/Inactive Status Field
    is_active = models.BooleanField(default=True)
    remarks = models.TextField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        ordering = ['admission_number']

    def __str__(self):
        return f"{self.name} ({self.admission_number})"
    
    def get_age(self):
        from datetime import date
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
    
    def years_in_school(self):
        """Calculate how many years the student has been admitted."""
        if self.admission_date:
            today = timezone.now().date()
            return today.year - self.admission_date.year - (
                (today.month, today.day) < (self.admission_date.month, self.admission_date.day)
            )
        return 0
    
    def update_active_status(self):
        """Update the is_active field based on admission date."""
        if self.years_in_school() >= 4:
            self.is_active = False
            self.save()

class Term(models.Model):
    name = models.CharField(max_length=50)  # Term 1, Term 2, Term 3
    year = models.IntegerField()  # e.g., 2023
    is_current = models.BooleanField(default=False)  # Indicates if this is the current active term

    def __str__(self):
        return f"{self.name} {self.year}"
    
    def save(self, *args, **kwargs):
        # If this term is being set as current, make sure no other term is current
        if self.is_current:
            Term.objects.filter(is_current=True).update(is_current=False)
        super().save(*args, **kwargs)

class CAT(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='cats')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    term = models.ForeignKey(Term, on_delete=models.CASCADE)

    class_of_study = models.ForeignKey(Class_of_study, on_delete=models.SET_NULL, null=True, blank=True)

    cat1 = models.FloatField(default=0)
    cat2 = models.FloatField(default=0)
    cat3 = models.FloatField(default=0)
    end_term = models.FloatField(default=0)  # Will store the average of CATs
    grade_points = models.FloatField(default=0.0)  # Store the numerical grade points
    letter_grade = models.CharField(max_length=2, default='F')  # Store the letter grade
    position = models.CharField(max_length=20, default='Fail')  # Store the class position

    def calculate_end_term(self):
        # Calculate average of CATs instead of sum
        total_cats = 3
        self.end_term = round((self.cat1 + self.cat2 + self.cat3) / total_cats, 2)
        return self.end_term

    def calculate_average(self):
        # Now just return end_term since it's already the average
        return self.end_term

    def assign_grade_points(self):
        average = self.calculate_average()
        
        if average >= 80:
            return 4.0, 'A'
        elif average >= 75:
            return 3.7, 'A-'
        elif average >= 70:
            return 3.3, 'B+'
        elif average >= 65:
            return 3.0, 'B'
        elif average >= 60:
            return 2.7, 'B-'
        elif average >= 55:
            return 2.3, 'C+'
        elif average >= 50:
            return 2.0, 'C'
        elif average >= 45:
            return 1.7, 'C-'
        elif average >= 40:
            return 1.3, 'D+'
        elif average >= 35:
            return 1.0, 'D'
        else:
            return 0.0, 'F'

    def determine_position(self):
        average = self.calculate_average()
        
        if average >= 70:
            return "First Class"
        elif average >= 60:
            return "Second Class Upper"
        elif average >= 50:
            return "Second Class Lower"
        elif average >= 40:
            return "Pass"
        else:
            return "Fail"

    def save(self, *args, **kwargs):
        # Set class_of_study if not set yet
        if not self.class_of_study:
            self.class_of_study = self.student.current_class
        self.end_term = self.calculate_end_term()
        self.grade_points, self.letter_grade = self.assign_grade_points()
        self.position = self.determine_position()
        super().save(*args, **kwargs)

    def get_full_grade_info(self):
        return {
            'end_term': self.end_term,
            'grade_points': self.grade_points,
            'letter_grade': self.letter_grade,
            'position': self.position
        }

    def __str__(self):
        return f"{self.student.name} - {self.subject.name} - {self.term.name}"
    


class Teacher(models.Model):
    id_number = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, unique=True)
    address = models.TextField(null=True, blank=True)
    username = models.CharField(max_length=150, blank=True, null=True)  # New field added
    
    # Assigned Class
    assigned_class = models.ForeignKey(Class_of_study, on_delete=models.SET_NULL, null=True, blank=True, related_name="teachers")
    
    # Profile Picture
    profile_image = models.ImageField(upload_to="teachers_profiles/", default="teachers_profiles/profile.png",  null=True, blank=True)

    # Unique 6-character Teacher Code
    teacher_code = models.CharField(max_length=6, unique=True, blank=True)
    
    # Additional Information
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[('M', 'Male'), ('F', 'Female')], null=True, blank=True)
    nationality = models.CharField(max_length=50, null=True, blank=True)
    
    # Employment Details
    employment_date = models.DateField(null=True, blank=True)
    #department = models.ForeignKey( Department, on_delete=models.SET_NULL , null=True, blank=True)
    department = models.CharField(max_length=100, null=True, blank=True)
    position = models.CharField(max_length=100, null=True, blank=True)  # e.g., Senior Teacher, HOD

    # Emergency Contact
    emergency_contact_name = models.CharField(max_length=100, null=True, blank=True)
    emergency_contact_phone = models.CharField(max_length=15, null=True, blank=True)
    emergency_contact_relationship = models.CharField(max_length=50, null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['first_name', 'last_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.teacher_code})"

# Signal to generate a unique 6-character Teacher Code
def generate_teacher_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

@receiver(pre_save, sender=Teacher)
def generate_unique_teacher_code(sender, instance, **kwargs):
    if not instance.teacher_code:
        unique_code = generate_teacher_code()
        while Teacher.objects.filter(teacher_code=unique_code).exists():
            unique_code = generate_teacher_code()
        instance.teacher_code = unique_code




class Staff(models.Model):
    # Basic Information
    id_number = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, unique=True)
    address = models.TextField(null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[('M', 'Male'), ('F', 'Female')], null=True, blank=True)
    nationality = models.CharField(max_length=50, null=True, blank=True)
    
    # Employment Details
    department = models.CharField(max_length=100, null=True, blank=True)
    position = models.CharField(max_length=100, null=True, blank=True)  # e.g., Admin, Teacher, Security, etc.
    employment_date = models.DateField(null=True, blank=True)
    salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=[('Active', 'Active'), ('Inactive', 'Inactive')], default='Active')

    # Profile Picture
    profile_image = models.ImageField(upload_to="staff_profiles/", default="profile.png", null=True, blank=True)
    
    # Emergency Contact
    emergency_contact_name = models.CharField(max_length=100, null=True, blank=True)
    emergency_contact_phone = models.CharField(max_length=15, null=True, blank=True)
    emergency_contact_relationship = models.CharField(max_length=50, null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['first_name', 'last_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.position})"



class NonStaff(models.Model):
    # Basic Information
    id_number = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, unique=True)
    address = models.TextField(null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[('M', 'Male'), ('F', 'Female')], null=True, blank=True)
    nationality = models.CharField(max_length=50, null=True, blank=True)
    
    # Non-Staff Role (e.g., Cleaner, Security, etc.)
    role = models.CharField(max_length=100, null=True, blank=True)
    hire_date = models.DateField(null=True, blank=True)
    salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Profile Picture
    profile_image = models.ImageField(upload_to="nonstaff_profiles/", default="profile.png", null=True, blank=True)

    # Emergency Contact
    emergency_contact_name = models.CharField(max_length=100, null=True, blank=True)
    emergency_contact_phone = models.CharField(max_length=15, null=True, blank=True)
    emergency_contact_relationship = models.CharField(max_length=50, null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['first_name', 'last_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.role})"


class Intern(models.Model):
    # Basic Information
    id_number = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, unique=True)
    address = models.TextField(null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[('M', 'Male'), ('F', 'Female')], null=True, blank=True)
    nationality = models.CharField(max_length=50, null=True, blank=True)

    # Internship Details
    department = models.CharField(max_length=100, null=True, blank=True)
    position = models.CharField(max_length=100, null=True, blank=True)  # e.g., IT Intern, Admin Intern
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    stipend = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Profile Picture
    profile_image = models.ImageField(upload_to="intern_profiles/", default="intern_profiles/profile.png", null=True, blank=True)

    
    # Emergency Contact
    emergency_contact_name = models.CharField(max_length=100, null=True, blank=True)
    emergency_contact_phone = models.CharField(max_length=15, null=True, blank=True)
    emergency_contact_relationship = models.CharField(max_length=50, null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['first_name', 'last_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.position})"


#profile model 
class Profile(models.Model):
    ROLE_CHOICES = (
        ('Admin', 'Admin'),
        ('Staff', 'staff'),
        
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    username = models.CharField(max_length=150, blank=True, null=True)
    about = models.TextField(blank=True, null=True)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='Staff')
    full_names = models.CharField(max_length=200)
    Region = models.CharField(max_length=200, blank=True, null=True)
    county = models.CharField(max_length=100, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    profile_image = models.ImageField(upload_to='profile_images/', default='profile_images/profile.png')
    website = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.full_names    


class Activity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)  # User performing the action
    action = models.CharField(max_length=255)  # The action performed
    timestamp = models.DateTimeField(default=now)  # Time of the activity
    ip_address = models.GenericIPAddressField(null=True, blank=True)  # Optional: Track user's IP address

    def __str__(self):
        return f"{self.user} - {self.action} at {self.timestamp}"
    


class NewsUpdate(models.Model):
    CATEGORY_CHOICES = [
        ('Education', 'Education'),  # Add Education category
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    image = models.ImageField(upload_to='news_updates/', blank=True, null=True)
    published_date = models.DateTimeField(default=now)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE,  blank=True, null=True)  # Link to User

    def __str__(self):
        return self.title
    

class Message(models.Model):
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name='received_messages', on_delete=models.CASCADE)
    content = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    # Fields for media uploads
    photo = models.ImageField(upload_to='photos/', blank=True, null=True)
    pdf = models.FileField(upload_to='pdfs/', blank=True, null=True)

    def __str__(self):
           return f'{self.sender.username} → {self.receiver.username}'

    


#fee 
class FeeStructure(models.Model):
    term = models.OneToOneField(Term, on_delete=models.CASCADE, related_name='fee_structure')
    amount_required = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Fee for {self.term}: {self.amount_required}"

class FeePayment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='fee_payments')
    term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name='fee_payments')
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField(auto_now_add=True)
    receipt_number = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return f"{self.student.name} - {self.term} - Paid: {self.amount_paid}"

    @property
    def balance(self):
        # Total paid by student in the term
        total_paid = FeePayment.objects.filter(student=self.student, term=self.term).aggregate(total=models.Sum('amount_paid'))['total'] or 0
        
        # Required fee for the term
        try:
            required_fee = self.term.fee_structure.amount_required
        except FeeStructure.DoesNotExist:
            required_fee = 0  # If no fee structure is set

        return required_fee - total_paid


class EnrolledSubject(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='enrolled_subjects')
    term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name='enrolled_subjects')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='enrolled_students')

    date_enrolled = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'term', 'subject')  # Prevent duplicates

    def __str__(self):
        return f"{self.student.name} enrolled in {self.subject.name} - {self.term.name} {self.term.year}"


class ResourceCategory(models.Model):
    """Category of resources, e.g., KCSE, KCPE, etc."""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Resource(models.Model):
    """A model to store revision materials like KCSE revision papers."""
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    category = models.ForeignKey(ResourceCategory, related_name="resources", on_delete=models.SET_NULL, null=True, blank=True)
    file = models.FileField(upload_to='resources/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    views = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def get_absolute_url(self):
        return reverse('resource_detail', args=[str(self.id)])

    def __str__(self):
        return self.title

    def increment_views(self):
        """Increment the view count when the resource is accessed."""
        self.views += 1
        self.save()

    def get_file_url(self):
        """Returns the URL of the uploaded resource file."""
        if self.file:
            return self.file.url
        return None


class ExaminationSession(models.Model):
    """Represents a specific KCSE Examination Session"""
    year = models.IntegerField()
    start_date = models.DateField()
    end_date = models.DateField()
    
    def __str__(self):
        return f"KCSE {self.year}"
    

class ExamTimeTable(models.Model):
    name = models.CharField(max_length= 50 , blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    session = models.ForeignKey(ExaminationSession, on_delete=models.CASCADE, related_name='timetables')
    time_table_pdf = models.FileField(upload_to='time_tables/', blank=True, null=True)

    def __str__(self):
        return f"Timetable for {self.session.year} "  
    



class TermReporting(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='term_reports')
    term = models.ForeignKey(Term, on_delete=models.CASCADE)
    reporting_date = models.DateField()
    
    # Simple reporting status
    STATUS_CHOICES = [
        ('REPORTED', 'Reported'),
        ('ABSENT', 'Absent'),
        ('LATE', 'Late Reporting'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='REPORTED')
    
    # Optional notes field
    notes = models.TextField(null=True, blank=True)
    
    class Meta:
        unique_together = ['student', 'term']
        ordering = ['-term__year', 'term__name', 'reporting_date']
    
    def __str__(self):
        return f"{self.student.name} - {self.term} ({self.get_status_display()})"
    


class Event(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    date = models.DateField()
    term = models.ForeignKey('Term', on_delete=models.CASCADE)  # Assuming event is linked to term

    def __str__(self):
        return self.title
