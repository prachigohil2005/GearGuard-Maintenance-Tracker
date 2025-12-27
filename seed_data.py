from models import db, User, Team, Equipment, MaintenanceRequest
from datetime import datetime, timedelta
import random


def seed_database():
    """Seed the database with sample data"""

    print("🌱 Seeding database...")

    # Create users
    users = [
        {'name': 'Admin User', 'email': 'admin@gearguard.com',
            'password': 'admin123', 'role': 'Admin'},
        {'name': 'John Manager', 'email': 'manager@gearguard.com',
            'password': 'manager123', 'role': 'Manager'},
        {'name': 'Mike Mechanic', 'email': 'mike@gearguard.com',
            'password': 'tech123', 'role': 'Technician'},
        {'name': 'Sarah Electrician', 'email': 'sarah@gearguard.com',
            'password': 'tech123', 'role': 'Technician'},
        {'name': 'David IT', 'email': 'david@gearguard.com',
            'password': 'tech123', 'role': 'Technician'},
        {'name': 'Lisa Tech', 'email': 'lisa@gearguard.com',
            'password': 'tech123', 'role': 'Technician'},
    ]

    user_objects = []
    for user_data in users:
        user = User(
            name=user_data['name'], email=user_data['email'], role=user_data['role'])
        user.set_password(user_data['password'])
        db.session.add(user)
        user_objects.append(user)

    db.session.commit()
    print(f"✅ Created {len(user_objects)} users")

    # Create teams
    # FIXED: Changed index 6 to 4 in General Maintenance to stay within user_objects bounds (0-5)
    teams_data = [
        {'name': 'Mechanical Team',
            'description': 'Handles all mechanical equipment maintenance', 'members': [2, 3]},
        {'name': 'Electrical Team',
            'description': 'Manages electrical systems and wiring', 'members': [3, 4]},
        {'name': 'IT Support Team',
            'description': 'Maintains computers and network equipment', 'members': [4, 5]},
        {'name': 'General Maintenance',
            'description': 'General facility maintenance', 'members': [5, 4]},
    ]

    team_objects = []
    for team_data in teams_data:
        team = Team(name=team_data['name'],
                    description=team_data['description'])

        # Add members
        for member_idx in team_data['members']:
            team.members.append(user_objects[member_idx])

        db.session.add(team)
        team_objects.append(team)

    db.session.commit()
    print(f"✅ Created {len(team_objects)} teams")

    # Create equipment
    equipment_data = [
        {'name': 'CNC Machine #1', 'serial': 'CNC-001',
            'dept': 'Production', 'team': 0, 'employee': 'John Smith'},
        {'name': 'CNC Machine #2', 'serial': 'CNC-002',
            'dept': 'Production', 'team': 0, 'employee': 'Jane Doe'},
        {'name': 'Industrial Printer', 'serial': 'PRINT-001',
            'dept': 'Production', 'team': 0, 'employee': ''},
        {'name': 'Power Generator', 'serial': 'GEN-001',
            'dept': 'Facilities', 'team': 1, 'employee': ''},
        {'name': 'HVAC System A', 'serial': 'HVAC-001',
            'dept': 'Facilities', 'team': 1, 'employee': ''},
        {'name': 'Server Rack #1', 'serial': 'SRV-001',
            'dept': 'IT', 'team': 2, 'employee': 'Tech Team'},
        {'name': 'Network Switch', 'serial': 'NET-001',
            'dept': 'IT', 'team': 2, 'employee': ''},
        {'name': 'Forklift #1', 'serial': 'FORK-001',
            'dept': 'Warehouse', 'team': 3, 'employee': 'Bob Wilson'},
        {'name': 'Conveyor Belt', 'serial': 'CONV-001',
            'dept': 'Warehouse', 'team': 0, 'employee': ''},
        {'name': 'Air Compressor', 'serial': 'COMP-001',
            'dept': 'Production', 'team': 0, 'employee': ''},
    ]

    equipment_objects = []
    for eq_data in equipment_data:
        # FIXED: Added min() to technician indexing to prevent future out-of-range errors
        tech_idx = min(eq_data['team'] + 2, len(user_objects) - 1)

        equipment = Equipment(
            name=eq_data['name'],
            serial_number=eq_data['serial'],
            department=eq_data['dept'],
            assigned_employee=eq_data['employee'],
            team_id=team_objects[eq_data['team']].id,
            default_technician_id=user_objects[tech_idx].id,
            purchase_date=(datetime.now() -
                           timedelta(days=random.randint(365, 1825))).date(),
            warranty_expiry=(datetime.now() +
                             timedelta(days=random.randint(-180, 365))).date(),
            location=f"Building A, Floor {random.randint(1, 3)}"
        )
        db.session.add(equipment)
        equipment_objects.append(equipment)

    db.session.commit()
    print(f"✅ Created {len(equipment_objects)} equipment items")

    # Create maintenance requests
    request_subjects = [
        'Oil leak detected', 'Unusual noise during operation', 'Equipment not starting',
        'Routine inspection', 'Quarterly maintenance', 'Sensor calibration',
        'Belt replacement needed', 'Electrical short circuit', 'Overheating issue',
        'Software update required', 'Preventive checkup', 'Parts replacement'
    ]

    statuses = ['New', 'In Progress', 'Repaired', 'New', 'In Progress']
    request_types = ['Corrective', 'Corrective', 'Preventive']

    maintenance_requests = []
    for i in range(20):
        equipment = random.choice(equipment_objects)
        request_type = random.choice(request_types)
        status = random.choice(statuses)

        req = MaintenanceRequest(
            subject=random.choice(request_subjects),
            description=f"Detailed description for maintenance request #{i+1}. This requires attention from the maintenance team.",
            request_type=request_type,
            equipment_id=equipment.id,
            team_id=equipment.team_id,
            assigned_technician_id=equipment.default_technician_id if random.random() > 0.3 else None,
            scheduled_date=(datetime.now() + timedelta(days=random.randint(-10, 30))
                            ).date() if request_type == 'Preventive' else None,
            due_date=(datetime.now() +
                      timedelta(days=random.randint(-5, 15))).date(),
            duration=round(random.uniform(0.5, 8.0),
                           1) if status == 'Repaired' else None,
            status=status,
            # Use real IDs from the seeded users
            created_by_id=random.choice(
                [user_objects[0].id, user_objects[1].id]),
            created_at=datetime.now() - timedelta(days=random.randint(0, 30)),
            completed_at=datetime.now() - timedelta(days=random.randint(0, 5)
                                                    ) if status == 'Repaired' else None
        )
        db.session.add(req)
        maintenance_requests.append(req)

    db.session.commit()
    print(f"✅ Created {len(maintenance_requests)} maintenance requests")

    print("\n🎉 Database seeded successfully!")
    print("\n📋 Test Accounts:")
    print("   Admin:     admin@gearguard.com / admin123")
    print("   Manager:   manager@gearguard.com / manager123")
    print("   Technician: mike@gearguard.com / tech123")
