from django.core.management.base import BaseCommand
from tracker.models import Badge

class Command(BaseCommand):
    help = "Seed default badges"

    def handle(self, *args, **options):
        badges = [
            ("Navigator",     "30-day streak",            "streak",      "⚓", "streak_days",    30),
            ("Rookie Sailor", "50-day streak",            "streak",      "🌊", "streak_days",    50),
            ("Zenith Runner", "100-day streak",           "streak",      "⚡", "streak_days",   100),
            ("Legend",        "365-day streak",           "streak",      "👑", "streak_days",   365),
            ("First Step",    "Complete your first day",  "achievement", "🥇", "total_days",      1),
            ("Shield Bearer", "Use a streak shield",      "achievement", "🛡️", "shields_used",    1),
            ("Focus Master",  "25 pomodoro sessions",     "achievement", "🍅", "pomodoros",      25),
            ("Architect",     "Create 10 tasks",          "achievement", "🔧", "tasks_created",  10),
            ("Century",       "100 days total",           "achievement", "💯", "total_days",    100),
            ("Zen Mode",      "100 pomodoro sessions",    "achievement", "🧘", "pomodoros",     100),
            ("Scribe",        "Write 10 notes",           "achievement", "📝", "notes_created",  10),
        ]
        created = 0
        for name, desc, btype, icon, rtype, rval in badges:
            _, c = Badge.objects.get_or_create(
                name=name,
                defaults=dict(description=desc, badge_type=btype, icon=icon,
                              requirement_type=rtype, requirement_value=rval)
            )
            if c:
                created += 1
        self.stdout.write(self.style.SUCCESS(f"Done — {created} badges created."))
