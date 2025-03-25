from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('general_student_list', views.general_student_list, name='general_student_list'),
    path('student/<int:student_id>/term/<int:term_id>/', views.student_marks, name='student_marks'),
    path('student/<int:student_id>/progress/', views.student_progress, name='student_progress'),
    path('promote-students/', views.promote_students, name='promote_students'),
    
    #urls for all classes / Streams 
    path('classes_lists/', views.class_lists, name='class_lists'),
    path('classes/<int:class_id>/terms/', views.term_list, name='term_list'),
    path('classes/<int:class_id>/terms/<int:term_id>/students/',  views.student_list, name='student_list'),


    # urls.py
    path('classes/<int:class_id>/terms/<int:term_id>/analysis/', views.subject_analysis, name='subject_analysis'),
    path('register/', views.register, name='register'),
    path('', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/<uidb64>/<token>/', views.reset_password, name='reset_password'),
    
    path('student_dashboard/', views.student_dashboard, name='student_dashboard'),
    path('report-for-term/', views.student_report_for_term, name='report_for_term'),
    path('student/teachers/', views.student_teachers_view, name='student_teachers'),
    path('fees/', views.view_fee_structure, name='view_all_fee_structures'),
    path('events/current-term/', views.current_term_events, name='current_term_events'),
    path('individual_student_progress/' , views.individual_student_progress , name='individual_student_progress'),
    path('student/<int:student_id>/year-report/<int:year>/', views.download_year_report, name='download_year_report'),
    path('student/<int:student_id>/term-report/<int:term_id>/', views.download_term_report, name='download_term_report'),
    path('student/enroll-subjects/', views.enroll_subjects, name='enroll_subjects'),



    path('student_profile/', views.student_profile, name='student_profile'),
    path('student_profile/edit/', views.edit_student_profile, name='edit_student_profile'),
    path('profile_detail/', views.profile_detail, name='profile_detail'),# admin profile view
    path('create-profile/', views.create_profile, name='create_profile'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),#admin profile edits

    #classs list view
    path('class_lists/', views.class_list, name='class_list'),
    path('create/', views.class_create, name='class_create'),
    path('<int:pk>/', views.class_detail, name='class_detail'),
    path('<int:pk>/update/', views.class_update, name='class_update'),
    path('<int:pk>/delete/', views.class_delete, name='class_delete'),

    #subject list views
    path('subjects/', views.subject_list, name='subject_list'),
    path('subjects/create/', views.subject_create, name='subject_create'),
    path('subjects/<int:pk>/', views.subject_detail, name='subject_detail'),
    path('subjects/<int:pk>/update/', views.subject_update, name='subject_update'),
    path('subjects/<int:pk>/delete/', views.subject_delete, name='subject_delete'),

    #students
    path('database_students_list/', views.database_students_list, name='database_students_list'),
    path('students/create/', views.student_create, name='student_create'),
    path('students/<int:pk>/', views.student_detail, name='student_detail'),
    path('students/<int:pk>/update/', views.student_update, name='student_update'),
    path('students/<int:pk>/delete/', views.student_delete, name='student_delete'),

    #terms
    path('terms/', views.term_lists, name='term_lists'),
    path('terms/create/', views.term_create, name='term_create'),
    path('terms/<int:pk>/', views.term_detail, name='term_detail'),
    path('terms/<int:pk>/update/', views.term_update, name='term_update'),
    path('terms/<int:pk>/delete/', views.term_delete, name='term_delete'),

    #cats
    path('cats/', views.cat_list, name='cat_list'),
    path('cats/create/', views.cat_create, name='cat_create'),
    path('ajax/student-search/', views.student_search, name='student_search'),
    path('get_class_of_study/', views.get_class_of_study, name='get_class_of_study'),
    path('cats/<int:pk>/', views.cat_detail, name='cat_detail'),
    path('cats/<int:pk>/update/', views.cat_update, name='cat_update'),
    path('cats/<int:pk>/delete/', views.cat_delete, name='cat_delete'),

    #graphs
    path('population-graph/', views.student_population_graph, name='population-graph'),
    path('class-distribution/', views.class_distribution_view, name='class-distribution'),
    #search
    path("search-student/", views.search_student, name="search_student"),
    path('student-results/', views.student_results, name='student_results'),
    #rankings
    path('rankings/', views.student_rankings, name='student_rankings'),
    path('rankings/form/', views.form_rankings, name='form_rankings'),
    path('stream-performance/', views.stream_performance, name='stream_performance'),
    path('subject-performance/', views.subject_performance, name='subject_performance'),
    #path('rankings/pdf_download/', views.rankings_pdf_download, name='rankings_pdf_download'),

    path('teachers/', views.teacher_list, name='teacher_list'),
    path('teachers/create/', views.teacher_create, name='teacher_create'),
    path('teachers/<int:teacher_id>/', views.teacher_detail, name='teacher_detail'),
    path('teachers/<int:teacher_id>/edit/', views.teacher_edit, name='teacher_edit'),
    path('teachers/<int:teacher_id>/delete/', views.teacher_delete, name='teacher_delete'),

    path('staff/create/', views.create_staff, name='create_staff'),
    path('staff/', views.staff_list, name='staff_list'),
    path('staff/<int:pk>/', views.staff_detail, name='staff_detail'),
    path('staff/update/<int:pk>/', views.update_staff, name='update_staff'),
    path('staff/delete/<int:pk>/', views.delete_staff, name='delete_staff'),

    path('nonstaff/create/', views.create_nonstaff, name='create_nonstaff'),
    path('nonstaff/', views.nonstaff_list, name='nonstaff_list'),
    path('nonstaff/<int:pk>/', views.nonstaff_detail, name='nonstaff_detail'),
    path('nonstaff/update/<int:pk>/', views.update_nonstaff, name='update_nonstaff'),
    path('nonstaff/delete/<int:pk>/', views.delete_nonstaff, name='delete_nonstaff'),

    path('intern/create/', views.create_intern, name='create_intern'),
    path('intern/', views.intern_list, name='intern_list'),
    path('intern/<int:pk>/', views.intern_detail, name='intern_detail'),
    path('intern/update/<int:pk>/', views.update_intern, name='update_intern'),
    path('intern/delete/<int:pk>/', views.delete_intern, name='delete_intern'),
    
    path('help-and-support/', views.help_and_support, name='help_and_support'),
    path('system-settings/', views.system_settings, name='system_settings'),

    path('news/<int:pk>/edit/', views.news_edit, name='news_edit'),
    path('news/<int:pk>/delete/', views.news_delete, name='news_delete'),

    path('messages/<str:username>/', views.send_message, name='message_thread'),
    path('messages/', views.message_list, name='message_list'),
    path('messages/create/<str:username>/', views.create_chat, name='create_chat'),




    #resources and assignment  views
    path('resources/add/', views.add_resource, name='add_resource'),
    path('resources/', views.resources_list, name='resources_list'),
    path('resources/<int:resource_id>/', views.resource_detail, name='resource_detail'),
    path('resource-search/', views.resource_search, name='resource_search'),
    path('assignments/', views.assignment_list, name='assignment_list'),
    path('assignments/create/', views.create_assignment, name='create_assignment'),

    #timetable
    path('timetable/', views.timetable_list, name='timetable_list'),
    path('timetable/create/', views.create_timetable, name='create_timetable'),
    path('timetable/update/<int:pk>/', views.update_timetable, name='update_timetable'),
    path('timetable/delete/<int:pk>/', views.delete_timetable, name='delete_timetable'),
    path('exam-timetable/<int:pk>/', views.exam_timetable_detail, name='exam_timetable_detail'),
]