import json
from datetime import date, timedelta, datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.utils import timezone
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.core.exceptions import ValidationError
from django.utils.html import escape

from .models import (Task, WeeklyTask, WeeklyTaskLog, RangeTask, RangeTaskLog,
                     DayLog, PomodoroLog, Note, Badge, UserBadge)
from .utils import (calculate_streak, get_heatmap_data, update_day_log,
                    check_badges, get_next_milestone, get_daily_quote, get_profile_stats)


# ── Security helpers ───────────────────────────────────────────────────────────
def _owned_task(request, task_id):
    return get_object_or_404(Task, id=task_id, user=request.user)

def _owned_weekly(request, wt_id):
    return get_object_or_404(WeeklyTask, id=wt_id, user=request.user)

def _owned_range(request, rt_id):
    return get_object_or_404(RangeTask, id=rt_id, user=request.user)

def _owned_note(request, note_id):
    return get_object_or_404(Note, id=note_id, user=request.user)


# ── Landing ────────────────────────────────────────────────────────────────────
def landing(request):
    if request.user.is_authenticated:
        return redirect("tracker:home")
    return render(request, "landing.html")

def privacy_view(request):
    return render(request, "privacy.html")

def terms_view(request):
    return render(request, "terms.html")


# ── Home ───────────────────────────────────────────────────────────────────────
@login_required
def home(request):
    user = request.user
    cs, ls = calculate_streak(user)
    heatmap = get_heatmap_data(user)
    total_done = DayLog.objects.filter(user=user, is_fully_completed=True).count()
    today = timezone.localdate()

    # Today's regular + range tasks for count display
    today_tasks = Task.objects.filter(user=user, target_date=today)
    today_done = today_tasks.filter(is_completed=True).count()
    today_total = today_tasks.count()

    # Add range tasks for today
    today_range = RangeTask.objects.filter(
        user=user, is_active=True, start_date__lte=today, end_date__gte=today
    )
    range_done = RangeTaskLog.objects.filter(
        user=user, range_task__in=today_range, date=today, is_completed=True
    ).count()
    today_done += range_done
    today_total += today_range.count()

    # Add weekly tasks for today
    weekday = today.weekday()
    weekly_qs = WeeklyTask.objects.filter(user=user, is_active=True)
    weekly_today = [wt for wt in weekly_qs if weekday in wt.weekday_list()]
    weekly_done = WeeklyTaskLog.objects.filter(
        user=user, weekly_task__in=weekly_today, date=today, is_completed=True
    ).count()
    today_done += weekly_done
    today_total += len(weekly_today)

    milestone = get_next_milestone(user)
    recent_badges = UserBadge.objects.filter(user=user).select_related("badge").order_by("-earned_at")[:4]

    return render(request, "tracker/home.html", {
        "current_streak": cs,
        "longest_streak": ls,
        "shields": user.profile.streak_shields,
        "today_done": today_done,
        "today_total": today_total,
        "heatmap_data": heatmap,
        "total_done": total_done,
        "milestone": milestone,
        "recent_badges": recent_badges,
        "quote": get_daily_quote(),
        "today": today,
    })


