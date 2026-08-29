from django.db import models
from django.contrib.auth.models import User

SHADE_COLORS = {
    0: "#ffffff", 1: "#cccccc", 2: "#999999",
    3: "#666666", 4: "#444444", 5: "#222222",
}

WEEKDAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


class Task(models.Model):
    """One-time task for a specific date. Long-term tasks show as overdue until done."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tasks")
    title = models.CharField(max_length=300)
    shade = models.IntegerField(default=0)
    target_date = models.DateField()
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    pomodoro_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["target_date", "created_at"]

    def shade_color(self):
        return SHADE_COLORS.get(self.shade, "#ffffff")

    def __str__(self):
        return f"{self.user.username}: {self.title} ({self.target_date})"


class WeeklyTask(models.Model):
    """Recurring task that appears on specific weekdays forever until deactivated."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="weekly_tasks")
    title = models.CharField(max_length=300)
    shade = models.IntegerField(default=0)
    # Comma-separated weekday numbers: "0,1,4" = Mon,Tue,Fri
    weekdays = models.CharField(max_length=20, default="0")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def shade_color(self):
        return SHADE_COLORS.get(self.shade, "#ffffff")

    def weekday_list(self):
        try:
            return [int(d) for d in self.weekdays.split(",") if d.strip().isdigit()]
        except Exception:
            return []

    def weekday_names(self):
        return [WEEKDAY_NAMES[d] for d in self.weekday_list() if 0 <= d <= 6]

    def __str__(self):
        return f"{self.user.username}: {self.title} [{self.weekdays}]"


class WeeklyTaskLog(models.Model):
    """Tracks daily completion of a WeeklyTask."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="weekly_logs")
    weekly_task = models.ForeignKey(WeeklyTask, on_delete=models.CASCADE, related_name="logs")
    date = models.DateField()
    is_completed = models.BooleanField(default=False)

    class Meta:
        unique_together = ["user", "weekly_task", "date"]

    def __str__(self):
        return f"{self.user.username}: {self.weekly_task.title} on {self.date}"


class DayLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="day_logs")
    date = models.DateField()
    tasks_total = models.IntegerField(default=0)
    tasks_completed = models.IntegerField(default=0)
    is_fully_completed = models.BooleanField(default=False)
    shield_used = models.BooleanField(default=False)

    class Meta:
        unique_together = ["user", "date"]
        ordering = ["-date"]

    def completion_pct(self):
        if self.tasks_total == 0:
            return 0
        return int(self.tasks_completed / self.tasks_total * 100)

    def __str__(self):
        return f"{self.user.username}: {self.date}"


class PomodoroLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="pomodoros")
    task = models.ForeignKey(Task, on_delete=models.SET_NULL, null=True, blank=True)
    duration_minutes = models.IntegerField()
    logged_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}: {self.duration_minutes}min"


class Note(models.Model):
    COLOR_CHOICES = [
        ("default", "Default"),
        ("warm",    "Warm"),
        ("cool",    "Cool"),
        ("accent",  "Accent"),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notes")
    title = models.CharField(max_length=200, blank=True)
    content = models.TextField()
    color = models.CharField(max_length=20, choices=COLOR_CHOICES, default="default")
    is_pinned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_pinned", "-updated_at"]

    def __str__(self):
        return f"{self.user.username}: {self.title or 'Untitled'}"


class Badge(models.Model):
    TYPE_CHOICES = [("streak", "Streak"), ("achievement", "Achievement")]
    REQ_CHOICES = [
        ("streak_days", "Streak Days"),
        ("total_days",  "Total Days Completed"),
        ("pomodoros",   "Total Pomodoros"),
        ("tasks_created","Tasks Created"),
        ("shields_used","Shields Used"),
        ("notes_created","Notes Created"),
    ]
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=200)
    badge_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    icon = models.CharField(max_length=10)
    requirement_type = models.CharField(max_length=50, choices=REQ_CHOICES)
    requirement_value = models.IntegerField(default=0)

    def __str__(self):
        return self.name


class UserBadge(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_badges")
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    earned_at = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = ["user", "badge"]

    def __str__(self):
        return f"{self.user.username} - {self.badge.name}"


class RangeTask(models.Model):
    """A task that spans a date range — appears every day from start to end."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="range_tasks")
    title = models.CharField(max_length=300)
    shade = models.IntegerField(default=0)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["start_date", "created_at"]

    def shade_color(self):
        return SHADE_COLORS.get(self.shade, "#ffffff")

    def duration_days(self):
        return (self.end_date - self.start_date).days + 1

    def __str__(self):
        return f"{self.user.username}: {self.title} ({self.start_date} → {self.end_date})"


class RangeTaskLog(models.Model):
    """Tracks daily completion of a RangeTask."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="range_logs")
    range_task = models.ForeignKey(RangeTask, on_delete=models.CASCADE, related_name="logs")
    date = models.DateField()
    is_completed = models.BooleanField(default=False)

    class Meta:
        unique_together = [["user", "range_task", "date"]]

    def __str__(self):
        return f"{self.user.username}: {self.range_task.title} on {self.date}"