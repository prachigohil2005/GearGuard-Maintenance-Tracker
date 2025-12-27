from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import secrets

db = SQLAlchemy()

# Association table for team members
team_members = db.Table('team_members',
                        db.Column('user_id', db.Integer, db.ForeignKey(
                            'users.id'), primary_key=True),
                        db.Column('team_id', db.Integer, db.ForeignKey(
                            'teams.id'), primary_key=True)
                        )


class User(UserMixin, db.Model):
    """User model for authentication and role management"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='Technician')
    reset_token = db.Column(db.String(100), unique=True)
    reset_token_expiry = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship to Teams
    # We define it here. It will automatically create 'members' on the Team objects
    teams = db.relationship('Team', secondary=team_members,
                            backref=db.backref('members', lazy='joined'))

    assigned_requests = db.relationship('MaintenanceRequest',
                                        foreign_keys='MaintenanceRequest.assigned_technician_id',
                                        backref='assigned_technician',
                                        lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_reset_token(self):
        self.reset_token = secrets.token_urlsafe(32)
        return self.reset_token

    def is_admin(self):
        return self.role == 'Admin'

    def is_manager(self):
        return self.role in ['Admin', 'Manager']

    def __repr__(self):
        return f'<User {self.name}>'


class Team(db.Model):
    """Maintenance team model"""
    __tablename__ = 'teams'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    equipment = db.relationship(
        'Equipment', backref='maintenance_team', lazy='dynamic')
    requests = db.relationship(
        'MaintenanceRequest', backref='team', lazy='dynamic')

    # Note: 'members' is automatically created here by the backref in the User class

    def get_member_count(self):
        return len(self.members)

    def get_open_requests_count(self):
        return self.requests.filter(MaintenanceRequest.status.in_(['New', 'In Progress'])).count()

    def get_monthly_stats(self, year, month):
        start_date = datetime(year, month, 1)
        end_date = datetime(
            year + 1, 1, 1) if month == 12 else datetime(year, month + 1, 1)

        requests_list = self.requests.filter(
            MaintenanceRequest.created_at >= start_date,
            MaintenanceRequest.created_at < end_date
        ).all()

        completed = [r for r in requests_list if r.status == 'Repaired']
        total_hours = sum(r.duration or 0 for r in completed)

        return {
            'total_requests': len(requests_list),
            'completed': len(completed),
            'total_hours': total_hours,
            'team_name': self.name
        }

    def __repr__(self):
        return f'<Team {self.name}>'


class Equipment(db.Model):
    """Equipment/Asset model"""
    __tablename__ = 'equipment'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    serial_number = db.Column(db.String(100), unique=True, nullable=False)
    department = db.Column(db.String(100), nullable=False)
    assigned_employee = db.Column(db.String(100))
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    default_technician_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    purchase_date = db.Column(db.Date)
    warranty_expiry = db.Column(db.Date)
    location = db.Column(db.String(200))
    is_scrapped = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    default_technician = db.relationship(
        'User', foreign_keys=[default_technician_id])
    maintenance_requests = db.relationship('MaintenanceRequest',
                                           backref='equipment',
                                           lazy='dynamic',
                                           cascade='all, delete-orphan')

    def get_open_requests_count(self):
        return self.maintenance_requests.filter(
            MaintenanceRequest.status.in_(['New', 'In Progress'])
        ).count()

    def get_status_badge(self):
        if self.is_scrapped:
            return 'Scrapped'
        if self.get_open_requests_count() > 0:
            return 'Maintenance Due'
        return 'Operational'

    def __repr__(self):
        return f'<Equipment {self.name}>'


class MaintenanceRequest(db.Model):
    """Maintenance request model"""
    __tablename__ = 'maintenance_requests'

    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    request_type = db.Column(db.String(20), nullable=False)
    equipment_id = db.Column(db.Integer, db.ForeignKey(
        'equipment.id'), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    assigned_technician_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    scheduled_date = db.Column(db.Date)
    duration = db.Column(db.Float)
    status = db.Column(db.String(20), nullable=False, default='New')
    created_by_id = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.Date)
    completed_at = db.Column(db.DateTime)
    notes = db.Column(db.Text)

    created_by = db.relationship('User', foreign_keys=[created_by_id])

    def is_overdue(self):
        if self.status in ['Repaired', 'Scrap']:
            return False
        if self.due_date:
            return datetime.now().date() > self.due_date
        return False

    def get_status_class(self):
        return {
            'New': 'status-new',
            'In Progress': 'status-progress',
            'Repaired': 'status-repaired',
            'Scrap': 'status-scrap'
        }.get(self.status, 'status-new')

    def get_priority_class(self):
        if self.is_overdue():
            return 'priority-high'
        return 'priority-medium' if self.request_type == 'Corrective' else 'priority-low'

    def __repr__(self):
        return f'<MaintenanceRequest {self.subject}>'
