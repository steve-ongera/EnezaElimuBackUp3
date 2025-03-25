from django.contrib import admin
from .models import *

@admin.register(EnrolledSubject)
class EnrolledSubjectAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject', 'term', 'date_enrolled')
    list_filter = ('term__year', 'term__name', 'subject')
    search_fields = ('student__name', 'student__admission_number', 'subject__name', 'term__name')

    # Optional: For ordering
    ordering = ('student', 'term__year', 'term__name', 'subject')

@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = ('term', 'amount_required')
    search_fields = ('term__name', 'term__year')
    list_filter = ('term__year',)

# Fee Payment Admin
@admin.register(FeePayment)
class FeePaymentAdmin(admin.ModelAdmin):
    list_display = ('student', 'term', 'amount_paid', 'payment_date', 'receipt_number', 'get_balance')
    search_fields = ('student__name', 'term__name', 'receipt_number')
    list_filter = ('term__year', 'payment_date')

    def get_balance(self, obj):
        return obj.balance
    get_balance.short_description = 'Balance'

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'teacher_code', 'email', 'phone', 'assigned_class')
    search_fields = ('first_name', 'last_name', 'teacher_code', 'email', 'phone')
    list_filter = ('assigned_class', 'gender', 'department')

@admin.register(ResourceCategory)
class ResourceCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'created_at', 'updated_at', 'views', 'is_active')
    list_filter = ('category', 'is_active', 'created_at')
    search_fields = ('title', 'description')
    readonly_fields = ('views', 'created_at', 'updated_at')
    ordering = ('-created_at',)

@admin.register(ExaminationSession)
class ExaminationSessionAdmin(admin.ModelAdmin):
    list_display = ('year', 'start_date', 'end_date')
    list_filter = ('year',)
    search_fields = ('year',)

@admin.register(ExamTimeTable)
class ExamTimeTableAdmin(admin.ModelAdmin):
    list_display = ('name', 'session', 'start_date', 'end_date')
    list_filter = ('session__year',)
    search_fields = ('name', 'session__year')

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'term', 'date')  # Columns to display in the list
    list_filter = ('term', 'date')            # Add filters by term and date
    search_fields = ('title', 'description')  # Add search functionality
    ordering = ('-date',)      

    

@admin.register(TermReporting)
class TermReportingAdmin(admin.ModelAdmin):
    list_display = ('student', 'term', 'reporting_date', 'status')
    list_filter = ('term', 'status', 'reporting_date')
    search_fields = ('student__name', 'student__admission_number', 'notes')
    date_hierarchy = 'reporting_date'
    
    # Actions for bulk updates
    actions = ['mark_as_reported', 'mark_as_absent', 'mark_as_late']
    
    def mark_as_reported(self, request, queryset):
        queryset.update(status='REPORTED')
    mark_as_reported.short_description = "Mark selected students as reported"
    
    def mark_as_absent(self, request, queryset):
        queryset.update(status='ABSENT')
    mark_as_absent.short_description = "Mark selected students as absent"
    
    def mark_as_late(self, request, queryset):
        queryset.update(status='LATE')
    mark_as_late.short_description = "Mark selected students as late"

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('name', 'admission_number', 'current_class', 'is_active', 'admission_date')
    list_filter = ('is_active', 'current_class')
    
from django.contrib import admin
from django import forms
from .models import CAT, Student, Subject, Term, Class_of_study

# Custom form for CATAdmin
class CATForm(forms.ModelForm):
    class Meta:
        model = CAT
        fields = '__all__'
        widgets = {
            'cat1': forms.NumberInput(attrs={'size': '4', 'style': 'width: 60px; text-align:center;'}),
            'cat2': forms.NumberInput(attrs={'size': '4', 'style': 'width: 60px; text-align:center;'}),
            'cat3': forms.NumberInput(attrs={'size': '4', 'style': 'width: 60px; text-align:center;'}),
            'student': forms.Select(attrs={'style': 'width: 250px;'}),
            'subject': forms.Select(attrs={'style': 'width: 180px;'}),
            'term': forms.Select(attrs={'style': 'width: 150px;'}),
        }

from django.utils.html import format_html
from .models import CAT, Student, Subject, Term, Class_of_study

@admin.register(CAT)
class CATAdmin(admin.ModelAdmin):
    list_display = (
        'student', 'subject', 'term', 'class_of_study',
        'formatted_cat1', 'formatted_cat2', 'formatted_cat3', 
        'formatted_end_term', 'formatted_grade_points', 
        'letter_grade', 
    )
    list_filter = ('class_of_study', 'term', 'subject', 'letter_grade', 'position')
    search_fields = ('student__name', 'student__admission_number', 'subject__name', 'term__name')
    readonly_fields = ('end_term', 'grade_points', 'letter_grade', 'position')
    

    fieldsets = (
        ('Student & Class Info', {
            'fields': ('student', 'class_of_study', 'subject', 'term')
        }),
        ('CAT Scores', {
            'fields': ('cat1', 'cat2', 'cat3')
        }),
        ('Result Summary (Auto Calculated)', {
            'fields': ('end_term', 'grade_points', 'letter_grade', 'position')
        }),
    )

    # Custom methods to format float fields to 2 decimal places:
    def formatted_cat1(self, obj):
        return f"{obj.cat1:.2f}"
    formatted_cat1.short_description = 'CAT 1'

    def formatted_cat2(self, obj):
        return f"{obj.cat2:.2f}"
    formatted_cat2.short_description = 'CAT 2'

    def formatted_cat3(self, obj):
        return f"{obj.cat3:.2f}"
    formatted_cat3.short_description = 'CAT 3'

    def formatted_end_term(self, obj):
        return f"{obj.end_term:.2f}"
    formatted_end_term.short_description = 'End Term'

    def formatted_grade_points(self, obj):
        return f"{obj.grade_points:.2f}"
    formatted_grade_points.short_description = 'Grade Points'


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = (
        'title', 
        'subject', 
        'class_of_study', 
        'term', 
        'collection_date', 
        'is_submitted'
    )
    
    list_filter = (
        'is_submitted', 
        'subject', 
        'class_of_study', 
        'term'
    )
    
    search_fields = (
        'title', 
        'description'
    )

admin.site.register(Class_of_study)
admin.site.register(Subject)
admin.site.register(Term)



admin.site.register(Staff)
admin.site.register(NonStaff)
admin.site.register(Intern)
admin.site.register(Department)

admin.site.register(Profile)
admin.site.register(Activity)
admin.site.register(Message)
admin.site.register(NewsUpdate)