# ── Today ──────────────────────────────────────────────────────────────────────
@login_required
def today_view(request):
    user = request.user
    today = timezone.localdate()
    weekday = today.weekday()

    # 1. Today's regular tasks
    today_tasks = list(Task.objects.filter(user=user, target_date=today).order_by("created_at"))

    # 2. Overdue tasks (past due, not completed)
    overdue_tasks = list(
        Task.objects.filter(user=user, target_date__lt=today, is_completed=False)
        .order_by("target_date", "created_at")[:20]
    )

    # 3. Weekly tasks for today
    weekly_qs = WeeklyTask.objects.filter(user=user, is_active=True)
    weekly_today = [wt for wt in weekly_qs if weekday in wt.weekday_list()]
    weekly_logs = {
        log.weekly_task_id: log
        for log in WeeklyTaskLog.objects.filter(user=user, date=today, weekly_task__in=weekly_today)
    }
    weekly_with_status = [
        {"task": wt, "log": weekly_logs.get(wt.id), "done": bool(weekly_logs.get(wt.id) and weekly_logs[wt.id].is_completed)}
        for wt in weekly_today
    ]

    # 4. Range tasks active today
    range_tasks = list(RangeTask.objects.filter(
        user=user, is_active=True, start_date__lte=today, end_date__gte=today
    ))
    range_logs = {
        log.range_task_id: log
        for log in RangeTaskLog.objects.filter(user=user, date=today, range_task__in=range_tasks)
    }
    range_with_status = [
        {
            "task": rt,
            "log": range_logs.get(rt.id),
            "done": bool(range_logs.get(rt.id) and range_logs[rt.id].is_completed),
            "days_left": (rt.end_date - today).days,
            "progress": round((today - rt.start_date).days / max((rt.end_date - rt.start_date).days, 1) * 100),
        }
        for rt in range_tasks
    ]

    # Sync day log
    update_day_log(user, today)

    tasks_done = sum(1 for t in today_tasks if t.is_completed)
    tasks_total = len(today_tasks)
    weekly_done_count = sum(1 for w in weekly_with_status if w["done"])
    weekly_total = len(weekly_with_status)
    range_done_count = sum(1 for r in range_with_status if r["done"])
    range_total = len(range_with_status)

    total_pom = PomodoroLog.objects.filter(user=user).count()
    all_count = tasks_total + weekly_total + range_total
    done_count = tasks_done + weekly_done_count + range_done_count
    all_done = all_count > 0 and done_count == all_count

    return render(request, "tracker/today.html", {
        "today": today,
        "tasks": today_tasks,
        "overdue_tasks": overdue_tasks,
        "weekly_with_status": weekly_with_status,
        "range_with_status": range_with_status,
        "tasks_done": tasks_done,
        "tasks_total": tasks_total,
        "weekly_done": weekly_done_count,
        "weekly_total": weekly_total,
        "range_done": range_done_count,
        "range_total": range_total,
        "total_done_all": done_count,
        "total_all": all_count,
        "total_pomodoros": total_pom,
        "all_done": all_done,
    })


# ── Tasks ──────────────────────────────────────────────────────────────────────
@login_required
def tasks_view(request):
    user = request.user
    today = timezone.localdate()

    if request.method == "POST":
        task_type = request.POST.get("task_type", "one_time")
        title = escape(request.POST.get("title", "").strip())
        shade = request.POST.get("shade", "0")

        if not title or len(title) > 300:
            return redirect("tracker:tasks")
        try:
            shade = max(0, min(5, int(shade)))
        except (ValueError, TypeError):
            shade = 0

        if task_type == "range":
            start_str = request.POST.get("start_date", "").strip()
            end_str = request.POST.get("end_date", "").strip()
            try:
                # Try standard HTML5 format first (YYYY-MM-DD)
                try:
                    start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
                    end_date = datetime.strptime(end_str, "%Y-%m-%d").date()
                except ValueError:
                    # Fallback for DD-MM-YYYY format from your UI
                    start_date = datetime.strptime(start_str, "%d-%m-%Y").date()
                    end_date = datetime.strptime(end_str, "%d-%m-%Y").date()

                if end_date < start_date:
                    return redirect("tracker:tasks")
                
                RangeTask.objects.create(
                    user=user, title=title, shade=shade,
                    start_date=start_date, end_date=end_date
                )
                # Update day logs for range
                cur = start_date
                while cur <= min(end_date, today):
                    update_day_log(user, cur)
                    cur += timedelta(days=1)
            except ValueError:
                pass
        else:
            date_str = request.POST.get("target_date", "").strip()
            try:
                td = datetime.strptime(date_str, "%Y-%m-%d").date()
                Task.objects.create(user=user, title=title, shade=shade, target_date=td)
                update_day_log(user, td)
            except ValueError:
                pass

        return redirect("tracker:tasks")

    upcoming = Task.objects.filter(user=user, target_date__gte=today).order_by("target_date", "created_at")
    overdue  = Task.objects.filter(user=user, target_date__lt=today, is_completed=False).order_by("target_date")
    past_done = Task.objects.filter(user=user, target_date__lt=today, is_completed=True).order_by("-target_date")[:60]

    # Active range tasks
    active_range = RangeTask.objects.filter(user=user, is_active=True, end_date__gte=today).order_by("start_date")
    all_range = RangeTask.objects.filter(user=user).order_by("-start_date")[:30]

    from itertools import groupby
    grouped_upcoming = [(d, list(g)) for d, g in groupby(upcoming, key=lambda t: t.target_date)]

    return render(request, "tracker/tasks.html", {
        "grouped_upcoming": grouped_upcoming,
        "overdue_tasks": overdue,
        "past_tasks": past_done,
        "active_range_tasks": active_range,
        "all_range_tasks": all_range,
        "today": today,
    })


