from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import db, MaintenanceRequest, Equipment, Team, User
from datetime import datetime

requests_bp = Blueprint('requests', __name__, url_prefix='/requests')

@requests_bp.route('/')
@login_required
def list_requests():
    """List all maintenance requests"""
    # Get filter parameters
    status = request.args.get('status', '')
    request_type = request.args.get('type', '')
    team_id = request.args.get('team', '')
    search = request.args.get('search', '')
    
    # Base query
    query = MaintenanceRequest.query
    
    # Apply filters
    if status:
        query = query.filter_by(status=status)
    if request_type:
        query = query.filter_by(request_type=request_type)
    if team_id:
        query = query.filter_by(team_id=team_id)
    if search:
        query = query.filter(
            db.or_(
                MaintenanceRequest.subject.contains(search),
                MaintenanceRequest.description.contains(search)
            )
        )
    
    # Role-based filtering
    if current_user.role == 'Technician':
        # Technicians see only their team's requests
        user_teams = [team.id for team in current_user.teams]
        query = query.filter(MaintenanceRequest.team_id.in_(user_teams))
    
    maintenance_requests = query.order_by(MaintenanceRequest.created_at.desc()).all()
    
    # Get teams for filter
    teams = Team.query.all()
    
    return render_template('requests/list.html',
                          maintenance_requests=maintenance_requests,
                          teams=teams,
                          filters={'status': status, 'type': request_type, 'team': team_id, 'search': search})


@requests_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create new maintenance request"""
    if request.method == 'POST':
        subject = request.form.get('subject')
        description = request.form.get('description')
        request_type = request.form.get('request_type')
        equipment_id = request.form.get('equipment_id')
        scheduled_date = request.form.get('scheduled_date')
        due_date = request.form.get('due_date')
        
        # Validation
        if not all([subject, description, request_type, equipment_id]):
            flash('Please fill all required fields.', 'danger')
            return render_template('requests/create.html',
                                  equipment_list=Equipment.query.filter_by(is_scrapped=False).all())
        
        # Get equipment to auto-fill team
        equipment = Equipment.query.get(equipment_id)
        if not equipment:
            flash('Invalid equipment selected.', 'danger')
            return render_template('requests/create.html',
                                  equipment_list=Equipment.query.filter_by(is_scrapped=False).all())
        
        # Create maintenance request
        maintenance_request = MaintenanceRequest(
            subject=subject,
            description=description,
            request_type=request_type,
            equipment_id=equipment_id,
            team_id=equipment.team_id,  # Auto-filled from equipment
            scheduled_date=datetime.strptime(scheduled_date, '%Y-%m-%d').date() if scheduled_date else None,
            due_date=datetime.strptime(due_date, '%Y-%m-%d').date() if due_date else None,
            created_by_id=current_user.id,
            status='New'
        )
        
        # Auto-assign default technician if available
        if equipment.default_technician_id:
            maintenance_request.assigned_technician_id = equipment.default_technician_id
        
        db.session.add(maintenance_request)
        db.session.commit()
        
        flash('Maintenance request created successfully!', 'success')
        return redirect(url_for('requests.view', id=maintenance_request.id))
    
    # GET request
    equipment_list = Equipment.query.filter_by(is_scrapped=False).order_by(Equipment.name).all()
    return render_template('requests/create.html', equipment_list=equipment_list)


@requests_bp.route('/<int:id>')
@login_required
def view(id):
    """View maintenance request details"""
    maintenance_request = MaintenanceRequest.query.get_or_404(id)
    
    # Check access for technicians
    if current_user.role == 'Technician':
        user_teams = [team.id for team in current_user.teams]
        if maintenance_request.team_id not in user_teams:
            flash('Access denied.', 'danger')
            return redirect(url_for('requests.list_requests'))
    
    # Get available technicians for assignment
    technicians = User.query.join(User.teams).filter(
        Team.id == maintenance_request.team_id
    ).all()
    
    return render_template('requests/view.html',
                          request=maintenance_request,
                          technicians=technicians)


@requests_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Edit maintenance request"""
    maintenance_request = MaintenanceRequest.query.get_or_404(id)
    
    # Check permissions
    can_edit = (
        current_user.is_manager() or
        maintenance_request.created_by_id == current_user.id or
        maintenance_request.assigned_technician_id == current_user.id
    )
    
    if not can_edit:
        flash('You do not have permission to edit this request.', 'danger')
        return redirect(url_for('requests.view', id=id))
    
    if request.method == 'POST':
        subject = request.form.get('subject')
        description = request.form.get('description')
        request_type = request.form.get('request_type')
        scheduled_date = request.form.get('scheduled_date')
        due_date = request.form.get('due_date')
        duration = request.form.get('duration')
        notes = request.form.get('notes')
        
        # Update request
        maintenance_request.subject = subject
        maintenance_request.description = description
        maintenance_request.request_type = request_type
        maintenance_request.scheduled_date = datetime.strptime(scheduled_date, '%Y-%m-%d').date() if scheduled_date else None
        maintenance_request.due_date = datetime.strptime(due_date, '%Y-%m-%d').date() if due_date else None
        maintenance_request.duration = float(duration) if duration else None
        maintenance_request.notes = notes
        
        db.session.commit()
        
        flash('Maintenance request updated successfully!', 'success')
        return redirect(url_for('requests.view', id=maintenance_request.id))
    
    # GET request
    return render_template('requests/edit.html', request=maintenance_request)


