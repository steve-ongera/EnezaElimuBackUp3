from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives, send_mail
from django.core.cache import cache
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.html import strip_tags
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.views import View
from django.conf import settings
from django.db.models import Avg, Sum, Max, Count, F, Q, Prefetch
from django.db.models.functions import Coalesce, ExtractYear
from django.db.models import functions
from django.db.models import Case, When
from django.db import models
from datetime import date, timedelta, datetime
from collections import defaultdict
import json

from .models import *
from .forms import *

from django.contrib.auth import get_user_model
Account = get_user_model()

from django.contrib.auth.decorators import login_required, user_passes_test

# Check if user is staff
def is_staff_user(user):
    return user.is_staff


def register(request):
    if request.method == "POST":
        form = StudentRegistrationForm(request.POST)
        password2 = request.POST.get('password2')  # Confirm password from HTML

        if form.is_valid():
            admission_number = form.cleaned_data['admission_number']
            name = form.cleaned_data['name']
            password = form.cleaned_data['password']

            # 1. Check if User already exists
            if User.objects.filter(username=admission_number).exists():
                form.add_error('admission_number', 'User with this admission number already exists.')
                return render(request, 'auth/register.html', {'form': form})

            # 2. Check password confirmation
            if password != password2:
                form.add_error('password', 'Passwords do not match.')
                return render(request, 'auth/register.html', {'form': form})

            # 3. Get the student instance
            try:
                student = Student.objects.get(admission_number=admission_number)
            except Student.DoesNotExist:
                form.add_error('admission_number', 'Admission number not found.')
                return render(request, 'auth/register.html', {'form': form})

            # 4. Create user
            try:
                user = User.objects.create_user(
                    username=admission_number,
                    password=password,
                    email=form.cleaned_data['email'],
                    first_name=student.name.split()[0],  # First name
                    last_name=" ".join(student.name.split()[1:]),  # Rest of the name
                )
                # 5. Log in
                login(request, user)
                messages.success(request, f'Registration successful! Welcome {user.first_name}.')
                return redirect('student_dashboard')
            except Exception as e:
                form.add_error(None, 'An unexpected error occurred during registration.')
                return render(request, 'auth/register.html', {'form': form})

    else:
        form = StudentRegistrationForm()

    return render(request, 'auth/register.html', {'form': form})


def custom_login(request):
    if request.method == "POST":
        admission_number = request.POST.get('admission_number', '').strip()
        password = request.POST.get('password', '').strip()
        
        # Input validation
        if not admission_number or not password:
            messages.error(request, "Both admission number and password are required.")
            return render(request, 'auth/login.html', {'admission_number': admission_number})
        
        user = authenticate(request, username=admission_number, password=password)

        if user is not None:
            if user.is_active:
                login(request, user)
                next_url = request.POST.get('next') or request.GET.get('next')
                
                # Success message with username
                messages.success(
                    request, 
                    f"Welcome back, {user.get_full_name() or user.username}! You've logged in successfully."
                )
                
                # Secure next URL validation
                from urllib.parse import urlparse
                if next_url:
                    netloc = urlparse(next_url).netloc
                    if netloc and netloc != request.get_host():
                        next_url = None
                
                # Redirect logic
                if user.is_staff:
                    return redirect(next_url or 'admin_dashboard')
                return redirect(next_url or 'student_dashboard')
            else:
                messages.error(request, "This account is inactive.")
        else:
            messages.error(request, "Invalid admission number or password.")
        
        # Return with preserved form input on error
        return render(request, 'auth/login.html', {
            'admission_number': admission_number,
            'next': request.POST.get('next', '')
        })

    # GET request - show login form
    return render(request, 'auth/login.html', {
        'next': request.GET.get('next', '')
    })



def custom_logout(request):
    logout(request)
    messages.error(request, "Logged out successfully!")
    return redirect('login')

# View to display the help and support page
@login_required
def help_and_support(request):
    return render(request, 'help/help_and_support.html')


# View to display the system settings page
@login_required
def system_settings(request):
    return render(request, 'help/system_settings.html')


#forgot password view 
def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        if Account.objects.filter(email=email).exists():
            user = Account.objects.get(email=email)

            # Generate reset password token and send email
            current_site = get_current_site(request)
            mail_subject = 'Reset Your Password'
            context = {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
                'protocol': 'https' if request.is_secure() else 'http'
            }
            
            # Render both HTML and plain text versions of the email
            html_message = render_to_string('auth/reset_password_email.html', context)
            plain_message = strip_tags(html_message)
            
            to_email = email
            
            # Use EmailMultiAlternatives for sending both HTML and plain text
            email = EmailMultiAlternatives(
                mail_subject,
                plain_message,
                'noreply@yourdomain.com',
                [to_email]
            )
            email.attach_alternative(html_message, "text/html")
            email.send()

            messages.success(request, 'Password reset email has been sent to your email address.')
            return redirect('login')
        else:
            messages.error(request, 'Account does not exist!')
            return redirect('forgot_password')
    return render(request, 'auth/forgot_password.html')



def reset_password(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))  # Replace force_text with force_str
        user = Account.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            password = request.POST.get('password')
            confirm_password = request.POST.get('confirm_password')

            if password == confirm_password:
                user.set_password(password)
                user.save()
                messages.success(request, 'Password reset successful. You can now login with your new password.')
                return redirect('login')
            else:
                messages.error(request, 'Passwords do not match.')
                return redirect('reset_password', uidb64=uidb64, token=token)
        return render(request, 'auth/reset_password.html')
    else:
        messages.error(request, 'Invalid reset link. Please try again.')
        return redirect('login')
    





@login_required
def student_dashboard(request):
    # Get the logged-in student's details
    try:
        student = Student.objects.get(admission_number=request.user.username)
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found. Please contact administration.")
        return redirect('login')  # or wherever you'd like to redirect

    

    recent_activities = Activity.objects.order_by('-timestamp')[:6]
    news_updates = NewsUpdate.objects.all().order_by('-published_date')[:5]

    terms = Term.objects.all().order_by('-year', 'name')

    # Get selected term from GET or default to the latest term where student enrolled
    selected_term_id = request.GET.get('term')

    if selected_term_id:
        selected_term = Term.objects.get(id=selected_term_id)
    else:
        # Check latest term where the student enrolled
        latest_enrollment = EnrolledSubject.objects.filter(student=student).order_by('-term__year', '-term__name').first()
        selected_term = latest_enrollment.term if latest_enrollment else Term.objects.order_by('-year', '-name').first()
     
     # Get fee balance for selected term
    try:
        required_fee = selected_term.fee_structure.amount_required
    except:
        required_fee = 0

    total_paid = FeePayment.objects.filter(student=student, term=selected_term).aggregate(total=Sum('amount_paid'))['total'] or 0
    fee_balance = required_fee - total_paid

    subjects_count = EnrolledSubject.objects.filter(student=student, term=selected_term).count()

    # Get the latest term (highest year, latest term)
    latest_term = Term.objects.order_by('-year', '-name').first()

    # Fetch recent CAT results for this student and term
    recent_results = CAT.objects.filter(student=student, term=latest_term)


    # Calculate latest term average
    latest_term_average = 0
    latest_term_grade = "N/A"
    latest_term_grade_point = 0.0
    latest_term_position = "N/A"
    
    if recent_results.exists():
        # Get the average of all end_term scores for latest term
        avg_result = recent_results.aggregate(avg_score=Avg('end_term'))
        latest_term_average = round(avg_result['avg_score'], 2) if avg_result['avg_score'] else 0
        
        # Determine grade information based on the latest term average
        dummy_cat = CAT(end_term=latest_term_average)
        latest_term_grade_point, latest_term_grade = dummy_cat.assign_grade_points()
        latest_term_position = dummy_cat.determine_position()

    # Fee balance data (from previous discussion)
    current_year = date.today().year
    admission_year = student.admission_date.year  # Extract year

    # Get terms from admission year up to current year
    terms = Term.objects.filter(year__gte=admission_year, year__lte=current_year).order_by('year', 'name')

    fee_data = []

    for term in terms:
        # Get required fee
        try:
            required_fee = term.fee_structure.amount_required
        except AttributeError:
            required_fee = 0

        # Get amount paid
        total_paid = FeePayment.objects.filter(student=student, term=term).aggregate(total=Sum('amount_paid'))['total'] or 0

        # Calculate balance
        balance = required_fee - total_paid

        fee_data.append({
            'term': term,
            'required_fee': required_fee,
            'total_paid': total_paid,
            'balance': balance,
        })

     # Get enrolled subjects for selected term
    enrolled_subjects = EnrolledSubject.objects.filter(student=student, term=selected_term)


    # NEW CODE: Create data for subject performance donut chart
    # Get recent performance data for the student in the latest term
    recent_cats = CAT.objects.filter(student=student, term=latest_term)
    
    # Create data for subject performance distribution
    subject_performance = []
    
    # Get all subjects with their scores
    for cat in recent_cats:
        subject_performance.append({
            'value': cat.end_term,  # Use the average score
            'name': cat.subject.name  # Use the subject name
        })
    
    # Sort by score (optional - can comment out if not needed)
    subject_performance.sort(key=lambda x: x['value'], reverse=True)
    
    # Convert to JSON for template
    performance_data_json = json.dumps(subject_performance)


    context = {
        'student': student,
        'fee_data': fee_data,
        'recent_results': recent_results,
        'latest_term': latest_term,
        'recent_activities':recent_activities,
        'news_updates': news_updates,
        'terms': terms,
        'selected_term': selected_term,
        'enrolled_subjects': enrolled_subjects,
        'fee_balance': fee_balance,
        'subjects_count': subjects_count,
        'performance_data_json': performance_data_json,  # Added performance data

        'latest_term_average': latest_term_average,  # Latest term average
        'latest_term_grade': latest_term_grade,      # Latest term grade
        'latest_term_grade_point': latest_term_grade_point,
        'latest_term_position': latest_term_position,
    }

    
    
    return render(request, 'dashboard/student_dashboard.html', context)


@login_required
@user_passes_test(is_staff_user)
def general_student_list(request):
    students = Student.objects.all()
    return render(request, 'students/student_list.html', {'students': students})

