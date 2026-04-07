"""Seed Ayan's timetable into the database."""
import sys
sys.path.insert(0, '.')
from app import app
from models import db, ScheduleEvent

# Subject colors
COLORS = {
    'Business Studies': '#f59e0b',
    'French': '#3b82f6',
    'English Literature': '#ec4899',
    'Combined Science': '#10b981',
    'Mathematics': '#8b5cf6',
    'Moral Education': '#64748b',
    'BTEC PE': '#ef4444',
    'Design & Technology': '#f97316',
    'Integrated Studies': '#06b6d4',
    'Physical Education': '#ef4444',
    'Form Period': '#94a3b8',
}

# Period times: Mon-Thu have 7 periods, Fri has 4 (half day)
PERIODS_WEEKDAY = [
    ('08:40', '09:35'),
    ('09:35', '10:30'),
    ('11:00', '11:55'),
    ('11:55', '12:50'),
    ('13:40', '14:35'),
    ('14:35', '15:30'),
    ('15:30', '16:00'),
]

PERIODS_FRIDAY = [
    ('08:40', '09:35'),
    ('09:35', '10:30'),
    ('10:40', '11:30'),
    ('11:30', '12:20'),
]

# WEEK A
WEEK_A = {
    0: [  # Monday
        ('Business Studies', 'SSM03'),
        ('French', 'SSU02'),
        ('English Literature', 'SSG09'),
        ('Combined Science', 'SSM13'),
        ('Combined Science', 'SSU23'),
        ('Mathematics', 'SSU10'),
        ('Moral Education', 'SSG19'),
    ],
    1: [  # Tuesday
        ('BTEC PE', 'SSU27A'),
        ('Combined Science', 'SSM24'),
        ('Mathematics', 'SSU10'),
        ('Combined Science', 'SSM13'),
        ('English Literature', 'SSG09'),
        ('Integrated Studies', 'SSM18'),
    ],
    2: [  # Wednesday
        ('Design & Technology', 'MPH02'),
        ('English Literature', 'SSG09'),
        ('BTEC PE', 'SSU27A'),
        ('Business Studies', 'SSM03'),
        ('French', 'SSU02'),
        ('Physical Education', None),
        ('Form Period', 'SSG19'),
    ],
    3: [  # Thursday
        ('BTEC PE', 'SSU27A'),
        ('Business Studies', 'SSM03'),
        ('Mathematics', 'SSU10'),
        ('English Literature', 'SSG09'),
        ('Design & Technology', 'MPH02'),
        ('French', 'SSU02'),
        ('Combined Science', 'SSM13'),
    ],
    4: [  # Friday
        ('Mathematics', 'SSU10'),
        ('Combined Science', 'SSU23'),
        ('Combined Science', 'SSM24'),
        ('Design & Technology', 'MPH02'),
    ],
}

# WEEK B
WEEK_B = {
    0: [  # Monday
        ('BTEC PE', 'SSU27A'),
        ('French', 'SSU02'),
        ('English Literature', 'SSG09'),
        ('Combined Science', 'SSU23'),
        ('Design & Technology', 'MPH02'),
        ('Combined Science', 'SSM24'),
        ('Moral Education', 'SSG19'),
    ],
    1: [  # Tuesday
        ('English Literature', 'SSG09'),
        ('Combined Science', 'SSM13'),
        ('Combined Science', 'SSM22'),
        ('BTEC PE', 'SSM13'),
        ('Mathematics', 'SSU10'),
        ('Integrated Studies', 'SSG06'),
    ],
    2: [  # Wednesday
        ('Business Studies', 'SSM03'),
        ('Combined Science', 'SSU23'),
        ('Combined Science', 'SSM24'),
        ('French', 'SSU02'),
        ('Mathematics', 'SSU10'),
        ('Physical Education', None),
        ('Form Period', 'SSG19'),
    ],
    3: [  # Thursday
        ('Combined Science', 'SSM13'),
        ('French', 'SSU02'),
        ('Mathematics', 'SSU10'),
        ('English Literature', 'SSG09'),
        ('Combined Science', 'SSM24'),
        ('Combined Science', 'SSU23'),
        ('Business Studies', 'SSM03'),
    ],
    4: [  # Friday
        ('Mathematics', 'SSU10'),
        ('English Literature', 'SSG09'),
        ('Design & Technology', 'MPH02'),
        ('Integrated Studies', 'SSU24'),
    ],
}


def seed():
    # Clear existing schedule
    ScheduleEvent.query.delete()
    db.session.commit()

    count = 0
    for week_type, week_data in [('A', WEEK_A), ('B', WEEK_B)]:
        for day, classes in week_data.items():
                periods = PERIODS_FRIDAY if day == 4 else PERIODS_WEEKDAY
                for i, (subject, room) in enumerate(classes):
                    start, end = periods[i]
                    event = ScheduleEvent(
                        title=subject,
                        day_of_week=day,
                        start_time=start,
                        end_time=end,
                        location=room,
                        color=COLORS.get(subject, '#6366f1'),
                        week_type=week_type,
                    )
                    db.session.add(event)
                    count += 1

    db.session.commit()
    print(f'Seeded {count} schedule events.')


if __name__ == '__main__':
    with app.app_context():
        seed()