@requests_bp.route('/<int:id>/assign', methods=['POST'])
@login_required
def assign(id):
    """Assign technician to request"""
    maintenance_request = MaintenanceRequest.query.get_or_404(id)
    technician_id = request.form.get('technician_id')
    
    # Check if user can assign (manager or self-assignment)
    if not current_user.is_manager() and int(technician_id) != current_user.id:
        flash('You can only assign yourself.', 'danger')
        return redirect(url_for('requests.view', id=id))
    
    # Verify technician is in the team
    technician = User.query.get(technician_id)
    user_teams = [team.id for team in technician.teams]
    
    if maintenance_request.team_id not in user_teams:
        flash('Technician is not part of the maintenance team.', 'danger')
        return redirect(url_for('requests.view', id=id))
    
    maintenance_request.assigned_technician_id = technician_id
    
    # If status is New, change to In Progress
    if maintenance_request.status == 'New':
        maintenance_request.status = 'In Progress'
    
    db.session.commit()
    
    flash('Technician assigned successfully!', 'success')
    return redirect(url_for('requests.view', id=id))


@requests_bp.route('/<int:id>/update-status', methods=['POST'])
@login_required
def update_status(id):
    """Update request status"""
    maintenance_request = MaintenanceRequest.query.get_or_404(id)
    new_status = request.form.get('status')
    
    # Check permissions
    can_update = (
        current_user.is_manager() or
        maintenance_request.assigned_technician_id == current_user.id
    )
    
    if not can_update:
        flash('You do not have permission to update this request.', 'danger')
        return redirect(url_for('requests.view', id=id))
    
    # Update status
    old_status = maintenance_request.status
    maintenance_request.status = new_status
    
    # If marked as Repaired or Scrap, set completion time
    if new_status in ['Repaired', 'Scrap'] and old_status not in ['Repaired', 'Scrap']:
        maintenance_request.completed_at = datetime.utcnow()
    
    # Special handling for Scrap status
    if new_status == 'Scrap':
        equipment = maintenance_request.equipment
        equipment.is_scrapped = True
        
        # Add system note
        if not maintenance_request.notes:
            maintenance_request.notes = ''
        maintenance_request.notes += f'\n[SYSTEM] Equipment marked as scrapped on {datetime.now().strftime("%Y-%m-%d %H:%M")}'
    
    db.session.commit()
    
    flash(f'Request status updated to {new_status}!', 'success')
    return redirect(url_for('requests.view', id=id))


@requests_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """Delete maintenance request"""
    maintenance_request = MaintenanceRequest.query.get_or_404(id)
    
    # Only admin or creator can delete
    if not (current_user.is_admin() or maintenance_request.created_by_id == current_user.id):
        flash('Access denied.', 'danger')
        return redirect(url_for('requests.view', id=id))
    
    db.session.delete(maintenance_request)
    db.session.commit()
    
    flash('Maintenance request deleted successfully!', 'success')
    return redirect(url_for('requests.list_requests'))


@requests_bp.route('/api/update-status/<int:id>', methods=['POST'])
@login_required
def api_update_status(id):
    """API endpoint for updating status (for Kanban drag & drop)"""
    try:
        maintenance_request = MaintenanceRequest.query.get_or_404(id)
        data = request.get_json()
        new_status = data.get('status')
        
        # Check permissions
        can_update = (
            current_user.is_manager() or
            maintenance_request.assigned_technician_id == current_user.id
        )
        
        if not can_update:
            return jsonify({'success': False, 'message': 'Access denied'}), 403
        
        # Update status
        old_status = maintenance_request.status
        maintenance_request.status = new_status
        
        # If marked as Repaired or Scrap, set completion time
        if new_status in ['Repaired', 'Scrap'] and old_status not in ['Repaired', 'Scrap']:
            maintenance_request.completed_at = datetime.utcnow()
        
        # Special handling for Scrap status
        if new_status == 'Scrap':
            equipment = maintenance_request.equipment
            equipment.is_scrapped = True
            if not maintenance_request.notes:
                maintenance_request.notes = ''
            maintenance_request.notes += f'\n[SYSTEM] Equipment marked as scrapped on {datetime.now().strftime("%Y-%m-%d %H:%M")}'
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Status updated'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
