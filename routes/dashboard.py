from flask import Blueprint, render_template, jsonify, request, flash, redirect, url_for
from flask_login import login_required, current_user
from models import db, Equipment, MaintenanceRequest, Team, User
from datetime import datetime, timedelta
from sqlalchemy import func, extract

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')


@dashboard_bp.route('/')
@login_required
def index():
    """Main dashboard"""
    # Get statistics
    total_equipment = Equipment.query.filter_by(is_scrapped=False).count()
    total_requests = MaintenanceRequest.query.count()
    open_requests = MaintenanceRequest.query.filter(
        MaintenanceRequest.status.in_(['New', 'In Progress'])
    ).count()
    completed_requests = MaintenanceRequest.query.filter_by(
        status='Repaired').count()

    # Get recent requests
    recent_requests = MaintenanceRequest.query.order_by(
        MaintenanceRequest.created_at.desc()
    ).limit(5).all()

    # Get overdue requests
    overdue_requests = MaintenanceRequest.query.filter(
        MaintenanceRequest.due_date < datetime.now().date(),
        MaintenanceRequest.status.in_(['New', 'In Progress'])
    ).all()

    # Get my assigned requests (if technician)
    my_requests = []
    if current_user.role == 'Technician':
        my_requests = MaintenanceRequest.query.filter_by(
            assigned_technician_id=current_user.id,
            status='In Progress'
        ).all()

    # Get team statistics
    teams = Team.query.all()
    team_stats = []
    for team in teams:
        team_stats.append({
            'name': team.name,
            'members': team.get_member_count(),
            'open_requests': team.get_open_requests_count()
        })

    return render_template('dashboard/index.html',
                           total_equipment=total_equipment,
                           total_requests=total_requests,
                           open_requests=open_requests,
                           completed_requests=completed_requests,
                           recent_requests=recent_requests,
                           overdue_requests=overdue_requests,
                           my_requests=my_requests,
                           team_stats=team_stats)


@dashboard_bp.route('/kanban')
@login_required
def kanban():
    """Kanban board view"""
    new_requests = MaintenanceRequest.query.filter_by(status='New').order_by(
        MaintenanceRequest.created_at.desc()
    ).all()

    in_progress_requests = MaintenanceRequest.query.filter_by(status='In Progress').order_by(
        MaintenanceRequest.created_at.desc()
    ).all()

    repaired_requests = MaintenanceRequest.query.filter_by(status='Repaired').order_by(
        MaintenanceRequest.completed_at.desc()
    ).limit(20).all()

    scrap_requests = MaintenanceRequest.query.filter_by(status='Scrap').order_by(
        MaintenanceRequest.completed_at.desc()
    ).limit(20).all()

    return render_template('dashboard/kanban.html',
                           new_requests=new_requests,
                           in_progress_requests=in_progress_requests,
                           repaired_requests=repaired_requests,
                           scrap_requests=scrap_requests)


@dashboard_bp.route('/calendar')
@login_required
def calendar():
    """Calendar view for preventive maintenance"""
    preventive_requests = MaintenanceRequest.query.filter_by(
        request_type='Preventive'
    ).all()

    events = []
    for req in preventive_requests:
        if req.scheduled_date:
            events.append({
                'id': req.id,
                'title': req.subject,
                'start': req.scheduled_date.isoformat(),
                'description': req.description,
                'status': req.status,
                'equipment': req.equipment.name,
                'technician': req.assigned_technician.name if req.assigned_technician else 'Unassigned'
            })

    return render_template('dashboard/calendar.html', events=events)


@dashboard_bp.route('/reports')
@login_required
def reports():
    """Reports page"""
    # Fix: Added current_user role check logic
    if not current_user.is_manager():
        flash('Access denied. Managers only.', 'danger')
        return redirect(url_for('dashboard.index'))

    # Get current month parameters from URL
    now = datetime.now()
    year = request.args.get('year', now.year, type=int)
    month = request.args.get('month', now.month, type=int)

    # Calculate date range for filtering
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)

    # Get team reports
    teams = Team.query.all()
    team_reports = []
    for team in teams:
        # Uses the method we fixed in models.py earlier
        stats = team.get_monthly_stats(year, month)
        team_reports.append(stats)

    # Overall Statistics for the period
    total_requests = MaintenanceRequest.query.filter(
        MaintenanceRequest.created_at >= start_date,
        MaintenanceRequest.created_at < end_date
    ).count()

    completed_requests = MaintenanceRequest.query.filter(
        MaintenanceRequest.created_at >= start_date,
        MaintenanceRequest.created_at < end_date,
        MaintenanceRequest.status == 'Repaired'
    ).count()

    total_duration = db.session.query(func.sum(MaintenanceRequest.duration)).filter(
        MaintenanceRequest.created_at >= start_date,
        MaintenanceRequest.created_at < end_date,
        MaintenanceRequest.status == 'Repaired'
    ).scalar() or 0

    return render_template('dashboard/reports.html',
                           team_reports=team_reports,
                           total_requests=total_requests,
                           completed_requests=completed_requests,
                           total_duration=total_duration,
                           year=year,
                           month=month)
