from django.contrib import admin
from .models import Task, WeeklyTask, WeeklyTaskLog, RangeTask, RangeTaskLog, DayLog, Note, Badge, UserBadge
admin.site.register(Task)
admin.site.register(WeeklyTask)
admin.site.register(WeeklyTaskLog)
admin.site.register(RangeTask)
admin.site.register(RangeTaskLog)
admin.site.register(DayLog)
admin.site.register(Note)
admin.site.register(Badge)
admin.site.register(UserBadge)