# ── Weekly Tasks ───────────────────────────────────────────────────────────────
@login_required
def weekly_tasks_view(request):
    user = request.user
    WEEKDAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    if request.method == "POST":
        action = request.POST.get("action", "")

        if action == "create":
            title = escape(request.POST.get("title", "").strip())
            shade = request.POST.get("shade", "0")
            weekdays_raw = request.POST.getlist("weekdays")

            if not title or len(title) > 300:
                return redirect("tracker:weekly_tasks")

            try:
                shade = max(0, min(5, int(shade)))
            except (ValueError, TypeError):
                shade = 0

            valid_days = sorted(set(
                int(d) for d in weekdays_raw
                if d.isdigit() and 0 <= int(d) <= 6
            ))
            if not valid_days:
                return redirect("tracker:weekly_tasks")

            WeeklyTask.objects.create(
                user=user, title=title, shade=shade,
                weekdays=",".join(str(d) for d in valid_days)
            )

        elif action == "toggle":
            wt_id = request.POST.get("id", "")
            if wt_id.isdigit():
                wt = get_object_or_404(WeeklyTask, id=int(wt_id), user=user)
                wt.is_active = not wt.is_active
                wt.save()

        elif action == "delete":
            wt_id = request.POST.get("id", "")
            if wt_id.isdigit():
                get_object_or_404(WeeklyTask, id=int(wt_id), user=user).delete()

        return redirect("tracker:weekly_tasks")

    weekly_tasks = WeeklyTask.objects.filter(user=user).order_by("-is_active", "created_at")
    return render(request, "tracker/weekly_tasks.html", {
        "weekly_tasks": weekly_tasks,
        "weekday_names": WEEKDAY_NAMES,
        "weekday_range": list(range(7)),
    })


# ── History ────────────────────────────────────────────────────────────────────
@login_required
def history_view(request):
    logs = DayLog.objects.filter(user=request.user).order_by("-date")[:90]
    return render(request, "tracker/history.html", {"logs": logs})


# ── Notes ──────────────────────────────────────────────────────────────────────
@login_required
def notes_view(request):
    user = request.user
    if request.method == "POST":
        action = request.POST.get("action", "create")

        if action == "create":
            title   = escape(request.POST.get("title", "").strip()[:200])
            content = request.POST.get("content", "").strip()
            color   = request.POST.get("color", "default")
            if color not in ("default", "warm", "cool", "accent"):
                color = "default"
            if content:
                Note.objects.create(user=user, title=title, content=content, color=color)
                check_badges(user)

        elif action == "pin":
            note_id = request.POST.get("id", "")
            if note_id.isdigit():
                note = get_object_or_404(Note, id=int(note_id), user=user)
                note.is_pinned = not note.is_pinned
                note.save()

        elif action == "delete":
            note_id = request.POST.get("id", "")
            if note_id.isdigit():
                get_object_or_404(Note, id=int(note_id), user=user).delete()

        return redirect("tracker:notes")

    notes = Note.objects.filter(user=user).order_by("-is_pinned", "-updated_at")
    return render(request, "tracker/notes.html", {"notes": notes})