@login_required
def student_marks(request, student_id, term_id):
    student = get_object_or_404(Student, id=student_id)
    term = get_object_or_404(Term, id=term_id)
    cats = CAT.objects.filter(student=student, term=term)

    context = {
        'student': student,
        'term': term,
        'cats': cats,
    }
    return render(request, 'marks/student_marks.html', context)

@login_required
def student_progress(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    
    # Get all years from terms
    # Get years from the student's admission year onwards
    admission_year = student.admission_date.year
    years = Term.objects.filter(year__gte=admission_year).values_list('year', flat=True).distinct().order_by('-year')
    years_list = list(years)
    
    # Default to the most recent year if available
    selected_year = request.GET.get('year', years_list[0] if years_list else None)
    
    # Get terms for the selected year
    terms = Term.objects.filter(year=selected_year).order_by('name')
    subjects = Subject.objects.all()
    progress_data = []
    
    # For year analysis
    year_subjects_data = {}
    term_count = 0

    for term in terms:
        term_data = {
            'term': term,
            'subjects': [],
            'term_average': 0,
            'overall_grade': '',
            'position': ''
        }
        
        total_score = 0
        subject_count = 0
        
        for subject in subjects:
            try:
                cat = CAT.objects.get(student=student, term=term, subject=subject)
                
                # Fix: Calculate average based only on completed CATs
                completed_cats = []
                if cat.cat1 is not None and cat.cat1 > 0:
                    completed_cats.append(cat.cat1)
                if cat.cat2 is not None and cat.cat2 > 0:
                    completed_cats.append(cat.cat2)
                if cat.cat3 is not None and cat.cat3 > 0:
                    completed_cats.append(cat.cat3)
                
                # Calculate actual average based on completed CATs only
                if completed_cats:
                    subject_average = sum(completed_cats) / len(completed_cats)
                else:
                    subject_average = 0

                 # Get appropriate grade and position for this subject based on actual average
                subject_grade = get_letter_grade(subject_average)
                _, subject_position = get_grade_and_position(subject_average)
                
                subject_data = {
                    'subject': subject,
                    'cat1': cat.cat1,
                    'cat2': cat.cat2,
                    'cat3': cat.cat3,
                    'average': subject_average,  # Use our recalculated average
                    'grade': subject_grade,
                    'grade_points': get_grade_points(subject_average),
                    'position': subject_position,  # Use the position from our function, not cat.position
                    'cat_id': cat.pk,
                    # 'average': subject_average,  # Use our recalculated average
                    # 'grade': get_letter_grade(subject_average),
                    # 'grade_points': get_grade_points(subject_average),
                    # 'position': cat.position,
                    # 'cat_id': cat.pk
                }
                
                if completed_cats:  # Only count subjects with at least one completed CAT
                    total_score += subject_average
                    subject_count += 1
                
                # Accumulate data for year analysis
                if subject.id not in year_subjects_data:
                    year_subjects_data[subject.id] = {
                        'subject': subject,
                        'total_score': subject_average,
                        'term_count': 1 if completed_cats else 0,
                    }
                else:
                    year_subjects_data[subject.id]['total_score'] += subject_average
                    if completed_cats:
                        year_subjects_data[subject.id]['term_count'] += 1
                
            except CAT.DoesNotExist:
                subject_data = {
                    'subject': subject,
                    'cat1': 'N/A',
                    'cat2': 'N/A',
                    'cat3': 'N/A',
                    'average': 'N/A',
                    'grade': 'N/A',
                    'grade_points': 'N/A',
                    'position': 'N/A',
                    'cat_id': None  # So template won't break
                }
            
            term_data['subjects'].append(subject_data)
        
        # Calculate term averages if there are subjects
        if subject_count > 0:
            term_data['term_average'] = round(total_score / subject_count, 2)
            # Determine overall grade based on term average
            term_data['overall_grade'], term_data['position'] = get_grade_and_position(term_data['term_average'])
        
        progress_data.append(term_data)
        term_count += 1
    
    # Process year analysis if all three terms are present
    has_all_terms = term_count == 3
    year_analysis = None
    
    if has_all_terms:
        year_analysis = {
            'subjects': [],
            'year_average': 0,
            'overall_grade': '',
            'position': ''
        }
        
        total_year_score = 0
        subjects_with_data = 0
        
        for subject_id, data in year_subjects_data.items():
            if data['term_count'] == 3:  # Only include subjects with data for all 3 terms
                avg_score = round(data['total_score'] / 3, 2)
                grade, position = get_grade_and_position(avg_score)
                
                subject_year_data = {
                    'subject': data['subject'],
                    'average': avg_score,
                    'grade': grade,
                    'position': position
                }
                
                year_analysis['subjects'].append(subject_year_data)
                total_year_score += avg_score
                subjects_with_data += 1
        
        if subjects_with_data > 0:
            year_analysis['year_average'] = round(total_year_score / subjects_with_data, 2)
            year_analysis['overall_grade'], year_analysis['position'] = get_grade_and_position(year_analysis['year_average'])
            
            # Sort subjects by average score (descending)
            year_analysis['subjects'].sort(key=lambda x: x['average'] if isinstance(x['average'], (int, float)) else 0, reverse=True)

    context = {
        'student': student,
        'progress_data': progress_data,
        'years': years_list,
        'selected_year': selected_year,
        'year_analysis': year_analysis,
        'has_all_terms': has_all_terms,
    }
    return render(request, 'marks/student_progress.html', context)

# Helper functions for grade calculation
def get_letter_grade(score):
    if score >= 80:
        return 'A'
    elif score >= 75:
        return 'A-'
    elif score >= 70:
        return 'B+'
    elif score >= 65:
        return 'B'
    elif score >= 60:
        return 'B-'
    elif score >= 55:
        return 'C+'
    elif score >= 50:
        return 'C'
    elif score >= 40:
        return 'D'
    else:
        return 'F'

def get_grade_points(score):
    if score >= 80:
        return 4.0
    elif score >= 75:
        return 3.7
    elif score >= 70:
        return 3.3
    elif score >= 65:
        return 3.0
    elif score >= 60:
        return 2.7
    elif score >= 55:
        return 2.3
    elif score >= 50:
        return 2.0
    elif score >= 40:
        return 1.0
    else:
        return 0.0

# This function should already exist in your code
# but I'm adding a definition in case it doesn't
def get_grade_and_position(average):
    if average >= 80:
        return 'A', 'First Class'
    elif average >= 75:
        return 'A-', 'First Class'
    elif average >= 70:
        return 'B+', 'First Class'
    elif average >= 65:
        return 'B', 'Second Class Upper'
    elif average >= 60:
        return 'B-', 'Second Class Upper'
    elif average >= 55:
        return 'C+', 'Second Class Lower'
    elif average >= 50:
        return 'C', 'Second Class Lower'
    elif average >= 40:
        return 'D', 'Pass'
    else:
        return 'F', 'Fail'

# Helper function to get grade and position based on average score
def get_grade_and_position(average):
    if average >= 80:
        return 'A', 'First Class'
    elif average >= 75:
        return 'A-', 'First Class'
    elif average >= 70:
        return 'B+', 'First Class'
    elif average >= 65:
        return 'B', 'Second Class Upper'
    elif average >= 60:
        return 'B-', 'Second Class Upper'
    elif average >= 55:
        return 'C+', 'Second Class Lower'
    elif average >= 50:
        return 'C', 'Second Class Lower'
    elif average >= 40:
        return 'D', 'Pass'
    else:
        return 'F', 'Fail'

#logged in user to see his marks

@login_required
def individual_student_progress(request):
    try:
        student = Student.objects.get(admission_number=request.user.username)
    except Student.DoesNotExist:
        return render(request, 'marks/no_results.html', {'message': 'Student record not found.'})

    admission_year = student.admission_date.year
    terms = Term.objects.filter(year__gte=admission_year).order_by('-year', 'name')

    subjects = Subject.objects.all()
    progress_data = []

    for term in terms:
        term_data = {
            'term': term,
            'subjects': [],
            'term_average': 0,
            'overall_grade': '',
            'position': ''
        }
        
        total_score = 0
        subject_count = 0
        
        for subject in subjects:
            try:
                cat = CAT.objects.get(student=student, term=term, subject=subject)
                
                # Fix: Calculate average based only on completed CATs
                completed_cats = []
                if cat.cat1 is not None and cat.cat1 > 0:
                    completed_cats.append(cat.cat1)
                if cat.cat2 is not None and cat.cat2 > 0:
                    completed_cats.append(cat.cat2)
                if cat.cat3 is not None and cat.cat3 > 0:
                    completed_cats.append(cat.cat3)
                
                # Calculate actual average based on completed CATs only
                if completed_cats:
                    subject_average = sum(completed_cats) / len(completed_cats)
                else:
                    subject_average = 0
                
                subject_data = {
                    'subject': subject.name,
                    'cat1': cat.cat1,
                    'cat2': cat.cat2,
                    'cat3': cat.cat3,
                    'average': subject_average,  # Use our recalculated average
                    'grade': get_letter_grade(subject_average),  # You'll need to add this function
                    'grade_points': get_grade_points(subject_average),  # You'll need to add this function
                    'position': cat.position
                }
                
                if completed_cats:  # Only count subjects with at least one completed CAT
                    total_score += subject_average
                    subject_count += 1
                
            except CAT.DoesNotExist:
                subject_data = {
                    'subject': subject.name,
                    'cat1': 'N/A',
                    'cat2': 'N/A',
                    'cat3': 'N/A',
                    'average': 'N/A',
                    'grade': 'N/A',
                    'grade_points': 'N/A',
                    'position': 'N/A'
                }
            
            term_data['subjects'].append(subject_data)
        
        # Calculate term averages
        if subject_count > 0:
            term_data['term_average'] = round(total_score / subject_count, 2)
            if term_data['term_average'] >= 80:
                term_data['overall_grade'] = 'A'
                term_data['position'] = 'First Class'
            elif term_data['term_average'] >= 75:
                term_data['overall_grade'] = 'A-'
                term_data['position'] = 'First Class'
            elif term_data['term_average'] >= 70:
                term_data['overall_grade'] = 'B+'
                term_data['position'] = 'First Class'
            elif term_data['term_average'] >= 65:
                term_data['overall_grade'] = 'B'
                term_data['position'] = 'Second Class Upper'
            elif term_data['term_average'] >= 60:
                term_data['overall_grade'] = 'B-'
                term_data['position'] = 'Second Class Upper'
            elif term_data['term_average'] >= 55:
                term_data['overall_grade'] = 'C+'
                term_data['position'] = 'Second Class Lower'
            elif term_data['term_average'] >= 50:
                term_data['overall_grade'] = 'C'
                term_data['position'] = 'Second Class Lower'
            elif term_data['term_average'] >= 40:
                term_data['overall_grade'] = 'D'
                term_data['position'] = 'Pass'
            else:
                term_data['overall_grade'] = 'F'
                term_data['position'] = 'Fail'
        
        progress_data.append(term_data)

    context = {
        'student': student,
        'progress_data': progress_data,
    }
    return render(request, 'marks/individual_student_progress.html', context)

# Helper functions for grade calculation
def get_letter_grade(score):
    if score >= 80:
        return 'A'
    elif score >= 75:
        return 'A-'
    elif score >= 70:
        return 'B+'
    elif score >= 65:
        return 'B'
    elif score >= 60:
        return 'B-'
    elif score >= 55:
        return 'C+'
    elif score >= 50:
        return 'C'
    elif score >= 40:
        return 'D'
    else:
        return 'F'

def get_grade_points(score):
    if score >= 80:
        return 4.0
    elif score >= 75:
        return 3.7
    elif score >= 70:
        return 3.3
    elif score >= 65:
        return 3.0
    elif score >= 60:
        return 2.7
    elif score >= 55:
        return 2.3
    elif score >= 50:
        return 2.0
    elif score >= 40:
        return 1.0
    else:
        return 0.0

#download reports view 
from myapp.utils import (
    generate_term_report_pdf, 
    generate_year_report_pdf,
    get_term_data,
    get_year_data
)

def generate_progress_data(student):
    terms = Term.objects.all().order_by('-year', 'name')
    subjects = Subject.objects.all()
    progress_data = []

    for term in terms:
        term_data = {
            'term': term,
            'subjects': [],
            'term_average': 0,
            'overall_grade': '',
            'position': ''
        }
        
        total_score = 0
        subject_count = 0
        
        for subject in subjects:
            try:
                cat = CAT.objects.get(student=student, term=term, subject=subject)
                
                # Fix: Calculate average based only on completed CATs
                completed_cats = []
                if cat.cat1 is not None and cat.cat1 > 0:
                    completed_cats.append(cat.cat1)
                if cat.cat2 is not None and cat.cat2 > 0:
                    completed_cats.append(cat.cat2)
                if cat.cat3 is not None and cat.cat3 > 0:
                    completed_cats.append(cat.cat3)
                
                # Calculate actual average based on completed CATs only
                if completed_cats:
                    subject_average = sum(completed_cats) / len(completed_cats)
                else:
                    subject_average = 0
                
                subject_data = {
                    'subject': subject,
                    'cat1': cat.cat1,
                    'cat2': cat.cat2,
                    'cat3': cat.cat3,
                    'average': subject_average,  # Use our recalculated average instead of cat.end_term
                    'grade': get_letter_grade(subject_average),  # Calculate grade based on new average
                    'grade_points': get_grade_points(subject_average),  # Calculate points based on new average
                    'position': cat.position
                }
                
                if completed_cats:  # Only count subjects with at least one completed CAT
                    total_score += subject_average
                    subject_count += 1
                
            except CAT.DoesNotExist:
                subject_data = {
                    'subject': subject,
                    'cat1': 'N/A',
                    'cat2': 'N/A',
                    'cat3': 'N/A',
                    'average': 'N/A',
                    'grade': 'N/A',
                    'grade_points': 'N/A',
                    'position': 'N/A'
                }
            
            term_data['subjects'].append(subject_data)
        
        if subject_count > 0:
            term_data['term_average'] = round(total_score / subject_count, 2)
            term_data['overall_grade'], term_data['position'] = get_grade_and_position(term_data['term_average'])
        
        progress_data.append(term_data)
    
    return progress_data


@login_required
def download_year_report(request, student_id, year):
    student = get_object_or_404(Student, id=student_id)
    # You may need to fetch or regenerate progress_data here
    # Example assumes progress_data available in session or re-queried:
    progress_data = generate_progress_data(student)  # You define this!
    year_data = get_year_data(progress_data, year)
    return generate_year_report_pdf(student, year, year_data)

@login_required
def download_term_report(request, student_id, term_id):
    student = get_object_or_404(Student, id=student_id)
    term = get_object_or_404(Term, id=term_id)
    # Same, regenerate or fetch progress_data
    progress_data = generate_progress_data(student)
    term_data = get_term_data(progress_data, term.year, term.name)
    return generate_term_report_pdf(student, term_data)



@login_required
@user_passes_test(is_staff_user)
def class_lists(request):
    classes = Class_of_study.objects.all().order_by('name', 'stream')
    return render(request, 'school/class_list.html', {
        'classes': classes
    })


@login_required
@user_passes_test(is_staff_user)
def term_list(request, class_id):
    class_of_study = get_object_or_404(Class_of_study, id=class_id)
    terms = Term.objects.filter(
        # your filtering conditions here
    ).order_by('-year', 'name')  # Sort by year descending, then term name
    return render(request, 'school/term_list.html', {
        'class_of_study': class_of_study,
        'terms': terms
    })



@login_required
def student_list(request, class_id, term_id):
    class_of_study = get_object_or_404(Class_of_study, id=class_id)
    term = get_object_or_404(Term, id=term_id)
    subjects = Subject.objects.all()
    
    # Get all CAT records for that class and term
    cats = CAT.objects.filter(term=term, class_of_study=class_of_study)
    
    # Extract unique students from those CAT records
    students = Student.objects.filter(id__in=cats.values_list('student_id', flat=True).distinct())
    
    # Create nested dicts
    students_results = {}
    student_averages = {}
    
    for student in students:
        student_cats = cats.filter(student=student)
        students_results[student.id] = {}
        
        total_score = 0
        valid_subjects = 0
        
        for cat in student_cats:
            students_results[student.id][cat.subject.id] = cat
            total_score += cat.end_term
            valid_subjects += 1
        
        # Calculate average and grade
        if valid_subjects > 0:
            term_average = round(total_score / valid_subjects, 2)
            temp_cat = CAT(cat1=term_average, cat2=term_average, cat3=term_average)
            temp_cat.end_term = term_average
            
            grade_points, letter_grade = temp_cat.assign_grade_points()
            position = temp_cat.determine_position()
            
            student_averages[student.id] = {
                'average': term_average,
                'grade': letter_grade,
                'grade_points': grade_points,
                'position': position,
                'name': student.name,
                'admission': student.admission_number
            }
    
    # Sort by average
    sorted_students = dict(sorted(
        student_averages.items(), 
        key=lambda x: x[1]['average'], 
        reverse=True
    ))
    
    # Add position numbers
    position = 1
    for student_id in sorted_students:
        sorted_students[student_id]['position_number'] = position
        position += 1
    
    return render(request, 'school/student_list.html', {
        'class_of_study': class_of_study,
        'term': term,
        'students': sorted_students,
        'subjects': subjects,
        'students_results': students_results,
    })



@login_required
def subject_analysis(request, class_id, term_id):
    class_of_study = get_object_or_404(Class_of_study, id=class_id)
    term = get_object_or_404(Term, id=term_id)
    subjects = Subject.objects.all()
    
    # Calculate average score for each subject
    subject_averages = {}
    for subject in subjects:
        cats = CAT.objects.filter(
            class_of_study=class_of_study,  # Changed from student__current_class
            term=term,
            subject=subject
        )
        if cats.exists():
            total_score = sum(cat.end_term for cat in cats)
            average = round(total_score / cats.count(), 2)
            
            # Additional analysis
            highest_score = max(cat.end_term for cat in cats)
            lowest_score = min(cat.end_term for cat in cats)
            
            subject_averages[subject.name] = {
                'average': average,
                'highest_score': highest_score,
                'lowest_score': lowest_score,
                'total_students': cats.count()
            }
    
    # Sort subjects by average score
    sorted_subjects = dict(sorted(
        subject_averages.items(), 
        key=lambda x: x[1]['average'], 
        reverse=True
    ))
    
    return render(request, 'school/subject_analysis.html', {
        'class_of_study': class_of_study,
        'term': term,
        'subject_averages': sorted_subjects
    })


@login_required
def student_profile(request):
    """View for students to see their profile"""
    # Assuming student is linked to user via admission number or some other field
    student = get_object_or_404(Student, admission_number=request.user.username)
    
    context = {
        'student': student
    }
    return render(request, 'students/profile.html', context)

@login_required
def edit_student_profile(request):
    """View for students to edit certain fields of their profile"""
    student = get_object_or_404(Student, admission_number=request.user.username)
    
    if request.method == 'POST':
        form = StudentProfileEditForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('student_profile')
    else:
        form = StudentProfileEditForm(instance=student)
    
    context = {
        'form': form,
        'student': student
    }
    return render(request, 'students/edit_profile.html', context)



@login_required
@user_passes_test(is_staff_user)
def class_list(request):
    classes = Class_of_study.objects.all()
    return render(request, 'class/class_list.html', {'classes': classes})


@login_required
@user_passes_test(is_staff_user)
def class_create(request):
    if request.method == 'POST':
        form = ClassForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('class_list')
    else:
        form = ClassForm()
    return render(request, 'class/class_form.html', {'form': form})


@login_required
@user_passes_test(is_staff_user)
def class_detail(request, pk):
    class_instance = get_object_or_404(Class_of_study, pk=pk)
    return render(request, 'class/class_detail.html', {'class_instance': class_instance})


@login_required
@user_passes_test(is_staff_user)
def class_update(request, pk):
    class_instance = get_object_or_404(Class_of_study, pk=pk)
    if request.method == 'POST':
        form = ClassForm(request.POST, instance=class_instance)
        if form.is_valid():
            form.save()
            return redirect('class_list')
    else:
        form = ClassForm(instance=class_instance)
    return render(request, 'class/class_form.html', {'form': form})


@login_required
@user_passes_test(is_staff_user)
def class_delete(request, pk):
    class_instance = get_object_or_404(Class_of_study, pk=pk)
    if request.method == 'POST':
        class_instance.delete()
        return redirect('class_list')
    return render(request, 'class/class_confirm_delete.html', {'class_instance': class_instance})





@login_required
@user_passes_test(is_staff_user)
def subject_list(request):
    subjects = Subject.objects.all()
    return render(request, 'subject/subject_list.html', {'subjects': subjects})


@login_required
@user_passes_test(is_staff_user)
def subject_create(request):
    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('subject_list')
    else:
        form = SubjectForm()
    return render(request, 'subject/subject_form.html', {'form': form})


@login_required
@user_passes_test(is_staff_user)
def subject_detail(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    return render(request, 'subject/subject_detail.html', {'subject': subject})


@login_required
@user_passes_test(is_staff_user)
def subject_update(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    if request.method == 'POST':
        form = SubjectForm(request.POST, instance=subject)
        if form.is_valid():
            form.save()
            return redirect('subject_list')
    else:
        form = SubjectForm(instance=subject)
    return render(request, 'subject/subject_form.html', {'form': form})


@login_required
@user_passes_test(is_staff_user)
def subject_delete(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    if request.method == 'POST':
        subject.delete()
        return redirect('subject_list')
    return render(request, 'subject/subject_confirm_delete.html', {'subject': subject})


@login_required
@user_passes_test(is_staff_user)
def students_list(request):
    students = Student.objects.all()
    return render(request, 'students/database_student_list.html', {'students': students})


@login_required
@user_passes_test(is_staff_user)
def student_create(request):
    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('student_list')
    else:
        form = StudentForm()
    return render(request, 'students/student_form.html', {'form': form})


@login_required
@user_passes_test(is_staff_user)
def student_detail(request, pk):
    student = get_object_or_404(Student, pk=pk)
    return render(request, 'students/student_detail.html', {'student': student})


@login_required
@user_passes_test(is_staff_user)
def student_update(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        form = StudentForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            return redirect('students_list')
    else:
        form = StudentForm(instance=student)
    return render(request, 'students/student_form.html', {'form': form})


@login_required
@user_passes_test(is_staff_user)
def student_delete(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        student.delete()
        return redirect('student_list')
    return render(request, 'students/student_confirm_delete.html', {'student': student})



@login_required
@user_passes_test(is_staff_user)
def term_lists(request):
    terms = Term.objects.all()
    return render(request, 'terms/term_list.html', {'terms': terms})


@login_required
@user_passes_test(is_staff_user)
def term_create(request):
    if request.method == 'POST':
        form = TermForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('term_list')
    else:
        form = TermForm()
    return render(request, 'terms/term_form.html', {'form': form})


@login_required
@user_passes_test(is_staff_user)
def term_detail(request, pk):
    term = get_object_or_404(Term, pk=pk)
    return render(request, 'terms/term_detail.html', {'term': term})


@login_required
@user_passes_test(is_staff_user)
def term_update(request, pk):
    term = get_object_or_404(Term, pk=pk)
    if request.method == 'POST':
        form = TermForm(request.POST, instance=term)
        if form.is_valid():
            form.save()
            return redirect('term_list')
    else:
        form = TermForm(instance=term)
    return render(request, 'terms/term_form.html', {'form': form})


@login_required
@user_passes_test(is_staff_user)
def term_delete(request, pk):
    term = get_object_or_404(Term, pk=pk)
    if request.method == 'POST':
        term.delete()
        return redirect('term_list')
    return render(request, 'terms/term_confirm_delete.html', {'term': term})




@login_required
@user_passes_test(is_staff_user)
def cat_list(request):
    cats = CAT.objects.all()
    return render(request, 'cats/cat_list.html', {'cats': cats})


from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def student_search(request):
    if request.method == 'GET':
        query = request.GET.get('term', '')
        students = Student.objects.filter(admission_number__icontains=query)[:10]
        results = []
        for student in students:
            results.append({
                'id': student.id,
                'label': f"{student.admission_number} - {student.name}",  # What appears in dropdown
                'value': student.admission_number,  # Filled into search box
                'name': student.name  # Sent back to display student's name
            })
        return JsonResponse(results, safe=False)


def get_class_of_study(request):
    student_id = request.GET.get('student_id')
    try:
        student = Student.objects.get(id=student_id)
        class_of_study = student.current_class  # current_class is FK to Class_of_study
        data = {
            'class_of_study': f"{class_of_study.name} - {class_of_study.stream}"
        }
    except Student.DoesNotExist:
        data = {'class_of_study': ''}
    return JsonResponse(data)

    

@login_required
@user_passes_test(is_staff_user)
def cat_create(request):
    if request.method == 'POST':
        form = CATForm(request.POST)
        if form.is_valid():
            cat = form.save(commit=False)
            student_id = request.POST.get('student')
            
            if student_id:
                try:
                    student = Student.objects.get(id=student_id)
                    cat.student = student
                    
                    # Ensure class_of_study is set only if student has a current_class
                    if student.current_class:
                        cat.class_of_study = student.current_class
                    else:
                        # Optional: Add a message or handle the case where student has no current class
                        messages.warning(request, f"Student {student} has no current class assigned.")
                except Student.DoesNotExist:
                    messages.error(request, "Selected student does not exist.")
                    return render(request, 'cats/cat_form.html', {'form': form})
            
            cat.save()
            messages.success(request, "The  Exams record has been successfully created.")
            return redirect('cat_create')
    else:
        form = CATForm()
    
    return render(request, 'cats/cat_form.html', {'form': form})


@login_required
@user_passes_test(is_staff_user)
def cat_detail(request, pk):
    cat = get_object_or_404(CAT, pk=pk)
    return render(request, 'cats/cat_detail.html', {'cat': cat})


@login_required
@user_passes_test(is_staff_user)
def cat_update(request, pk):
    cat = get_object_or_404(CAT, pk=pk)
    if request.method == 'POST':
        form = CATForm(request.POST, instance=cat)
        if form.is_valid():
            form.save()
            # Redirect back to the same CAT detail view
            return redirect('cat_detail', pk=cat.pk)
    else:
        form = CATForm(instance=cat)
    return render(request, 'cats/updatecat_form.html', {'form': form})



@login_required
@user_passes_test(is_staff_user)
def cat_delete(request, pk):
    cat = get_object_or_404(CAT, pk=pk)
    if request.method == 'POST':
        cat.delete()
        return redirect('cat_list')
    return render(request, 'cats/cat_confirm_delete.html', {'cat': cat})




@login_required
def student_population_graph(request):
    # Get data aggregated by year
    population_data = Term.objects.values('year').annotate(
        student_count=Count('cat__student', distinct=True)
    ).order_by('year')
    
    # Prepare data for the template
    years = [data['year'] for data in population_data]
    counts = [data['student_count'] for data in population_data]
    
    context = {
        'years': years,  
        'counts': counts,
        'population_data': population_data,
    }
    
    return render(request, 'graph/population_graph.html', context)

@login_required
def class_distribution_view(request):
    # Get all available years from Term model
    available_years = Term.objects.values_list('year', flat=True).distinct().order_by('-year')
    
    # Get the selected year (default to latest year if none selected)
    selected_year = request.GET.get('year', available_years.first())
    
    # Get students who have CATs in the selected year, grouped by their previous class
    previous_class_distribution = CAT.objects.filter(
        term__year=selected_year
    ).values(
        'class_of_study__name', 
        'class_of_study__stream'
    ).annotate(
        student_count=Count('student', distinct=True)
    ).order_by('class_of_study__name', 'class_of_study__stream')
    
    # Prepare data for the chart
    classes = []
    counts = []
    labels = []
    
    for item in previous_class_distribution:
        class_name = item['class_of_study__name']
        stream = item['class_of_study__stream']
        count = item['student_count']
        
        classes.append(class_name)
        counts.append(count)
        labels.append(f"{class_name} - {stream}")
    
    context = {
        'class_distribution': previous_class_distribution,
        'classes': classes,
        'counts': counts,
        'labels': labels,
        'available_years': available_years,
        'selected_year': int(selected_year) if selected_year else None,
    }
    
    return render(request, 'graph/class_distribution.html', context)

@login_required
@user_passes_test(is_staff_user)
def search_student(request):
    form = StudentSearchForm(request.GET or None)
    students = None

    if form.is_valid():
        query = form.cleaned_data.get("query")
        if query:
            students = Student.objects.filter(
                models.Q(name__icontains=query) | 
                models.Q(admission_number__icontains=query) |
                models.Q(current_class__name__icontains=query)
            )

    return render(request, "search/search_student.html", {"form": form, "students": students})


#rankings for specific class
@login_required
@user_passes_test(is_staff_user)
def student_rankings(request):
    # Get filter parameters from request
    selected_year = request.GET.get('year')
    selected_term = request.GET.get('term')
    selected_class = request.GET.get('class')  # New parameter for class filtering
    
    # Cache key construction with class parameter
    cache_key = f'rankings_{selected_year}_{selected_term}_{selected_class}'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return render(request, 'rankings/student_rankings.html', cached_data)
    
    # Efficiently get filter options using values_list with distinct
    available_years = Term.objects.values_list('year', flat=True)\
        .distinct().order_by('-year')
    available_terms = Term.objects.values_list('name', flat=True).distinct()
    available_classes = Class_of_study.objects.all()  # Get all available classes
    
    if not selected_year:
        selected_year = available_years.first()
    
    selected_year = int(selected_year)
    
    # Optimize term query
    terms_query = Term.objects.filter(year=selected_year)
    if selected_term:
        terms_query = terms_query.filter(name=selected_term)
    
    # Prefetch related CAT data
    cat_prefetch = Prefetch(
        'cats',
        queryset=CAT.objects.select_related('subject', 'class_of_study')
    )
    
    rankings = []
    
    for term in terms_query:
        # Base query with prefetch
        base_query = Student.objects.prefetch_related(cat_prefetch).filter(cats__term=term)
        
        # Apply class filter using class_of_study instead of current_class
        if selected_class:
            base_query = base_query.filter(cats__class_of_study_id=selected_class)
        
        # Optimize student query with annotations and prefetch_related
        student_rankings = (
            base_query
            .annotate(
                average_score=Coalesce(
                    Avg('cats__end_term'),
                    0.0
                ),
                subjects_count=Count('cats__subject', distinct=True),
                total_grade_points=Coalesce(
                    Avg('cats__grade_points'),
                    0.0
                )
            )
            .filter(subjects_count__gt=0)
            .select_related('current_class')
            .order_by('-average_score')
        ).distinct()
        
        # Process results in chunks to reduce memory usage
        CHUNK_SIZE = 50
        term_results = {
            'term': term,
            'students': []
        }
        
        for rank, student in enumerate(student_rankings, 1):
            # Get subject grades efficiently using prefetched data
            subject_grades = [
                cat for cat in student.cats.all()
                if cat.term_id == term.id and 
                   (not selected_class or cat.class_of_study_id == int(selected_class))
            ]
            
            student_data = {
                'rank': rank,
                'student': student,
                'average_score': round(student.average_score, 2),
                'grade_point_average': round(student.total_grade_points, 2),
                'subjects': subject_grades,
                'total_subjects': student.subjects_count,
                'overall_grade': _calculate_overall_grade(student.total_grade_points)
            }
            
            term_results['students'].append(student_data)
            
            # Process in chunks to reduce memory usage
            if len(term_results['students']) >= CHUNK_SIZE:
                rankings.append(term_results)
                term_results = {
                    'term': term,
                    'students': []
                }
        
        if term_results['students']:
            rankings.append(term_results)
    
    context = {
        'rankings': rankings,
        'available_years': available_years,
        'available_terms': available_terms,
        'available_classes': available_classes,
        'selected_year': selected_year,
        'selected_term': selected_term,
        'selected_class': selected_class,
    }
    
    # Cache the results
    cache.set(cache_key, context, timeout=3600)  # Cache for 1 hour
    
    return render(request, 'rankings/student_rankings.html', context)


def _calculate_overall_grade(gpa):
    """Helper function to calculate overall grade"""
    if gpa >= 3.7:
        return 'A'
    elif gpa >= 3.3:
        return 'B+'
    elif gpa >= 3.0:
        return 'B'
    elif gpa >= 2.7:
        return 'B-'
    elif gpa >= 2.3:
        return 'C+'
    elif gpa >= 2.0:
        return 'C'
    return 'F'

@login_required
@user_passes_test(is_staff_user)
def form_rankings(request):
    # Get filter parameters from request
    selected_year = request.GET.get('year')
    selected_term = request.GET.get('term')
    selected_form = request.GET.get('form')  # Filter for specific form (Form 1, Form 2, etc.)
    
    # Cache key construction with form parameter
    cache_key = f'form_rankings_{selected_year}_{selected_term}_{selected_form}'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return render(request, 'rankings/form_rankings.html', cached_data)
    
    # Efficiently get filter options
    available_years = Term.objects.values_list('year', flat=True)\
        .distinct().order_by('-year')
    available_terms = Term.objects.values_list('name', flat=True).distinct()
    
    # Get distinct form names (without stream)
    available_forms = Class_of_study.objects.values_list('name', flat=True)\
        .distinct().order_by('name')
    
    if not selected_year:
        selected_year = available_years.first()
    
    selected_year = int(selected_year)
    
    # Optimize term query
    terms_query = Term.objects.filter(year=selected_year)
    if selected_term:
        terms_query = terms_query.filter(name=selected_term)
    
    # Prefetch related CAT data
    cat_prefetch = Prefetch(
        'cats',
        queryset=CAT.objects.select_related('subject', 'class_of_study')
    )
    
    form_rankings = []
    
    for term in terms_query:
        # Base query with prefetch
        base_query = Student.objects.prefetch_related(cat_prefetch).filter(cats__term=term)
        
        # Apply form filter if selected - now using CAT's class_of_study
        if selected_form:
            base_query = base_query.filter(cats__class_of_study__name=selected_form)
        
        # Optimize student query with annotations and prefetch_related
        student_rankings = (
            base_query
            .annotate(
                average_score=Coalesce(
                    Avg('cats__end_term'),
                    0.0
                ),
                subjects_count=Count('cats__subject', distinct=True),
                total_grade_points=Coalesce(
                    Avg('cats__grade_points'),
                    0.0
                )
            )
            .filter(subjects_count__gt=0)
            .select_related('current_class')
            .order_by('-average_score')
        ).distinct()
        
        # Process results in chunks to reduce memory usage
        CHUNK_SIZE = 50
        term_results = {
            'term': term,
            'students': []
        }
        
        # No stream grouping - process all students in a single list
        for rank, student in enumerate(student_rankings, 1):
            # Get subject grades efficiently using prefetched data
            subject_grades = [
                cat for cat in student.cats.all()
                if cat.term_id == term.id and 
                   (not selected_form or cat.class_of_study.name == selected_form)
            ]
            
            student_data = {
                'rank': rank,
                'student': student,
                'average_score': round(student.average_score, 2),
                'grade_point_average': round(student.total_grade_points, 2),
                'subjects': subject_grades,
                'total_subjects': student.subjects_count,
                'overall_grade': _calculate_overall_grade(student.total_grade_points)
            }
            
            term_results['students'].append(student_data)
            
            # Process in chunks to free up memory
            if len(term_results['students']) >= CHUNK_SIZE and False:  # Disabled chunking to keep all students in one list
                form_rankings.append(term_results)
                term_results = {
                    'term': term,
                    'students': []
                }
        
        form_rankings.append(term_results)
    
    context = {
        'rankings': form_rankings,
        'available_years': available_years,
        'available_terms': available_terms,
        'available_forms': available_forms,
        'selected_year': selected_year,
        'selected_term': selected_term,
        'selected_form': selected_form,
    }
    
    # Cache the results
    cache.set(cache_key, context, timeout=3600)  # Cache for 1 hour
    
    return render(request, 'rankings/form_rankings.html', context)

@login_required
@user_passes_test(is_staff_user)
def stream_performance(request):
    # Get filter parameters
    selected_year = request.GET.get('year')
    selected_term = request.GET.get('term')
    
    # Cache key for performance
    cache_key = f'stream_performance_{selected_year}_{selected_term}'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return render(request, 'rankings/stream_performance.html', cached_data)
    
    # Get available filter options
    available_years = Term.objects.values_list('year', flat=True)\
        .distinct().order_by('-year')
    available_terms = Term.objects.values_list('name', flat=True).distinct()
    
    if not selected_year:
        selected_year = available_years.first()
    
    selected_year = int(selected_year)
    
    # Get terms based on filters
    terms_query = Term.objects.filter(year=selected_year)
    if selected_term:
        terms_query = terms_query.filter(name=selected_term)
    
    # Get all subjects for the header
    subjects = Subject.objects.all().order_by('name')
    
    stream_analytics = []
    
    for term in terms_query:
        # Get all streams that have students with CATs in this term
        streams = Class_of_study.objects.filter(
            students__cats__term=term
        ).distinct()
        
        term_data = {
            'term': term,
            'streams': []
        }
        
        for stream in streams:
            # Get subject-wise performance for this stream
            subject_performance = []
            total_points = 0
            subject_count = 0
            
            for subject in subjects:
                # Calculate average performance for this subject in this stream
                subject_stats = CAT.objects.filter(
                    student__current_class=stream,
                    term=term,
                    subject=subject
                ).aggregate(
                    avg_score=Coalesce(Avg('end_term'), 0.0),
                    avg_points=Coalesce(Avg('grade_points'), 0.0),
                    student_count=Count('student', distinct=True)
                )
                
                if subject_stats['student_count'] > 0:
                    grade = _get_letter_grade(subject_stats['avg_points'])
                    subject_performance.append({
                        'subject': subject,
                        'average_score': round(subject_stats['avg_score'], 2),
                        'grade_points': round(subject_stats['avg_points'], 2),
                        'letter_grade': grade,
                        'students': subject_stats['student_count']
                    })
                    total_points += subject_stats['avg_points']
                    subject_count += 1
            
            # Calculate overall stream performance
            if subject_count > 0:
                stream_mean_points = total_points / subject_count
                stream_mean_grade = _get_letter_grade(stream_mean_points)
                
                # Get total number of students in stream
                student_count = Student.objects.filter(
                    current_class=stream,
                    cats__term=term
                ).distinct().count()
                
                stream_data = {
                    'stream': stream,
                    'subjects': subject_performance,
                    'mean_points': round(stream_mean_points, 2),
                    'mean_grade': stream_mean_grade,
                    'total_students': student_count
                }
                
                term_data['streams'].append(stream_data)
        
        # Sort streams by mean points
        term_data['streams'].sort(key=lambda x: x['mean_points'], reverse=True)
        
        # Add rankings
        for rank, stream_data in enumerate(term_data['streams'], 1):
            stream_data['rank'] = rank
        
        stream_analytics.append(term_data)
    
    context = {
        'analytics': stream_analytics,
        'subjects': subjects,
        'available_years': available_years,
        'available_terms': available_terms,
        'selected_year': selected_year,
        'selected_term': selected_term,
    }
    
    # Cache the results
    cache.set(cache_key, context, timeout=3600)  # Cache for 1 hour
    
    return render(request, 'rankings/stream_performance.html', context)

def _get_letter_grade(points):
    """Helper function to get letter grade from points"""
    if points >= 3.7:
        return 'A'
    elif points >= 3.3:
        return 'B+'
    elif points >= 3.0:
        return 'B'
    elif points >= 2.7:
        return 'B-'
    elif points >= 2.3:
        return 'C+'
    elif points >= 2.0:
        return 'C'
    return 'F'


@login_required
@user_passes_test(is_staff_user)
def subject_performance(request):
    # Get filter parameters
    selected_year = request.GET.get('year')
    selected_term = request.GET.get('term')
    
    # Cache key for performance
    cache_key = f'subject_performance_{selected_year}_{selected_term}'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return render(request, 'rankings/subject_performance.html', cached_data)
    
    # Get available filter options
    available_years = Term.objects.values_list('year', flat=True)\
        .distinct().order_by('-year')
    available_terms = Term.objects.values_list('name', flat=True).distinct()
    
    if not selected_year:
        selected_year = available_years.first()
    
    selected_year = int(selected_year)
    
    # Get terms based on filters
    terms_query = Term.objects.filter(year=selected_year)
    if selected_term:
        terms_query = terms_query.filter(name=selected_term)
    
    # Get all streams for the analysis
    streams = Class_of_study.objects.all().order_by('name', 'stream')
    
    subject_analytics = []
    
    for term in terms_query:
        term_data = {
            'term': term,
            'subjects': []
        }
        
        subjects = Subject.objects.all()
        
        for subject in subjects:
            # Overall subject performance
            overall_stats = CAT.objects.filter(
                term=term,
                subject=subject
            ).aggregate(
                avg_score=Coalesce(Avg('end_term'), 0.0),
                avg_points=Coalesce(Avg('grade_points'), 0.0),
                total_students=Count('student', distinct=True),
                a_count=Count('pk', filter=Q(letter_grade='A')),
                a_minus_count=Count('pk', filter=Q(letter_grade='A-')),
                b_plus_count=Count('pk', filter=Q(letter_grade='B+')),
                b_count=Count('pk', filter=Q(letter_grade='B')),
                b_minus_count=Count('pk', filter=Q(letter_grade='B-')),
                c_plus_count=Count('pk', filter=Q(letter_grade='C+')),
                c_count=Count('pk', filter=Q(letter_grade='C')),
                fail_count=Count('pk', filter=Q(letter_grade='F'))
            )
            
            if overall_stats['total_students'] > 0:
                # Get performance by stream
                stream_performance = []
                for stream in streams:
                    stream_stats = CAT.objects.filter(
                        term=term,
                        subject=subject,
                        student__current_class=stream
                    ).aggregate(
                        avg_score=Coalesce(Avg('end_term'), 0.0),
                        avg_points=Coalesce(Avg('grade_points'), 0.0),
                        student_count=Count('student', distinct=True)
                    )
                    
                    if stream_stats['student_count'] > 0:
                        stream_performance.append({
                            'stream': stream,
                            'average_score': round(stream_stats['avg_score'], 2),
                            'grade_points': round(stream_stats['avg_points'], 2),
                            'students': stream_stats['student_count'],
                            'letter_grade': _get_letter_grade(stream_stats['avg_points'])
                        })
                
                # Calculate quality metrics
                total_quality_grades = (
                    overall_stats['a_count'] + 
                    overall_stats['a_minus_count'] + 
                    overall_stats['b_plus_count']
                )
                quality_percentage = (total_quality_grades / overall_stats['total_students']) * 100 if overall_stats['total_students'] > 0 else 0
                
                subject_data = {
                    'subject': subject,
                    'average_score': round(overall_stats['avg_score'], 2),
                    'grade_points': round(overall_stats['avg_points'], 2),
                    'letter_grade': _get_letter_grade(overall_stats['avg_points']),
                    'total_students': overall_stats['total_students'],
                    'streams': stream_performance,
                    'grade_distribution': {
                        'A': overall_stats['a_count'],
                        'A-': overall_stats['a_minus_count'],
                        'B+': overall_stats['b_plus_count'],
                        'B': overall_stats['b_count'],
                        'B-': overall_stats['b_minus_count'],
                        'C+': overall_stats['c_plus_count'],
                        'C': overall_stats['c_count'],
                        'F': overall_stats['fail_count']
                    },
                    'quality_percentage': round(quality_percentage, 2),
                    'pass_rate': round(((overall_stats['total_students'] - overall_stats['fail_count']) / overall_stats['total_students']) * 100 if overall_stats['total_students'] > 0 else 0, 2)
                }
                
                term_data['subjects'].append(subject_data)
        
        # Sort subjects by grade points
        term_data['subjects'].sort(key=lambda x: (x['grade_points'], x['quality_percentage']), reverse=True)
        
        # Add rankings
        for rank, subject_data in enumerate(term_data['subjects'], 1):
            subject_data['rank'] = rank
        
        subject_analytics.append(term_data)
    
    context = {
        'analytics': subject_analytics,
        'streams': streams,
        'available_years': available_years,
        'available_terms': available_terms,
        'selected_year': selected_year,
        'selected_term': selected_term,
    }
    
    # Cache the results
    cache.set(cache_key, context, timeout=3600)  # Cache for 1 hour
    
    return render(request, 'rankings/subject_performance.html', context)

def _get_letter_grade(points):
    """Helper function to get letter grade from points"""
    if points >= 3.7:
        return 'A'
    elif points >= 3.3:
        return 'B+'
    elif points >= 3.0:
        return 'B'
    elif points >= 2.7:
        return 'B-'
    elif points >= 2.3:
        return 'C+'
    elif points >= 2.0:
        return 'C'
    return 'F'



@login_required
@user_passes_test(is_staff_user)
def teacher_create(request):
    if request.method == 'POST':
        form = TeacherForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Teacher added successfully!')
            return redirect('teacher_list')  # Redirect to teacher list page
    else:
        form = TeacherForm()
    return render(request, 'teachers/teacher_form.html', {'form': form})



@login_required
def teacher_detail(request, teacher_id):
    teacher = get_object_or_404(Teacher, id=teacher_id)
    
    User = get_user_model()
    teacher_user = User.objects.filter(username=teacher.username).first()

    can_message = teacher_user is not None and teacher_user != request.user

    return render(request, 'teachers/teacher_detail.html', {
        'teacher': teacher,
        'can_message': can_message,
    })

@login_required
@user_passes_test(is_staff_user)
def teacher_edit(request, teacher_id):
    teacher = get_object_or_404(Teacher, id=teacher_id)
    if request.method == 'POST':
        form = TeacherEditForm(request.POST, request.FILES, instance=teacher)
        if form.is_valid():
            form.save()
            messages.success(request, 'Teacher details updated successfully!')
            return redirect('teacher_list')
    else:
        form = TeacherEditForm(instance=teacher)
    return render(request, 'teachers/teacher_form.html', {'form': form})


@login_required
@user_passes_test(is_staff_user)
def teacher_delete(request, teacher_id):
    teacher = get_object_or_404(Teacher, id=teacher_id)
    if request.method == 'POST':
        teacher.delete()
        messages.success(request, 'Teacher deleted successfully!')
        return redirect('teacher_list')
    return render(request, 'teachers/teacher_confirm_delete.html', {'teacher': teacher})


@login_required
@user_passes_test(is_staff_user)
def teacher_list(request):
    teachers = Teacher.objects.all()
    return render(request, 'teachers/teacher_list.html', {'teachers': teachers})



@login_required
@user_passes_test(is_staff_user)
def create_staff(request):
    if request.method == 'POST':
        form = StaffForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('staff_list')
    else:
        form = StaffForm()
    return render(request, 'staff/create_staff.html', {'form': form})


@login_required
@user_passes_test(is_staff_user)
def staff_list(request):
    staff_members = Staff.objects.all()
    return render(request, 'staff/staff_list.html', {'staff_members': staff_members})


@login_required
@user_passes_test(is_staff_user)
def staff_detail(request, pk):
    staff_member = get_object_or_404(Staff, pk=pk)
    return render(request, 'staff/staff_detail.html', {'staff_member': staff_member})


@login_required
@user_passes_test(is_staff_user)
def update_staff(request, pk):
    staff_member = get_object_or_404(Staff, pk=pk)
    if request.method == 'POST':
        form = StaffForm(request.POST, request.FILES, instance=staff_member)
        if form.is_valid():
            form.save()
            return redirect('staff_list')
    else:
        form = StaffForm(instance=staff_member)
    return render(request, 'staff/update_staff.html', {'form': form})


@login_required
@user_passes_test(is_staff_user)
def delete_staff(request, pk):
    staff_member = get_object_or_404(Staff, pk=pk)
    if request.method == 'POST':
        staff_member.delete()
        return redirect('staff_list')
    return render(request, 'staff/delete_staff.html', {'staff_member': staff_member})




@login_required
@user_passes_test(is_staff_user)
def create_nonstaff(request):
    if request.method == 'POST':
        form = NonStaffForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('nonstaff_list')
    else:
        form = NonStaffForm()
    return render(request, 'nonstaff/create_nonstaff.html', {'form': form})


@login_required
@user_passes_test(is_staff_user)
def nonstaff_list(request):
    nonstaff_members = NonStaff.objects.all()
    return render(request, 'nonstaff/nonstaff_list.html', {'nonstaff_members': nonstaff_members})


@login_required
@user_passes_test(is_staff_user)
def nonstaff_detail(request, pk):
    nonstaff_member = get_object_or_404(NonStaff, pk=pk)
    return render(request, 'nonstaff/nonstaff_detail.html', {'nonstaff_member': nonstaff_member})


@login_required
@user_passes_test(is_staff_user)
def update_nonstaff(request, pk):
    nonstaff_member = get_object_or_404(NonStaff, pk=pk)
    if request.method == 'POST':
        form = NonStaffForm(request.POST, request.FILES, instance=nonstaff_member)
        if form.is_valid():
            form.save()
            return redirect('nonstaff_list')
    else:
        form = NonStaffForm(instance=nonstaff_member)
    return render(request, 'nonstaff/update_nonstaff.html', {'form': form})


@login_required
@user_passes_test(is_staff_user)
def delete_nonstaff(request, pk):
    nonstaff_member = get_object_or_404(NonStaff, pk=pk)
    if request.method == 'POST':
        nonstaff_member.delete()
        return redirect('nonstaff_list')
    return render(request, 'nonstaff/delete_nonstaff.html', {'nonstaff_member': nonstaff_member})




@login_required
@user_passes_test(is_staff_user)
def create_intern(request):
    if request.method == 'POST':
        form = InternForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('intern_list')
    else:
        form = InternForm()
    return render(request, 'intern/create_intern.html', {'form': form})


@login_required
@user_passes_test(is_staff_user)
def intern_list(request):
    interns = Intern.objects.all()
    return render(request, 'intern/intern_list.html', {'interns': interns})

@login_required
@user_passes_test(is_staff_user)
def intern_detail(request, pk):
    intern = get_object_or_404(Intern, pk=pk)
    return render(request, 'intern/intern_detail.html', {'intern': intern})


@login_required
@user_passes_test(is_staff_user)
def update_intern(request, pk):
    intern = get_object_or_404(Intern, pk=pk)
    if request.method == 'POST':
        form = InternForm(request.POST, request.FILES, instance=intern)
        if form.is_valid():
            form.save()
            return redirect('intern_list')
    else:
        form = InternForm(instance=intern)
    return render(request, 'intern/update_intern.html', {'form': form})



@login_required
@user_passes_test(is_staff_user)
def delete_intern(request, pk):
    intern = get_object_or_404(Intern, pk=pk)
    if request.method == 'POST':
        intern.delete()
        return redirect('intern_list')
    return render(request, 'intern/delete_intern.html', {'intern': intern})



# views.py
from django.shortcuts import render
from django.contrib import messages
from .models import Student, CAT, Term
from django.db.models import Avg
@login_required

def student_results(request):
    if request.method == 'POST':
        admission_number = request.POST.get('admission_number')
        year = request.POST.get('year')
        term_name = request.POST.get('term')
        
        try:
            # Get the student
            student = Student.objects.get(admission_number=admission_number)
            
            # Get the term
            term = Term.objects.get(name=term_name, year=year)
            
            # Get all CAT results for this student in the specified term
            results = CAT.objects.filter(
                student=student,
                term=term
            ).select_related('subject')  # Optimize query by including subject data
            
            if not results.exists():
                messages.error(request, "No results found for the specified term.")
                return render(request, 'results/student_results_form.html')
            
            # Calculate overall average and total grade points
            overall_average = results.aggregate(Avg('end_term'))['end_term__avg']
            total_grade_points = sum(result.grade_points for result in results)
            gpa = total_grade_points / len(results) if results else 0
            
            # Prepare context for template
            context = {
                'student': student,
                'results': results,
                'term': term,
                'overall_average': round(overall_average, 2) if overall_average else 0,
                'gpa': round(gpa, 2),
                'show_results': True
            }
            
            return render(request, 'results/student_results_form.html', context)
            
        except Student.DoesNotExist:
            messages.error(request, "Student with this admission number does not exist.")
        except Term.DoesNotExist:
            messages.error(request, "Invalid term or year selected.")
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
    
    return render(request, 'results/student_results_form.html')


#admin dashboard
import json
from django.contrib import messages as flash_messages
@login_required
@user_passes_test(is_staff_user)

def admin_dashboard(request):
    # Get student counts grouped by year
    yearly_data = Student.objects.annotate(year=ExtractYear('admission_date'))\
        .values('year')\
        .annotate(count=Count('id'))\
        .order_by('year')
    
    # Prepare data for the chart
    years = []
    counts = []
    cumulative_counts = []
    running_total = 0
    
    for data in yearly_data:
        if data['year']:  # Ensure year is not None
            years.append(data['year'])  # Store only the year
            counts.append(data['count'])
            running_total += data['count']
            cumulative_counts.append(running_total)
    
    # Calculate year-over-year growth
    growth_rates = []
    for i in range(1, len(counts)):
        if counts[i-1] > 0:
            growth = ((counts[i] - counts[i-1]) / counts[i-1]) * 100
            growth_rates.append(round(growth, 1))
        else:
            growth_rates.append(0)
    growth_rates.insert(0, 0)  # No growth rate for first year


    # Get counts
    active_student_count = Student.objects.filter(is_active=True).count()
    student_count = Student.objects.count()
    teacher_count = Teacher.objects.count()
    staff_count = Staff.objects.count()
    nonstaff_count = NonStaff.objects.count()
    recent_activities = Activity.objects.order_by('-timestamp')[:6]
    news_updates = NewsUpdate.objects.all().order_by('-published_date')[:12]

    students = Student.objects.all() # dispalying list of all students in html using for loop
    teachers = Teacher.objects.all()[:6] # displaying 6 taechers in the database
    
    # Prepare data for chart
    chart_data = [
        {'name': 'Students', 'count': student_count, 'color': '#2563eb'},
        {'name': 'Teachers', 'count': teacher_count, 'color': '#16a34a'},
        {'name': 'Staff', 'count': staff_count, 'color': '#dc2626'},
        {'name': 'Non-Staff', 'count': nonstaff_count, 'color': '#ca8a04'}
    ]
    #donut graph for analysis of user type
    # Prepare the data for the chart
    personnel_data = [
        {'name': 'Students', 'value': Student.objects.count()},
        {'name': 'Teachers', 'value': Teacher.objects.count()},
        {'name': 'Staff', 'value': Staff.objects.count()},
        {'name': 'Non-Staff', 'value': NonStaff.objects.count()},
        {'name': 'Interns', 'value': Intern.objects.count()},
    ]

    # Get student counts by admission year
    yearly_students = Student.objects.filter(
        admission_date__isnull=False
    ).annotate(
        year=ExtractYear('admission_date')
    ).values('year').annotate(
        count=Count('id')
    ).order_by('year')

    student_yearly_data = [
        {'name': str(entry['year']), 'value': entry['count']}
        for entry in yearly_students
    ]
    
    context = {
        'students':students,
        'teachers': teachers,
        'recent_activities':recent_activities,
        'news_updates': news_updates,
        'student_count': student_count,
        'teacher_count': teacher_count,
        'staff_count': staff_count,
        'nonstaff_count': nonstaff_count,
        'chart_data': json.dumps(chart_data),

        'data': json.dumps(personnel_data),
        'student_yearly_data': json.dumps(student_yearly_data),

        'years': json.dumps(years),  # Years as integers (2020, 2021, etc.)
        'counts': json.dumps(counts),
        'cumulative_counts': json.dumps(cumulative_counts),
        'growth_rates': json.dumps(growth_rates),
        'total_students': sum(counts),
        'latest_year_count': counts[-1] if counts else 0,
        'yearly_data': yearly_data,
        'active_student_count': active_student_count,
    }
    
    return render(request, 'dashboard/admin_dashboard.html', context)


@login_required
def profile_detail(request):
    try:
        # Get or create the user's profile
        profile, created = Profile.objects.get_or_create(user=request.user)
    except Profile.DoesNotExist:
        profile = None

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()  # Save the form with the new image
            return redirect('profile_detail')
    else:
        form = ProfileForm(instance=profile)

    return render(request, 'auth/profile_detail.html', {
        'profile': profile,
        'form': form,
    })


@login_required
def create_profile(request):
    # Check if the logged-in user already has a profile
    if hasattr(request.user, 'profile'):
        return redirect('profile_detail')  # If the user already has a profile, redirect to profile detail

    # Handle the form submission
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user  # Associate the profile with the logged-in user
            profile.save()
            return redirect('profile_detail')  # Redirect to profile detail after saving

    else:
        form = ProfileForm()

    return render(request, 'auth/create_profile.html', {'form': form})


@login_required
def edit_profile(request):
    # Get the user's profile
    profile = Profile.objects.get(user=request.user)

    if request.method == 'POST':
        # Bind the form to the POST data
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            # Save the updated profile
            form.save()
            return redirect('profile_detail')  # Redirect to the profile page after saving
    else:
        # Create an empty form bound to the current profile
        form = ProfileForm(instance=profile)

    return render(request, 'auth/edit_profile.html', {'form': form})


@login_required
def news_edit(request, pk):
    news = get_object_or_404(NewsUpdate, pk=pk)

    # Ensure only the creator can edit
    if news.created_by != request.user:
        return redirect('dashboard')  # Redirect to a suitable page, e.g., the home page

    if request.method == 'POST':
        form = NewsUpdateForm(request.POST, request.FILES, instance=news)
        if form.is_valid():
            form.save()
            return redirect('admin_dashboard')  # Redirect to a suitable page after editing
    else:
        form = NewsUpdateForm(instance=news)

    return render(request, 'news/news_edit.html', {'form': form})


@login_required
def news_delete(request, pk):
    news = get_object_or_404(NewsUpdate, pk=pk)

    # Ensure only the creator can delete
    if news.created_by != request.user:
        return HttpResponseForbidden("You are not allowed to delete this news item.")

    if request.method == 'POST':  # Confirm deletion via POST request
        news.delete()
        return redirect('dashbaord')  # Redirect to a suitable page after deletion

    return render(request, 'news/news_confirm_delete.html', {'news': news})





#messaging

@login_required
def send_message(request, username):
    receiver = get_object_or_404(User, username=username)
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:  # Ensure the content is not empty
            Message.objects.create(sender=request.user, receiver=receiver, content=content)
        return redirect('message_thread', username=username)

    return render(request, 'message/send_message.html', {'receiver': receiver})

@login_required
def message_thread(request, username):
    receiver = get_object_or_404(User, username=username)
    messages = Message.objects.filter(sender=request.user, receiver=receiver) | \
               Message.objects.filter(sender=receiver, receiver=request.user)
    messages = messages.order_by('timestamp')

    return render(request, 'message/message_thread.html', {'receiver': receiver, 'messages': messages})


@login_required
def send_message(request, username):
    receiver = get_object_or_404(User, username=username)

    # Update the last seen time in the session
    request.session['last_seen'] = timezone.now().isoformat()  # Store as ISO format string
    
    if request.method == 'POST':
        form = MessageForm(request.POST, request.FILES)  # Handle file uploads
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.receiver = receiver
            message.save()
            return redirect('message_thread', username=username)
    else:
        form = MessageForm()

    # Retrieve messages between the sender and receiver
    messages = Message.objects.filter(
        sender=request.user, receiver=receiver
    ) | Message.objects.filter(
        sender=receiver, receiver=request.user
    )
    messages = messages.order_by('timestamp')

   
    # Last seen
    last_seen_str = request.session.get('last_seen')  # Retrieve the string
    last_seen = datetime.fromisoformat(last_seen_str) if last_seen_str else None

    
    return render(request, 'message/message_thread.html', {
        'receiver': receiver,
        'messages': messages,
        'last_seen': last_seen,  # Pass the datetime object
        'form': form,  # Pass the form to the template
    })


@login_required
def message_list(request):
    sent_messages = Message.objects.filter(sender=request.user).values_list('receiver', flat=True)
    received_messages = Message.objects.filter(receiver=request.user).values_list('sender', flat=True)
    
    # Combine both sender and receiver lists and eliminate duplicates
    user_ids = set(list(sent_messages) + list(received_messages))
    users = User.objects.filter(id__in=user_ids)
    
    return render(request, 'message/message_list.html', {
        'users': users
    })


@login_required
def create_chat(request, username):
    receiver = get_object_or_404(User, username=username)

    # Check if a message already exists between the logged-in user and the receiver
    existing_message = Message.objects.filter(
        (Q(sender=request.user) & Q(receiver=receiver)) | 
        (Q(sender=receiver) & Q(receiver=request.user))
    ).first()

    
    return redirect('message_thread', username=username)


@login_required
def nav_bar_messages(request):
    # Fetch the latest 3 messages involving the logged-in user
    messages = Message.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user)
    ).order_by('-timestamp')[:3]  # Limit to 3 messages

    return render(request, 'base/navbar.html', {
        'messages': messages,  # Pass the messages to the context
    })



@login_required
def enroll_subjects(request):
    student = Student.objects.get(admission_number=request.user.username)

    try:
        current_term = Term.objects.get(is_current=True)
    except Term.DoesNotExist:
        messages.error(request, "Current term not set. Please contact admin.")
        return redirect('student_dashboard')
    
    # Check if student already enrolled for current term
    already_enrolled = EnrolledSubject.objects.filter(student=student, term=current_term).exists()

    form = EnrollSubjectForm()
    form.fields['term'].queryset = Term.objects.filter(id=current_term.id)
    form.fields['term'].initial = current_term

    if request.method == 'POST' and not already_enrolled:
        form = EnrollSubjectForm(request.POST)
        form.fields['term'].queryset = Term.objects.filter(id=current_term.id)
        form.fields['term'].initial = current_term
        if form.is_valid():
            subjects = form.cleaned_data['subjects']

            # Prevent duplicate enrollments
            for subject in subjects:
                EnrolledSubject.objects.get_or_create(
                    student=student,
                    term=current_term,
                    subject=subject
                )
            messages.success(request, f"Successfully enrolled for {current_term.name} {current_term.year}.")
            return redirect('student_dashboard')

    context = {
        'form': form,
        'current_term': current_term,
        'student': student,
        'already_enrolled': already_enrolled,
    }

    return render(request, 'students/enroll_subjects.html', context)





#resources and revision material  views
@login_required
def add_resource(request):
    if request.method == 'POST':
        form = ResourceForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Resource added successfully!")
            return redirect('resources_list')  # Redirect to the resource list page
        else:
            messages.error(request, "Error adding resource. Please try again.")
    else:
        form = ResourceForm()

    return render(request, 'resources/add_resource.html', {'form': form})


@login_required
def resources_list(request):
    resources = Resource.objects.filter(is_active=True).order_by('-created_at')
    return render(request, 'resources/resources_list.html', {'resources': resources})

@login_required
def resource_detail(request, resource_id):
    resource = Resource.objects.get(id=resource_id)
    resource.increment_views()  # Increment views count each time a resource is accessed
    return render(request, 'resources/resource_detail.html', {'resource': resource})

@login_required
def resource_search(request):
    query = request.GET.get('query', '')
    resources = Resource.objects.filter(title__icontains=query)

    results = []

    for resource in resources:
        # Truncate description to 20 words (you can adjust this number)
        truncated_description = strip_tags(resource.description)  # Remove any HTML tags
        words = truncated_description.split()
        if len(words) > 20:
            truncated_description = ' '.join(words[:20]) + '...'  # Add three dots if the description is too long

        results.append({
            'title': resource.title,
            'description': truncated_description,
            'url': reverse('resource_detail', args=[resource.id]),
        })

    return JsonResponse({'resources': results})


#time table views
@login_required
def timetable_list(request):
    timetables = ExamTimeTable.objects.select_related('session').all()
    return render(request, 'time_table/timetable_list.html', {'timetables': timetables})

@login_required
@user_passes_test(is_staff_user)
def create_timetable(request):
    if request.method == 'POST':
        form = ExamTimeTableForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Exam timetable created successfully.')
            return redirect('timetable_list')
    else:
        form = ExamTimeTableForm()
    return render(request, 'time_table/timetable_form.html', {'form': form})

@login_required
@user_passes_test(is_staff_user)
def update_timetable(request, pk):
    timetable = get_object_or_404(ExamTimeTable, pk=pk)
    if request.method == 'POST':
        form = ExamTimeTableForm(request.POST, request.FILES, instance=timetable)
        if form.is_valid():
            form.save()
            messages.success(request, 'Exam timetable updated successfully.')
            return redirect('timetable_list')
    else:
        form = ExamTimeTableForm(instance=timetable)
    return render(request, 'time_table/timetable_form.html', {'form': form})

@login_required
@user_passes_test(is_staff_user)
def delete_timetable(request, pk):
    timetable = get_object_or_404(ExamTimeTable, pk=pk)
    timetable.delete()
    messages.success(request, 'Exam timetable deleted successfully.')
    return redirect('timetable_list')


@login_required
def exam_timetable_detail(request, pk):
    # Get the ExamTimeTable object by its primary key (pk)
    timetable = get_object_or_404(ExamTimeTable, pk=pk)
    
    # Return the rendered template with the timetable object
    return render(request, 'time_table/exam_timetable_detail.html', {'timetable': timetable})



@login_required
def student_report_for_term(request):
    """
    View for students to self-report for the current active term.
    Only accessible to authenticated users.
    """
    # Identify student based on admission_number matching username
    try:
        student = Student.objects.get(admission_number=request.user.username)
    except Student.DoesNotExist:
        messages.error(request, "No student profile found for your account. Please contact administration.")
        return redirect('student_dashboard')
    
    # Get the current active term (where is_current=True)
    try:
        current_term = Term.objects.get(is_current=True)
    except Term.DoesNotExist:
        messages.warning(request, "No active term found. Please contact administration.")
        return redirect('student_dashboard')
    
    # Check if the student has already reported for the current term
    existing_report = TermReporting.objects.filter(
        student=student,
        term=current_term
    ).first()
    
    if request.method == 'POST':
        if existing_report:
            messages.info(request, f"You have already reported for {current_term}.")
            return redirect('student_dashboard')
        
        notes = request.POST.get('notes', '')
        
        TermReporting.objects.create(
            student=student,
            term=current_term,
            reporting_date=timezone.now().date(),
            status='REPORTED',
            notes=notes
        )
        
        messages.success(request, f"You have successfully reported for {current_term}.")
        return redirect('student_dashboard')
    
    context = {
        'student': student,
        'current_term': current_term,
        'already_reported': existing_report is not None
    }
    
    return render(request, 'students/report_for_term.html', context)


@login_required
def view_fee_structure(request):
    try:
        student = Student.objects.get(admission_number=request.user.username)
    except Student.DoesNotExist:
        messages.error(request, "No student profile found for your account.")
        return redirect('student_dashboard')

    if not student.admission_date:
        messages.error(request, "Your admission date is not set. Please contact administration.")
        return redirect('student_dashboard')

    # Filter terms from the student's admission date to the current date
    current_year = date.today().year
    terms = Term.objects.filter(year__gte=student.admission_date.year, year__lte=current_year)

    # Retrieve fee structures for the filtered terms
    fee_structures = FeeStructure.objects.filter(term__in=terms).select_related('term')

    # Identify the current term
    current_term = Term.objects.filter(is_current=True).first()

    context = {
        'student': student,
        'fee_structures': fee_structures,
        'current_term': current_term
    }


    return render(request, 'students/all_fee_structures.html', context)




@login_required
def student_teachers_view(request):
    try:
        # Fetch student based on username == admission_number
        student = Student.objects.get(admission_number=request.user.username)
    except Student.DoesNotExist:
        messages.error(request, "No student profile found for your account.")
        return redirect('student_dashboard')  # Redirect wherever your dashboard is
    
    # 1. Get all Senior Teachers
    senior_teachers = Teacher.objects.filter(position__iexact="Senior Teacher")

    # 2. Get teachers assigned to student's class
    assigned_teachers = Teacher.objects.filter(assigned_class=student.current_class)

    context = {
        'student': student,
        'senior_teachers': senior_teachers,
        'assigned_teachers': assigned_teachers,
    }

    return render(request, 'students/teachers_list.html', context)


@login_required
def current_term_events(request):
    # Get the current term
    current_term = Term.objects.filter(is_current=True).first()
    
    events = []
    if current_term:
        # Get events related to the current term
        events = Event.objects.filter(term=current_term)
    
    context = {
        'current_term': current_term,
        'events': events,
    }
    
    return render(request, 'events/current_term_events.html', context)

@login_required
@user_passes_test(is_staff_user)
def promote_students(request):
    form_order = ['Form 1', 'Form 2', 'Form 3', 'Form 4']

    if request.method == 'POST':
        classes = Class_of_study.objects.all()

        for student in Student.objects.filter(is_active=True):
            current_class = student.current_class
            if current_class:
                current_form = current_class.name
                current_stream = current_class.stream

                try:
                    current_index = form_order.index(current_form)
                except ValueError:
                    continue

                if current_index == len(form_order) - 1:
                    # Graduated
                    student.current_class = None
                    student.is_active = False
                    student.remarks = "Graduated"
                else:
                    next_form = form_order[current_index + 1]
                    try:
                        next_class = Class_of_study.objects.get(name=next_form, stream=current_stream)
                        student.current_class = next_class
                    except Class_of_study.DoesNotExist:
                        continue
                student.save()

        messages.success(request, "Students promoted successfully!")
        return redirect('students_list')  # Replace with your actual view

    return render(request, 'students/promote_students.html')