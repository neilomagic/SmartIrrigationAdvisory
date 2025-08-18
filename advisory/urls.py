from django.urls import path

from . import views

app_name = 'advisory'

urlpatterns = [
    # Dashboard (new)
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # Analytics URLs (new)
    path('analytics/system/', views.system_analytics_view, name='system_analytics'),
    path('analytics/field/<int:field_id>/',
         views.field_analytics_view, name='field_analytics'),
    path('analytics/api/<int:field_id>/',
         views.analytics_api_view, name='analytics_api'),
    path('analytics/compare/', views.performance_comparison_view,
         name='performance_comparison'),

    # Existing URLs
    path('', views.dashboard_view, name='dashboard'),
    path('create/', views.create_field_view, name='create_field'),
    path('field/<int:field_id>/advice/',
         views.get_irrigation_advice, name='get_advice'),
    path('fields/', views.FieldListView.as_view(), name='field_list'),
    path('field/<int:field_id>/history/',
         views.advisory_history_view, name='advisory_history'),
    path('field/<int:field_id>/map/', views.field_map_view, name='field_map')
]
