from django import forms
from django.contrib.auth.models import User
from .models import *

class EnrollSubjectForm(forms.Form):
    term = forms.ModelChoiceField(queryset=Term.objects.all(), label="Select Term")
    subjects = forms.ModelMultipleChoiceField(
        queryset=Subject.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label="Select Subjects"
    )


class StudentRegistrationForm(forms.ModelForm):
    admission_number = forms.CharField(max_length=20, help_text="Enter your admission number")
    name = forms.CharField(max_length=100, help_text="Enter your full name")
    email = forms.EmailField(help_text="Enter your email address")
    password = forms.CharField(widget=forms.PasswordInput, help_text="Enter a strong password")
    password2 = forms.CharField(widget=forms.PasswordInput, help_text="Confirm password")  # Added confirm password

    class Meta:
        model = User
        fields = ['email', 'password']  # Only fields available in User

    def clean(self):
        cleaned_data = super().clean()
        admission_number = cleaned_data.get("admission_number")
        name = cleaned_data.get("name")

        # Check admission number exists
        try:
            student = Student.objects.get(admission_number=admission_number)
        except Student.DoesNotExist:
            raise forms.ValidationError("Admission number does not exist.")

        # Name match
        if student.name.strip().lower() != name.strip().lower():
            raise forms.ValidationError("Name does not match our records.")

        # Password match
        password = cleaned_data.get("password")
        password2 = cleaned_data.get("password2")
        if password and password2 and password != password2:
            raise forms.ValidationError("Passwords do not match.")

        return cleaned_data






class StudentProfileEditForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            'profile_image',
            'address',
            'emergency_contact_name',
            'emergency_contact_phone',
            'emergency_contact_relationship',
            'medical_conditions',
            'blood_group'
        ]
        widgets = {
            'profile_image': forms.FileInput(attrs={'class': 'form-control', 'id': 'profileImageInput', 'accept': 'image/*'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Address'}),
            'emergency_contact_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Emergency Contact Name'}),
            'emergency_contact_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Emergency Contact Phone'}),
            'emergency_contact_relationship': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Relationship to Student'}),
            'medical_conditions': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Medical Conditions', 'rows': 3}),
            'blood_group': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Blood Group'}),
        }


class ClassForm(forms.ModelForm):
    class Meta:
        model = Class_of_study
        fields = ['name', 'stream']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Class Name'}),
            'stream': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Stream'}),
        }



class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name', 'code']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Subject Name'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Subject Code'}),
        }





class StudentForm(forms.ModelForm):
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="Date of Birth"
    )
    admission_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        required=False,
        label="Admission Date"
    )

    class Meta:
        model = Student
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'}),
            'admission_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Admission Number'}),
            'current_class': forms.Select(attrs={'class': 'form-select'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Address','rows': '1',}),
            'father_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Father Name'}),
            'father_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Father Phone'}),
            'father_occupation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Father Occupation'}),
            'mother_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Mother Name'}),
            'mother_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Mother Phone'}),
            'mother_occupation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Mother Occupation'}),
            'guardian_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Guardian Name'}),
            'guardian_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Guardian Phone'}),
            'guardian_relationship': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Guardian Relationship'}),
            'guardian_address': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Guardian Address','rows': '1'}),
            'emergency_contact_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Emergency Contact Name'}),
            'emergency_contact_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Emergency Contact Phone'}),
            'emergency_contact_relationship': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Emergency Contact Relationship'}),
            'blood_group': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Blood Group'}),
            'medical_conditions': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Medical Conditions','rows': '1'}),
            'previous_school': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Previous School'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Remarks','rows': '1'}),
        }






class TermForm(forms.ModelForm):
    class Meta:
        model = Term
        fields = ['name', 'year']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Term Name'}),
            'year': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Year'}),
        }




class CATForm(forms.ModelForm):
    class_of_study = forms.ModelChoiceField(
        queryset=Student.objects.first().current_class.__class__.objects.all() if Student.objects.exists() else None,
        label='Class of Study',
        required=False,
        widget=forms.Select(attrs={'class': 'form-select', 'readonly': 'readonly'})
    )

    class Meta:
        model = CAT
        fields = ['student', 'subject', 'term', 'class_of_study', 'cat1', 'cat2', 'cat3']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-select'}),
            'subject': forms.Select(attrs={'class': 'form-select'}),
            'term': forms.Select(attrs={'class': 'form-select'}),
            'cat1': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'CAT 1 Score'}),
            'cat2': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'CAT 2 Score'}),
            'cat3': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'CAT 3 Score'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # If a student is selected, pre-populate the class_of_study
        if 'student' in self.data:
            student_id = self.data.get('student')
            if student_id:
                try:
                    student = Student.objects.get(id=student_id)
                    if student.current_class:
                        self.fields['class_of_study'].initial = student.current_class
                        self.fields['class_of_study'].widget.attrs['disabled'] = 'disabled'
                except Student.DoesNotExist:
                    pass


class StudentSearchForm(forms.Form):
    query = forms.CharField(
        label="Search Student",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter student name, admission number, or class...'
        })
    )






class TeacherForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = [
            'id_number', 'first_name', 'last_name', 'email', 'phone', 'address', 'assigned_class', 
            'profile_image', 'date_of_birth', 'gender', 'nationality', 'employment_date', 'department', 
            'position', 'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship'
        ]
        widgets = {
            'id_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ID Number'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Address'}),
            'assigned_class': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Assigned Class'}),
            'profile_image': forms.FileInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'nationality': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nationality'}),
            'employment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'position': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Position'}),
            'emergency_contact_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Emergency Contact Name'}),
            'emergency_contact_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Emergency Contact Phone'}),
            'emergency_contact_relationship': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Relationship'}),
        }

    
class TeacherEditForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = ['id_number', 'first_name', 'last_name', 'email', 'phone', 'address', 'assigned_class', 
                  'profile_image', 'date_of_birth', 'gender', 'nationality', 'employment_date', 'department', 
                  'position', 'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship']
        
        widgets = {
            'id_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ID Number'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Address'}),
            'assigned_class': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Assigned Class'}),
            'profile_image': forms.FileInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'nationality': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nationality'}),
            'employment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'position': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Position'}),
            'emergency_contact_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Emergency Contact Name'}),
            'emergency_contact_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Emergency Contact Phone'}),
            'emergency_contact_relationship': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Relationship'}),
        }




class StaffForm(forms.ModelForm):
    class Meta:
        model = Staff
        fields = [
            'id_number', 'first_name', 'last_name', 'email', 'phone', 'address',
            'date_of_birth', 'gender', 'nationality', 'department', 'position',
            'employment_date', 'salary', 'status', 'profile_image', 
            'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship'
        ]
        widgets = {
            'id_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ID Number'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Address'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'nationality': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nationality'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'position': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Position'}),
            'employment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'salary': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Salary'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'profile_image': forms.FileInput(attrs={'class': 'form-control'}),
            'emergency_contact_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Emergency Contact Name'}),
            'emergency_contact_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Emergency Contact Phone'}),
            'emergency_contact_relationship': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Relationship'}),
        }


class NonStaffForm(forms.ModelForm):
    class Meta:
        model = NonStaff
        fields = [
            'id_number', 'first_name', 'last_name', 'email', 'phone', 'address',
            'date_of_birth', 'gender', 'nationality', 'role', 'hire_date', 
            'salary', 'profile_image', 
            'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship'
        ]
        widgets = {
            'id_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ID Number'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Address'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'nationality': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nationality'}),
            'role': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Role'}),
            'hire_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'salary': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Salary'}),
            'profile_image': forms.FileInput(attrs={'class': 'form-control'}),
            'emergency_contact_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Emergency Contact Name'}),
            'emergency_contact_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Emergency Contact Phone'}),
            'emergency_contact_relationship': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Relationship'}),
        }



class InternForm(forms.ModelForm):
    class Meta:
        model = Intern
        fields = [
            'id_number', 'first_name', 'last_name', 'email', 'phone', 'address',
            'date_of_birth', 'gender', 'nationality', 'department', 'position',
            'start_date', 'end_date', 'stipend', 'profile_image',
            'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship'
        ]
        widgets = {
            'id_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ID Number'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Address'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'nationality': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nationality'}),
            'department': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Department'}),
            'position': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Position'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'stipend': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Stipend'}),
            'profile_image': forms.FileInput(attrs={'class': 'form-control'}),
            'emergency_contact_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Emergency Contact Name'}),
            'emergency_contact_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Emergency Contact Phone'}),
            'emergency_contact_relationship': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Relationship'}),
        }


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = [
            'profile_image', 'full_names', 'about', 'role', 'Region', 
            'county', 'address', 'phone', 'email'
        ]
        widgets = {
            'profile_image': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
            'full_names': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter full names'}),
            'about': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Write about yourself'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'Region': forms.Select(attrs={'class': 'form-control'}),
            'county': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter county'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter address'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter phone number'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email address'})
        }
        labels = {
            'profile_image': 'Profile Image',
            'full_names': 'Full Names',
            'about': 'About Me',
            'role': 'Role',
            'Region': 'Region',
            'county': 'County',
            'address': 'Address',
            'phone': 'Phone Number',
            'email': 'Email Address'
        }
        help_texts = {
            'email': 'Please enter a valid email address.'
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if len(phone) != 10:
            raise forms.ValidationError("Phone number must be 10 digits.")
        return phone

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Profile.objects.filter(email=email).exists():
            raise forms.ValidationError("This email address is already in use.")
        return email




class NewsUpdateForm(forms.ModelForm):
    class Meta:
        model = NewsUpdate
        fields = ['title', 'description', 'category', 'image']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'News Title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Write a brief description...', 'rows': 4}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content', 'photo', 'pdf']  # Include only content, photo, and pdf
        widgets = {
            'content': forms.Textarea(attrs={'placeholder': 'Type your message'}),
        }


class ResourceForm(forms.ModelForm):
    class Meta:
        model = Resource
        fields = ['title', 'description', 'category', 'file', 'is_active']
    
    # Optional: Customize form validation or widgets here if needed
    # Example: Add a widget for the description to use a textarea
    description = forms.CharField(widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Enter a brief description of the resource'}))

class ExamTimeTableForm(forms.ModelForm):
    class Meta:
        model = ExamTimeTable
        fields = '__all__'
               