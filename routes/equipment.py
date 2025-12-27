from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Equipment, Team, User, MaintenanceRequest
from datetime import datetime

equipment_bp = Blueprint('equipment', __name__, url_prefix='/equipment')

@equipment_bp.route('/')
@login_required
def list_equipment():
    """List all equipment with filters"""
    # Get filter parameters
    department = request.args.get('department', '')
    employee = request.args.get('employee', '')
    status = request.args.get('status', '')
    search = request.args.get('search', '')
    
    # Base query
    query = Equipment.query
    
    # Apply filters
    if department:
        query = query.filter_by(department=department)
    if employee:
        query = query.filter(Equipment.assigned_employee.contains(employee))
    if status == 'scrapped':
        query = query.filter_by(is_scrapped=True)
    elif status == 'operational':
        query = query.filter_by(is_scrapped=False)
    if search:
        query = query.filter(
            db.or_(
                Equipment.name.contains(search),
                Equipment.serial_number.contains(search)
            )
        )
    
    equipment_list = query.order_by(Equipment.created_at.desc()).all()
    
    # Get unique departments for filter
    departments = db.session.query(Equipment.department).distinct().all()
    departments = [d[0] for d in departments]
    
    return render_template('equipment/list.html',
                          equipment_list=equipment_list,
                          departments=departments,
                          filters={'department': department, 'employee': employee, 'status': status, 'search': search})


@equipment_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create new equipment"""
    if not current_user.is_manager():
        flash('Access denied. Managers and Admins only.', 'danger')
        return redirect(url_for('equipment.list_equipment'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        serial_number = request.form.get('serial_number')
        department = request.form.get('department')
        assigned_employee = request.form.get('assigned_employee')
        team_id = request.form.get('team_id')
        default_technician_id = request.form.get('default_technician_id')
        purchase_date = request.form.get('purchase_date')
        warranty_expiry = request.form.get('warranty_expiry')
        location = request.form.get('location')
        
        # Validation
        if not all([name, serial_number, department, team_id]):
            flash('Please fill all required fields.', 'danger')
            return render_template('equipment/create.html',
                                  teams=Team.query.all(),
                                  technicians=User.query.filter_by(role='Technician').all())
        
        # Check if serial number exists
        if Equipment.query.filter_by(serial_number=serial_number).first():
            flash('Serial number already exists.', 'danger')
            return render_template('equipment/create.html',
                                  teams=Team.query.all(),
                                  technicians=User.query.filter_by(role='Technician').all())
        
        # Create equipment
        equipment = Equipment(
            name=name,
            serial_number=serial_number,
            department=department,
            assigned_employee=assigned_employee,
            team_id=team_id,
            default_technician_id=default_technician_id if default_technician_id else None,
            purchase_date=datetime.strptime(purchase_date, '%Y-%m-%d').date() if purchase_date else None,
            warranty_expiry=datetime.strptime(warranty_expiry, '%Y-%m-%d').date() if warranty_expiry else None,
            location=location
        )
        
        db.session.add(equipment)
        db.session.commit()
        
        flash('Equipment created successfully!', 'success')
        return redirect(url_for('equipment.view', id=equipment.id))
    
    # GET request
    teams = Team.query.all()
    technicians = User.query.filter_by(role='Technician').all()
    
    return render_template('equipment/create.html', teams=teams, technicians=technicians)


@equipment_bp.route('/<int:id>')
@login_required
def view(id):
    """View equipment details"""
    equipment = Equipment.query.get_or_404(id)
    
    # Get maintenance requests for this equipment
    maintenance_requests = equipment.maintenance_requests.order_by(
        MaintenanceRequest.created_at.desc()
    ).all()
    
    return render_template('equipment/view.html',
                          equipment=equipment,
                          maintenance_requests=maintenance_requests)


@equipment_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Edit equipment"""
    if not current_user.is_manager():
        flash('Access denied. Managers and Admins only.', 'danger')
        return redirect(url_for('equipment.view', id=id))
    
    equipment = Equipment.query.get_or_404(id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        serial_number = request.form.get('serial_number')
        department = request.form.get('department')
        assigned_employee = request.form.get('assigned_employee')
        team_id = request.form.get('team_id')
        default_technician_id = request.form.get('default_technician_id')
        purchase_date = request.form.get('purchase_date')
        warranty_expiry = request.form.get('warranty_expiry')
        location = request.form.get('location')
        is_scrapped = request.form.get('is_scrapped') == 'on'
        
        # Check if serial number is taken by another equipment
        existing = Equipment.query.filter_by(serial_number=serial_number).first()
        if existing and existing.id != equipment.id:
            flash('Serial number already exists.', 'danger')
            return render_template('equipment/edit.html',
                                  equipment=equipment,
                                  teams=Team.query.all(),
                                  technicians=User.query.filter_by(role='Technician').all())
        
        # Update equipment
        equipment.name = name
        equipment.serial_number = serial_number
        equipment.department = department
        equipment.assigned_employee = assigned_employee
        equipment.team_id = team_id
        equipment.default_technician_id = default_technician_id if default_technician_id else None
        equipment.purchase_date = datetime.strptime(purchase_date, '%Y-%m-%d').date() if purchase_date else None
        equipment.warranty_expiry = datetime.strptime(warranty_expiry, '%Y-%m-%d').date() if warranty_expiry else None
        equipment.location = location
        equipment.is_scrapped = is_scrapped
        
        db.session.commit()
        
        flash('Equipment updated successfully!', 'success')
        return redirect(url_for('equipment.view', id=equipment.id))
    
    # GET request
    teams = Team.query.all()
    technicians = User.query.filter_by(role='Technician').all()
    
    return render_template('equipment/edit.html',
                          equipment=equipment,
                          teams=teams,
                          technicians=technicians)


@equipment_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """Delete equipment"""
    if not current_user.is_admin():
        flash('Access denied. Admins only.', 'danger')
        return redirect(url_for('equipment.view', id=id))
    
    equipment = Equipment.query.get_or_404(id)
    
    # Check if there are active maintenance requests
    active_requests = equipment.maintenance_requests.filter(
        MaintenanceRequest.status.in_(['New', 'In Progress'])
    ).count()
    
    if active_requests > 0:
        flash('Cannot delete equipment with active maintenance requests.', 'danger')
        return redirect(url_for('equipment.view', id=id))
    
    db.session.delete(equipment)
    db.session.commit()
    
    flash('Equipment deleted successfully!', 'success')
    return redirect(url_for('equipment.list_equipment'))
