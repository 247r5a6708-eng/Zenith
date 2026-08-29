import random
import hashlib
from datetime import date, timedelta
from django.utils import timezone


# ── Daily quote (deterministic per calendar date) ─────────────────────────────
QUOTES = [
    "The summit is what drives us, but the climb itself is what matters.",
    "Discipline is the bridge between goals and accomplishment.",
    "Every day is a new page — make it worth reading.",
    "Small steps daily outperform giant leaps occasionally.",
    "Consistency is the mother of mastery.",
    "You don't rise to your goals; you fall to your systems.",
    "The best time to plant a tree was 20 years ago. The second best time is now.",
    "Excellence is not a destination; it is a continuous journey.",
    "Focus on the process, and the results will follow.",
    "Motivation gets you started. Discipline keeps you going.",
    "Do what is hard and your life will be easy.",
    "Progress, not perfection.",
    "One task at a time. One day at a time. One step at a time.",
    "The only way out is through.",
    "Show up every day, even when the results aren't visible yet.",
    "Your future self is watching you right now — make them proud.",
    "The streak doesn't build itself. You do.",
    "Fall in love with the process and the results will come.",
    "Hard work always beats talent when talent doesn't work hard.",
    "Every expert was once a beginner who refused to quit.",
    "Dreams don't work unless you do.",
    "Be so consistent that people are shocked when you take a day off.",
    "The pain of discipline is far less than the pain of regret.",
    "Reach for the Zenith — not tomorrow, today.",
    "Success is the sum of small efforts repeated day in and day out.",
    "Don't wish it were easier; wish you were better.",
    "Clear mind. Strong work. Day by day.",
    "It's not about having time, it's about making time.",
    "Outwork your excuses.",
    "The road to the top is always under construction.",
    "Strive for progress, not perfection.",
    "Your potential is only limited by your persistence.",
    "Build the habit and the habit will build you.",
    "Zenith is not a place — it's a practice.",
    "Great things never came from comfort zones.",
    "Stay patient and trust your journey.",
    "Today's effort is tomorrow's advantage.",
    "Don't count the days — make the days count.",
    "A river cuts through rock not because of its power, but its persistence.",
    "Focus is the new superpower.",
    "You are what you repeatedly do.",
    "The grind is where the growth hides.",
    "Start before you're ready.",
    "Clarity of purpose fuels consistency of action.",
    "Do something today that your future self will thank you for.",
    "Silence the doubt. Trust the process.",
    "The highest peak starts with a single step.",
    "Make your work ethic your signature.",
    "Not all progress is visible. Keep going.",
    "Master the mundane to achieve the magnificent.",
]


def get_daily_quote():
    """Same quote all day; different every day. No randomness needed."""
    today_str = str(timezone.localdate())
    idx = int(hashlib.md5(today_str.encode()).hexdigest(), 16) % len(QUOTES)
    return QUOTES[idx]


# ── Streak calculation ─────────────────────────────────────────────────────────
def calculate_streak(user):
    from .models import DayLog
    today = timezone.localdate()
    logs = DayLog.objects.filter(user=user, date__lte=today)
    completed = {l.date for l in logs if l.is_fully_completed or l.shield_used}

    if not completed:
        return 0, 0

    # Current streak
    current = 0
    check = today
    if today not in completed:
        check = today - timedelta(days=1)
    while check in completed:
        current += 1
        check -= timedelta(days=1)

    # Longest streak
    sorted_d = sorted(completed)
    longest, run = 1, 1
    for i in range(1, len(sorted_d)):
        if (sorted_d[i] - sorted_d[i - 1]).days == 1:
            run += 1
            longest = max(longest, run)
        else:
            run = 1
    longest = max(longest, run)

    return current, longest


# ── Heatmap ────────────────────────────────────────────────────────────────────
def get_heatmap_data(user):
    from datetime import timedelta
    from .models import DayLog

    today = timezone.localdate()
    start_date = today - timedelta(days=364)
    logs = DayLog.objects.filter(user=user, date__gte=start_date)
    
    heatmap = {}
    for log in logs:
        ds = log.date.strftime("%Y-%m-%d")
        
        # Calculate shade intensity based on completion % (5 levels: 0–4,
        # matching the 5 --h0..--h4 CSS variables defined per theme).
        pct = log.completion_pct()
        shade = 0
        if pct > 0: shade = 1
        if pct >= 30: shade = 2
        if pct >= 60: shade = 3
        if pct >= 90: shade = 4
        
        heatmap[ds] = {
            "shade": shade,
            "tc": log.tasks_completed,
            "tt": log.tasks_total,
            "su": log.shield_used
        }
    return heatmap


# ── Day log update (counts regular + weekly + range tasks) ────────────────────
def update_day_log(user, target_date=None):
    from .models import Task, WeeklyTask, WeeklyTaskLog, RangeTask, RangeTaskLog, DayLog
    if target_date is None:
        target_date = timezone.localdate()

    # Regular tasks
    regular = Task.objects.filter(user=user, target_date=target_date)
    reg_total = regular.count()
    reg_done = regular.filter(is_completed=True).count()

    # Weekly tasks active on that weekday
    weekday = target_date.weekday()
    weekly_qs = WeeklyTask.objects.filter(user=user, is_active=True)
    weekly_today = [wt for wt in weekly_qs if weekday in wt.weekday_list()]
    wkly_total = len(weekly_today)
    wkly_done = WeeklyTaskLog.objects.filter(
        user=user, weekly_task__in=weekly_today, date=target_date, is_completed=True
    ).count()

    # Range tasks that cover target_date
    range_qs = RangeTask.objects.filter(
        user=user, is_active=True,
        start_date__lte=target_date, end_date__gte=target_date
    )
    range_total = range_qs.count()
    range_done = RangeTaskLog.objects.filter(
        user=user, range_task__in=range_qs, date=target_date, is_completed=True
    ).count()

    total = reg_total + wkly_total + range_total
    done = reg_done + wkly_done + range_done

    log, _ = DayLog.objects.get_or_create(user=user, date=target_date)
    log.tasks_total = total
    log.tasks_completed = done
    log.is_fully_completed = total > 0 and done == total
    log.save()
    check_badges(user)
    return log