@login_required
def note_edit_view(request, note_id):
    note = _owned_note(request, note_id)
    if request.method == "POST":
        title   = escape(request.POST.get("title", "").strip()[:200])
        content = request.POST.get("content", "").strip()
        color   = request.POST.get("color", "default")
        if color not in ("default", "warm", "cool", "accent"):
            color = "default"
        if content:
            note.title = title
            note.content = content
            note.color = color
            note.save()
        return redirect("tracker:notes")
    return render(request, "tracker/note_edit.html", {"note": note})


# ── Profile ────────────────────────────────────────────────────────────────────
@login_required
def profile_view(request):
    user = request.user
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "theme":
            theme = request.POST.get("theme", "midnight")
            if theme in ("midnight", "paper"):
                user.profile.theme = theme
                user.profile.save()
            return redirect("tracker:profile")
        elif action == "password":
            form = PasswordChangeForm(user, request.POST)
            if form.is_valid():
                u = form.save()
                update_session_auth_hash(request, u)
                return redirect("tracker:profile")
            return render(request, "tracker/profile.html", {
                "pw_form": form, "pw_open": True, **_profile_ctx(user),
            })
        elif action == "update_email":
            new_email = request.POST.get("email", "").strip()
            if new_email and "@" in new_email:
                user.email = new_email
                user.save()
            return redirect("tracker:profile")
    return render(request, "tracker/profile.html", {
        "pw_form": PasswordChangeForm(user), **_profile_ctx(user),
    })


def _profile_ctx(user):
    earned_ids = set(UserBadge.objects.filter(user=user).values_list("badge_id", flat=True))
    streak_badges = UserBadge.objects.filter(user=user, badge__badge_type="streak").select_related("badge")
    ach_badges    = UserBadge.objects.filter(user=user, badge__badge_type="achievement").select_related("badge")
    all_badges    = Badge.objects.all()
    stats         = get_profile_stats(user)
    # Recent activity (last 7 days)
    today = timezone.localdate()
    recent_logs = DayLog.objects.filter(user=user, date__gte=today - timedelta(days=6)).order_by("date")
    return {
        "streak_badges": streak_badges,
        "ach_badges": ach_badges,
        "all_badges": all_badges,
        "earned_ids": earned_ids,
        "stats": stats,
        "recent_logs": recent_logs,
        "today": today,
        "member_since": user.date_joined,
    }


# ── JSON APIs ──────────────────────────────────────────────────────────────────
@login_required
@require_POST
def api_complete_task(request):
    try:
        data = json.loads(request.body)
        task_id = int(data.get("task_id", 0))
    except (json.JSONDecodeError, ValueError, TypeError):
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)

    task = get_object_or_404(Task, id=task_id, user=request.user)
    task.is_completed = bool(data.get("completed", True))
    task.completed_at = timezone.now() if task.is_completed else None
    task.save()
    log = update_day_log(request.user, task.target_date)
    cs, _ = calculate_streak(request.user)

    # Update today's log too if this was an overdue task
    today = timezone.localdate()
    today_log = update_day_log(request.user, today)

    return JsonResponse({
        "success": True,
        "fully_completed": log.is_fully_completed,
        "tasks_completed": log.tasks_completed,
        "tasks_total": log.tasks_total,
        "current_streak": cs,
        "today_done": today_log.tasks_completed,
        "today_total": today_log.tasks_total,
    })


@login_required
@require_POST
def api_complete_weekly(request):
    try:
        data = json.loads(request.body)
        wt_id = int(data.get("wt_id", 0))
        done  = bool(data.get("completed", True))
    except (json.JSONDecodeError, ValueError, TypeError):
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)

    wt = get_object_or_404(WeeklyTask, id=wt_id, user=request.user)
    today = timezone.localdate()
    log, _ = WeeklyTaskLog.objects.get_or_create(
        user=request.user, weekly_task=wt, date=today
    )
    log.is_completed = done
    log.save()
    day_log = update_day_log(request.user, today)
    cs, _ = calculate_streak(request.user)
    return JsonResponse({
        "success": True,
        "fully_completed": day_log.is_fully_completed,
        "current_streak": cs,
        "today_done": day_log.tasks_completed,
        "today_total": day_log.tasks_total,
    })


