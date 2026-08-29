from django.urls import path
from . import views

app_name = "tracker"

urlpatterns = [
    path("",              views.home,             name="home"),
    path("today/",        views.today_view,        name="today"),
    path("tasks/",        views.tasks_view,        name="tasks"),
    path("weekly/",       views.weekly_tasks_view, name="weekly_tasks"),
    path("history/",      views.history_view,      name="history"),
    path("notes/",        views.notes_view,        name="notes"),
    path("notes/<int:note_id>/edit/", views.note_edit_view, name="note_edit"),
    path("profile/",      views.profile_view,      name="profile"),
    # JSON APIs
    path("api/task/complete/",    views.api_complete_task,    name="api_complete"),
    path("api/weekly/complete/",  views.api_complete_weekly,  name="api_weekly_complete"),
    path("api/range/complete/",   views.api_complete_range,   name="api_range_complete"),
    path("api/pomodoro/log/",     views.api_log_pomodoro,     name="api_pomodoro"),
    path("api/shield/use/",       views.api_use_shield,       name="api_shield"),
    path("api/task/delete/",      views.api_delete_task,      name="api_delete"),
    path("api/range/delete/",     views.api_delete_range,     name="api_range_delete"),
    path("api/home/stats/",       views.api_home_stats,       name="api_home_stats"),
]
