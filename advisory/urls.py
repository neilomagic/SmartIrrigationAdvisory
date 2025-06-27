from django.urls import path

from . import views

app_name = 'advisory'

urlpatterns = [

    path('', views.create_field_view, name='create_field'),

    path('create/', views.create_field_view, name='create_field'),
    path('field/<int:field_id>/advice/',
         views.get_irrigation_advice, name='get_advice'),
    path('fields/', views.FieldListView.as_view(), name='field_list'),
    path('field/<int:field_id>/history/',
         views.advisory_history_view, name='advisory_history'),

    path('field/<int:field_id>/map/', views.field_map_view, name='field_map')



]
