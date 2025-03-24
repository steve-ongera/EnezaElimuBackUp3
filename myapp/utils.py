from django.conf import settings
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
import os
from io import BytesIO
from datetime import datetime
from django.utils.text import slugify

def link_callback(uri, rel):
    """
    Convert HTML URIs to absolute system paths so xhtml2pdf can access those resources
    """
    # Use the static folder
    static_url = settings.STATIC_URL
    static_root = settings.STATIC_ROOT
    media_url = settings.MEDIA_URL
    media_root = settings.MEDIA_ROOT

    # Make sure that file exists
    if uri.startswith(media_url):
        path = os.path.join(media_root, uri.replace(media_url, ""))
    elif uri.startswith(static_url):
        path = os.path.join(static_root, uri.replace(static_url, ""))
    else:
        return uri

    # Make sure that file exists
    if not os.path.isfile(path):
        raise Exception(
            'media URI must start with %s or %s' % (static_url, media_url)
        )
    return path

def render_to_pdf(template_src, context_dict={}):
    """
    Function to generate PDF from HTML template
    """
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result, link_callback=link_callback)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None

def generate_term_report_pdf(student, term_data):
    """
    Generate a PDF report for a specific term
    """
    context = {
        'student': student,
        'term_data': term_data,
        'school_name': settings.SCHOOL_NAME,
        'school_logo': settings.SCHOOL_LOGO_PATH,
        'generated_date': datetime.now().strftime("%d-%m-%Y"),
        'principal_name': settings.PRINCIPAL_NAME,
        'is_term_report': True
    }
    
    pdf = render_to_pdf('marks/pdf_reports/term_report_template.html', context)
    if pdf:
        filename = f"{slugify(student.name)}_{term_data['term'].name}_{term_data['term'].year}_report.pdf"
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    return HttpResponse("Error generating PDF", status=400)
def generate_year_report_pdf(student, year, year_data):
    """
    Generate a PDF report for an entire academic year
    """
    # Calculate yearly averages and summaries
    subjects_total_scores = {}
    subjects_count = {}
    
    # Extract term data for the specified year
    term_data_list = []
    for data in year_data:
        term_data_list.append(data)
        for subject in data['subjects']:
            # Check if the average value is a number and not 'N/A'
            if subject['average'] != 'N/A' and isinstance(subject['average'], (int, float)) and subject['average'] > 0:
                subject_name = subject['subject'].name if hasattr(subject['subject'], 'name') else str(subject['subject'])
                
                # Initialize if not already in our dictionaries
                if subject_name not in subjects_total_scores:
                    subjects_total_scores[subject_name] = 0
                    subjects_count[subject_name] = 0
                
                # Add this term's score to the total
                subjects_total_scores[subject_name] += subject['average']
                subjects_count[subject_name] += 1
    
    # Calculate overall average from subject averages
    total_year_score = 0
    valid_subjects = 0
    
    for subject_name, total_score in subjects_total_scores.items():
        count = subjects_count[subject_name]
        if count > 0:
            subject_average = total_score / count
            total_year_score += subject_average
            valid_subjects += 1
    
    # Calculate year average
    year_average = round(total_year_score / max(1, valid_subjects), 2)
    
    # Determine year grade and position
    year_grade, year_position = get_grade_and_position(year_average)
    
    context = {
        'student': student,
        'year': year,
        'term_data_list': term_data_list,
        'year_average': year_average,
        'overall_grade': year_grade,
        'position': year_position,
        'school_name': settings.SCHOOL_NAME,
        'school_logo': settings.SCHOOL_LOGO_PATH,
        'generated_date': datetime.now().strftime("%d-%m-%Y"),
        'principal_name': settings.PRINCIPAL_NAME,
        'is_year_report': True
    }
    
    pdf = render_to_pdf('marks/pdf_reports/year_report_template.html', context)
    if pdf:
        filename = f"{slugify(student.name)}_{year}_annual_report.pdf"
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    return HttpResponse("Error generating PDF", status=400)

def generate_term_report_pdf(student, term_data):
    """
    Generate a PDF report for a specific term
    """
    if not term_data:
        return HttpResponse("No data available for this term", status=404)
    
    # Recalculate term average to ensure it's based on the correct subject data
    total_score = 0
    valid_subjects = 0
    
    for subject in term_data['subjects']:
        if subject['average'] != 'N/A' and isinstance(subject['average'], (int, float)) and subject['average'] > 0:
            total_score += subject['average']
            valid_subjects += 1
    
    term_average = round(total_score / max(1, valid_subjects), 2)
    overall_grade, position = get_grade_and_position(term_average)
    
    # Update term data with corrected calculations
    updated_term_data = term_data.copy()
    updated_term_data['term_average'] = term_average
    updated_term_data['overall_grade'] = overall_grade
    updated_term_data['position'] = position
    
    # Update each subject's grade and position using the corrected average
    for subject in updated_term_data['subjects']:
        if subject['average'] != 'N/A' and isinstance(subject['average'], (int, float)):
            subject['grade'] = get_letter_grade(subject['average'])
            subject['grade_points'] = get_grade_points(subject['average'])
            # Set position based on the grade
            _, subject['position'] = get_grade_and_position(subject['average'])
    
    context = {
        'student': student,
        'term_data': updated_term_data,
        'school_name': settings.SCHOOL_NAME,
        'school_logo': settings.SCHOOL_LOGO_PATH,
        'generated_date': datetime.now().strftime("%d-%m-%Y"),
        'principal_name': settings.PRINCIPAL_NAME,
        'is_year_report': False
    }
    
    pdf = render_to_pdf('marks/pdf_reports/term_report_template.html', context)
    if pdf:
        term = term_data['term']
        filename = f"{slugify(student.name)}_{term.year}_{term.name}_report.pdf"
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    return HttpResponse("Error generating PDF", status=400)

def get_grade_and_position(average):
    """
    Helper function to determine grade and position based on average score
    """
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

def get_term_data(progress_data, year, term_name):
    """
    Helper function to extract term data for a specific year and term
    """
    for term_data in progress_data:
        if term_data['term'].year == year and term_data['term'].name == term_name:
            return term_data
    return None

def get_year_data(progress_data, year):
    """
    Helper function to extract all term data for a specific year
    """
    year_data = []
    for term_data in progress_data:
        if term_data['term'].year == year:
            year_data.append(term_data)
    return year_data

def get_letter_grade(score):
    """
    Helper function to get letter grade based on score
    """
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
    """
    Helper function to get grade points based on score
    """
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