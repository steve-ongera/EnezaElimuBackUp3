from django import template

register = template.Library()

@register.filter
def calculate_year_average(term_list):
    """Calculate the average across all terms in a year"""
    if not term_list:
        return 0
    try:
        # Access dictionary values instead of attributes
        total = sum(float(term.get('term_average', 0)) for term in term_list)
        return round(total / len(term_list), 1)
    except (ValueError, TypeError):
        return 0

@register.filter
def calculate_grade(average):
    """Convert numerical average to letter grade"""
    try:
        avg = float(average)
        if avg >= 80:
            return 'A'
        elif avg >= 70:
            return 'B'
        elif avg >= 60:
            return 'C'
        elif avg >= 50:
            return 'D'
        else:
            return 'E'
    except (ValueError, TypeError):
        return 'N/A'