# ── Badge checking ─────────────────────────────────────────────────────────────
def check_badges(user):
    from .models import Badge, UserBadge, Task, DayLog, PomodoroLog, Note
    earned = set(UserBadge.objects.filter(user=user).values_list("badge_id", flat=True))
    cs, _ = calculate_streak(user)
    total_days   = DayLog.objects.filter(user=user, is_fully_completed=True).count()
    total_pom    = PomodoroLog.objects.filter(user=user).count()
    total_tasks  = Task.objects.filter(user=user).count()
    shields_used = DayLog.objects.filter(user=user, shield_used=True).count()
    total_notes  = Note.objects.filter(user=user).count()

    for badge in Badge.objects.all():
        if badge.id in earned:
            continue
        rt, rv = badge.requirement_type, badge.requirement_value
        give = (
            (rt == "streak_days"   and cs >= rv) or
            (rt == "total_days"    and total_days >= rv) or
            (rt == "pomodoros"     and total_pom >= rv) or
            (rt == "tasks_created" and total_tasks >= rv) or
            (rt == "shields_used"  and shields_used >= rv) or
            (rt == "notes_created" and total_notes >= rv)
        )
        if give:
            UserBadge.objects.create(user=user, badge=badge)
            if badge.badge_type == "streak":
                prof = user.profile
                prof.streak_shields = min(prof.streak_shields + 1, 5)
                prof.save()


# ── Next milestone ─────────────────────────────────────────────────────────────
def get_next_milestone(user):
    cs, _ = calculate_streak(user)
    milestones = [
        (7,   "🌱", "Sprout",        "7-Day Streak"),
        (14,  "🌿", "Sapling",       "14-Day Streak"),
        (30,  "⚓", "Navigator",     "30-Day Streak"),
        (50,  "🌊", "Rookie Sailor", "50-Day Streak"),
        (100, "⚡", "Zenith Runner", "100-Day Streak"),
        (150, "🔥", "Flame Keeper",  "150-Day Streak"),
        (200, "💫", "Star Voyager",  "200-Day Streak"),
        (365, "👑", "Legend",        "365-Day Streak"),
    ]
    for days, icon, title, subtitle in milestones:
        if cs < days:
            return {
                "target": days,
                "days_remaining": days - cs,
                "progress": round(cs / days * 100, 1),
                "icon": icon,
                "title": title,
                "subtitle": subtitle,
            }
    return None


# ── Profile statistics ─────────────────────────────────────────────────────────
def get_profile_stats(user):
    from .models import Task, WeeklyTask, RangeTask, DayLog, PomodoroLog, Note, WeeklyTaskLog
    today = timezone.localdate()
    cs, ls = calculate_streak(user)

    total_tasks_created = Task.objects.filter(user=user).count()
    total_tasks_completed = Task.objects.filter(user=user, is_completed=True).count()
    total_pomodoros = PomodoroLog.objects.filter(user=user).count()
    total_focus_mins = sum(
        p.duration_minutes for p in PomodoroLog.objects.filter(user=user)
    )
    total_notes = Note.objects.filter(user=user).count()
    total_full_days = DayLog.objects.filter(user=user, is_fully_completed=True).count()
    shields_used = DayLog.objects.filter(user=user, shield_used=True).count()
    active_weekly = WeeklyTask.objects.filter(user=user, is_active=True).count()
    active_range = RangeTask.objects.filter(
        user=user, is_active=True, end_date__gte=today
    ).count()

    # This week's completion
    week_start = today - timedelta(days=today.weekday())
    week_logs = DayLog.objects.filter(user=user, date__gte=week_start, date__lte=today)
    week_full = week_logs.filter(is_fully_completed=True).count()

    # Average completion rate (last 30 days)
    thirty_ago = today - timedelta(days=30)
    recent_logs = DayLog.objects.filter(user=user, date__gte=thirty_ago, tasks_total__gt=0)
    if recent_logs.exists():
        avg_rate = sum(l.completion_pct() for l in recent_logs) / recent_logs.count()
    else:
        avg_rate = 0

    return {
        "current_streak": cs,
        "longest_streak": ls,
        "total_full_days": total_full_days,
        "total_tasks_created": total_tasks_created,
        "total_tasks_completed": total_tasks_completed,
        "completion_rate": round(
            total_tasks_completed / total_tasks_created * 100 if total_tasks_created else 0
        ),
        "total_pomodoros": total_pomodoros,
        "total_focus_hours": round(total_focus_mins / 60, 1),
        "total_notes": total_notes,
        "shields_used": shields_used,
        "shields_remaining": user.profile.streak_shields,
        "active_weekly": active_weekly,
        "active_range": active_range,
        "week_full": week_full,
        "avg_completion_rate_30d": round(avg_rate),
    }
