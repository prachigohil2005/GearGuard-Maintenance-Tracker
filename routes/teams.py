from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Team, User

teams_bp = Blueprint('teams', __name__, url_prefix='/teams')

@teams_bp.route('/')
@login_required
def list_teams():
    """List all teams"""
    teams = Team.query.order_by(Team.name).all()
    return render_template('teams/list.html', teams=teams)


@teams_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create new team"""
    if not current_user.is_manager():
        flash('Access denied. Managers and Admins only.', 'danger')
        return redirect(url_for('teams.list_teams'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        member_ids = request.form.getlist('members')
        
        # Validation
        if not name:
            flash('Team name is required.', 'danger')
            return render_template('teams/create.html',
                                  users=User.query.filter_by(role='Technician').all())
        
        # Check if team name exists
        if Team.query.filter_by(name=name).first():
            flash('Team name already exists.', 'danger')
            return render_template('teams/create.html',
                                  users=User.query.filter_by(role='Technician').all())
        
        # Create team
        team = Team(name=name, description=description)
        
        # Add members
        if member_ids:
            members = User.query.filter(User.id.in_(member_ids)).all()
            for member in members:
                team.members.append(member)
        
        db.session.add(team)
        db.session.commit()
        
        flash('Team created successfully!', 'success')
        return redirect(url_for('teams.view', id=team.id))
    
    # GET request
    users = User.query.filter_by(role='Technician').all()
    return render_template('teams/create.html', users=users)


@teams_bp.route('/<int:id>')
@login_required
def view(id):
    """View team details"""
    team = Team.query.get_or_404(id)
    
    # Get team statistics
    open_requests = team.requests.filter(
        db.or_(
            team.requests.c.status == 'New',
            team.requests.c.status == 'In Progress'
        )
    ).count() if hasattr(team.requests, 'c') else team.get_open_requests_count()
    
    return render_template('teams/view.html', team=team, open_requests=open_requests)


@teams_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Edit team"""
    if not current_user.is_manager():
        flash('Access denied. Managers and Admins only.', 'danger')
        return redirect(url_for('teams.view', id=id))
    
    team = Team.query.get_or_404(id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        member_ids = request.form.getlist('members')
        
        # Check if name is taken by another team
        existing = Team.query.filter_by(name=name).first()
        if existing and existing.id != team.id:
            flash('Team name already exists.', 'danger')
            return render_template('teams/edit.html',
                                  team=team,
                                  users=User.query.filter_by(role='Technician').all())
        
        # Update team
        team.name = name
        team.description = description
        
        # Update members
        team.members = []
        if member_ids:
            members = User.query.filter(User.id.in_(member_ids)).all()
            for member in members:
                team.members.append(member)
        
        db.session.commit()
        
        flash('Team updated successfully!', 'success')
        return redirect(url_for('teams.view', id=team.id))
    
    # GET request
    users = User.query.filter_by(role='Technician').all()
    return render_template('teams/edit.html', team=team, users=users)


@teams_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """Delete team"""
    if not current_user.is_admin():
        flash('Access denied. Admins only.', 'danger')
        return redirect(url_for('teams.view', id=id))
    
    team = Team.query.get_or_404(id)
    
    # Check if team has equipment assigned
    if team.equipment.count() > 0:
        flash('Cannot delete team with assigned equipment.', 'danger')
        return redirect(url_for('teams.view', id=id))
    
    db.session.delete(team)
    db.session.commit()
    
    flash('Team deleted successfully!', 'success')
    return redirect(url_for('teams.list_teams'))