@login_required
@require_POST
def api_complete_range(request):
    try:
        data = json.loads(request.body)
        rt_id = int(data.get("rt_id", 0))
        done  = bool(data.get("completed", True))
    except (json.JSONDecodeError, ValueError, TypeError):
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)

    rt = get_object_or_404(RangeTask, id=rt_id, user=request.user)
    today = timezone.localdate()
    log, _ = RangeTaskLog.objects.get_or_create(
        user=request.user, range_task=rt, date=today
    )
    log.is_completed = done
    log.save()
    day_log = update_day_log(request.user, today)
    cs, _ = calculate_streak(request.user)
    return JsonResponse({
        "success": True,
        "fully_completed": day_log.is_fully_completed,
        "current_streak": cs,
        "today_done": day_log.tasks_completed,
        "today_total": day_log.tasks_total,
    })


@login_required
@require_POST
def api_log_pomodoro(request):
    try:
        data = json.loads(request.body)
        duration = int(data.get("duration", 25))
        if duration not in (25, 45, 60):
            duration = 25
    except (json.JSONDecodeError, ValueError, TypeError):
        return JsonResponse({"success": False, "error": "Invalid data"}, status=400)

    PomodoroLog.objects.create(user=request.user, duration_minutes=duration)
    check_badges(request.user)
    total = PomodoroLog.objects.filter(user=request.user).count()
    return JsonResponse({"success": True, "total_pomodoros": total})


@login_required
@require_POST
def api_use_shield(request):
    user = request.user
    if user.profile.streak_shields <= 0:
        return JsonResponse({"success": False, "error": "No shields available"})
    yesterday = timezone.localdate() - timedelta(days=1)
    log, _ = DayLog.objects.get_or_create(user=user, date=yesterday)
    if log.is_fully_completed or log.shield_used:
        return JsonResponse({"success": False, "error": "Shield not needed or already used"})
    log.shield_used = True
    log.save()
    user.profile.streak_shields -= 1
    user.profile.save()
    cs, _ = calculate_streak(user)
    return JsonResponse({"success": True, "shields": user.profile.streak_shields, "current_streak": cs})


@login_required
@require_POST
def api_delete_task(request):
    try:
        data = json.loads(request.body)
        task_id = int(data.get("task_id", 0))
    except (json.JSONDecodeError, ValueError, TypeError):
        return JsonResponse({"success": False}, status=400)

    task = get_object_or_404(Task, id=task_id, user=request.user)
    td = task.target_date
    task.delete()
    update_day_log(request.user, td)
    return JsonResponse({"success": True})


@login_required
@require_POST
def api_delete_range(request):
    try:
        data = json.loads(request.body)
        rt_id = int(data.get("rt_id", 0))
    except (json.JSONDecodeError, ValueError, TypeError):
        return JsonResponse({"success": False}, status=400)

    rt = get_object_or_404(RangeTask, id=rt_id, user=request.user)
    today = timezone.localdate()
    start = rt.start_date
    end = min(rt.end_date, today)
    rt.delete()
    # Update affected day logs
    cur = start
    while cur <= end:
        update_day_log(request.user, cur)
        cur += timedelta(days=1)
    return JsonResponse({"success": True})


@login_required
def api_home_stats(request):
    """Live stats for home page refresh."""
    user = request.user
    today = timezone.localdate()
    cs, ls = calculate_streak(user)

    today_log = DayLog.objects.filter(user=user, date=today).first()
    done = today_log.tasks_completed if today_log else 0
    total = today_log.tasks_total if today_log else 0

    return JsonResponse({
        "current_streak": cs,
        "longest_streak": ls,
        "shields": user.profile.streak_shields,
        "today_done": done,
        "today_total": total,
    })