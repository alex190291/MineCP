"""
System setup tracking model.
"""
from app.extensions import db
from datetime import datetime


class SystemSetup(db.Model):
    """Track system setup completion."""
    __tablename__ = 'system_setup'

    id = db.Column(db.Integer, primary_key=True)
    setup_key = db.Column(db.String(50), unique=True, nullable=False)
    completed = db.Column(db.Boolean, default=False, nullable=False)
    completed_at = db.Column(db.DateTime)

    def __repr__(self):
        return f'<SystemSetup {self.setup_key}: {self.completed}>'

    @staticmethod
    def is_first_run():
        """Check if this is the first run of the application."""
        setup = SystemSetup.query.filter_by(setup_key='initial_setup').first()
        return setup is None or not setup.completed

    @staticmethod
    def mark_setup_complete():
        """Mark initial setup as complete."""
        setup = SystemSetup.query.filter_by(setup_key='initial_setup').first()
        if setup is None:
            setup = SystemSetup(setup_key='initial_setup')
            db.session.add(setup)

        setup.completed = True
        setup.completed_at = datetime.utcnow()
        db.session.commit()
