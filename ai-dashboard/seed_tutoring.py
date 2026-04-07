"""Seed Ayan's tutoring sessions into the database."""
from models import db, CalendarEvent

# Tutor subject colors
TUTOR_COLORS = {
    'Biology': '#10b981',
    'Business': '#f59e0b',
    'Chemistry': '#8b5cf6',
    'English': '#ec4899',
    'Physics': '#3b82f6',
    'Maths': '#ef4444',
}

# Tutoring sessions extracted from calendar screenshot
SESSIONS = [
    ('2026-03-30', 'Biology', '16:00', '17:00'),
    ('2026-03-31', 'Business', '16:00', '17:00'),
    ('2026-03-31', 'Chemistry', '18:00', '19:00'),
    ('2026-04-01', 'Biology', '16:00', '17:00'),
    ('2026-04-01', 'English', '17:30', '18:30'),
    ('2026-04-02', 'Physics', '17:00', '18:00'),
    ('2026-04-03', 'English', '16:30', '17:30'),
    ('2026-04-04', 'Biology', '13:00', '14:00'),
    ('2026-04-05', 'English', '12:30', '13:30'),
    ('2026-04-06', 'Biology', '16:00', '17:00'),
    ('2026-04-06', 'Maths', '17:30', '18:30'),
    ('2026-04-07', 'English', '17:00', '18:00'),
    ('2026-04-07', 'Chemistry', '18:00', '19:00'),
    ('2026-04-08', 'Biology', '16:00', '17:00'),
    ('2026-04-08', 'English', '18:30', '19:30'),
    ('2026-04-09', 'Business', '16:00', '17:00'),
    ('2026-04-09', 'Physics', '18:00', '19:00'),
    ('2026-04-10', 'English', '11:30', '12:30'),
    ('2026-04-11', 'Biology', '13:00', '14:00'),
    ('2026-04-12', 'English', '12:30', '13:30'),
    ('2026-04-12', 'Maths', '11:00', '12:00'),
]


def seed_tutoring():
    count = 0
    for date, subject, start, end in SESSIONS:
        event = CalendarEvent(
            title=f'{subject} Tutoring',
            date=date,
            start_time=start,
            end_time=end,
            color=TUTOR_COLORS.get(subject, '#f59e0b'),
            event_type='tutor',
        )
        db.session.add(event)
        count += 1
    db.session.commit()
    print(f'Seeded {count} tutoring sessions.')


if __name__ == '__main__':
    import sys
    sys.path.insert(0, '.')
    from app import app
    with app.app_context():
        seed_tutoring()
