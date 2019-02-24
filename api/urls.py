from django.urls import path

from . import views

urlpatterns = [
    path('send', views.send),
    path('endpoint', views.endpoint),
    path('departments', views.departments),
    path('bases', views.bases),
    path('researches/templates', views.ResearchesTemplates.as_view()),
    path('researches/all', views.Researches.as_view()),
    path('researches/by-department', views.researches_by_department),
    path('researches/params', views.researches_params),
    path('researches/update', views.researches_update),
    path('researches/details', views.researches_details),
    path('researches/paraclinic_details', views.paraclinic_details),
    path('current-user-info', views.current_user_info),
    path('directive-from', views.directive_from),
    path('patients/search-card', views.patients_search_card),
    path('patients/search-individual', views.patients_search_individual),
    path('patients/search-l2-card', views.patients_search_l2_card),
    path('patients/card/<int:card_id>', views.patients_get_card_data),
    path('directions/generate', views.directions_generate),
    path('directions/rmis-directions', views.directions_rmis_directions),
    path('directions/rmis-direction', views.directions_rmis_direction),
    path('directions/history', views.directions_history),
    path('directions/cancel', views.directions_cancel),
    path('directions/results', views.directions_results),
    path('directions/services', views.directions_services),
    path('directions/mark-visit', views.directions_mark_visit),
    path('directions/visit-journal', views.directions_visit_journal),
    path('directions/last-result', views.directions_last_result),
    path('directions/results-report', views.directions_results_report),
    path('directions/paraclinic_form', views.directions_paraclinic_form),
    path('directions/paraclinic_result', views.directions_paraclinic_result),
    path('directions/paraclinic_result_confirm', views.directions_paraclinic_confirm),
    path('directions/paraclinic_result_confirm_reset', views.directions_paraclinic_confirm_reset),
    path('directions/paraclinic_result_history', views.directions_paraclinic_history),
    path('statistics-tickets/types', views.statistics_tickets_types),
    path('statistics-tickets/send', views.statistics_tickets_send),
    path('statistics-tickets/get', views.statistics_tickets_get),
    path('statistics-tickets/invalidate', views.statistics_tickets_invalidate),
    path('mkb10', views.mkb10),
    path('vich_code', views.vich_code),
    path('flg', views.flg),
    path('search-template', views.search_template),
    path('load-templates', views.load_templates),
    path('get-template', views.get_template),
    path('templates/update', views.update_template),
    path('modules', views.modules_view),
]
