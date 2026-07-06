from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from decimal import Decimal

db = SQLAlchemy()


# STATES

class State(db.Model):
    __tablename__ = 'states'

    state_id   = db.Column(db.Integer, primary_key=True, autoincrement=True)
    state_name = db.Column(db.String(100), nullable=False)

    # Relationships
    facilities = db.relationship('Facility', backref='state', lazy=True)
    workers    = db.relationship('Worker',   backref='state', lazy=True)

    def __repr__(self):
        return f'<State {self.state_name}>'



# PROFESSIONS

class Profession(db.Model):
    __tablename__ = 'professions'

    profession_id   = db.Column(db.Integer, primary_key=True, autoincrement=True)
    profession_name = db.Column(db.String(100), nullable=False)

    # Relationships
    workers = db.relationship('Worker', backref='profession', lazy=True)
    shifts  = db.relationship('Shift',  backref='profession', lazy=True)

    def __repr__(self):
        return f'<Profession {self.profession_name}>'



# ADMINS

class Admin(db.Model):
    __tablename__ = 'admins'

    admin_id   = db.Column(db.Integer, primary_key=True, autoincrement=True)
    first_name = db.Column(db.String(50),  nullable=False)
    last_name  = db.Column(db.String(50),  nullable=False)
    email      = db.Column(db.String(100), nullable=False, unique=True)
    password   = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)

    def __repr__(self):
        return f'<Admin {self.first_name} {self.last_name}>'



# FACILITIES

class Facility(db.Model):
    __tablename__ = 'facilities'

    facility_id      = db.Column(db.Integer, primary_key=True, autoincrement=True)
    state_id         = db.Column(db.Integer, db.ForeignKey('states.state_id'), nullable=False)
    facility_name    = db.Column(db.String(225), nullable=False)
    facility_address = db.Column(db.String(255), nullable=False)
    city             = db.Column(db.String(100), nullable=False)
    contact_email    = db.Column(db.String(100), nullable=False, unique=True)
    contact_phone    = db.Column(db.String(20),  nullable=False)
    password         = db.Column(db.String(255), nullable=False)
    plan             = db.Column(db.Enum('basic', 'standard', 'premium'), nullable=False, default='basic')
    plan_expires_at  = db.Column(db.TIMESTAMP, nullable=True)
    cac_document              = db.Column(db.String(255), nullable=True)
    operating_licence_document = db.Column(db.String(255), nullable=True)
    status           = db.Column(db.Enum('pending', 'active', 'inactive', 'suspended'), nullable=False, default='pending')
    created_at       = db.Column(db.TIMESTAMP, default=datetime.utcnow)

    # Relationships
    shifts = db.relationship('Shift', backref='facility', lazy=True)

    def __repr__(self):
        return f'<Facility {self.facility_name}>'



# WORKERS

class Worker(db.Model):
    __tablename__ = 'workers'

    worker_id      = db.Column(db.Integer, primary_key=True, autoincrement=True)
    profession_id  = db.Column(db.Integer, db.ForeignKey('professions.profession_id'), nullable=False)
    state_id       = db.Column(db.Integer, db.ForeignKey('states.state_id'),           nullable=False)
    first_name     = db.Column(db.String(50),  nullable=False)
    last_name      = db.Column(db.String(50),  nullable=False)
    email_address  = db.Column(db.String(100), nullable=False, unique=True)
    phone_number   = db.Column(db.String(20),  nullable=False)
    licence_number = db.Column(db.String(50),  nullable=True)
    password       = db.Column(db.String(255), nullable=False)
    bank_name           = db.Column(db.String(100), nullable=True)
    bank_account_number = db.Column(db.String(20),  nullable=True)
    bank_account_name   = db.Column(db.String(100), nullable=True)
    licence_document      = db.Column(db.String(255), nullable=True)
    qualification_document = db.Column(db.String(255), nullable=True)
    id_document           = db.Column(db.String(255), nullable=True)
    passport_photo        = db.Column(db.String(255), nullable=True)
    status         = db.Column(db.Enum('pending', 'active', 'inactive', 'suspended'), nullable=False, default='pending')
    created_at     = db.Column(db.TIMESTAMP, default=datetime.utcnow)

    # Relationships
    bookings  = db.relationship('Booking',        backref='worker', lazy=True)
    locations = db.relationship('WorkerLocation', backref='worker', lazy=True)

    def __repr__(self):
        return f'<Worker {self.first_name} {self.last_name}>'



# SHIFTS

class Shift(db.Model):
    __tablename__ = 'shifts'

    shift_id      = db.Column(db.Integer, primary_key=True, autoincrement=True)
    facility_id   = db.Column(db.Integer, db.ForeignKey('facilities.facility_id'), nullable=False)
    profession_id = db.Column(db.Integer, db.ForeignKey('professions.profession_id'), nullable=False)
    role_needed   = db.Column(db.String(100),       nullable=False)
    shift_date    = db.Column(db.Date,              nullable=False)
    start_time    = db.Column(db.Time,              nullable=False)
    end_time      = db.Column(db.Time,              nullable=False)
    pay_rate      = db.Column(db.Numeric(10, 2),    nullable=False)
    status        = db.Column(
                        db.Enum('open', 'filled', 'cancelled', 'completed'),
                        nullable=False,
                        default='open'
                    )
    created_at    = db.Column(db.TIMESTAMP, default=datetime.utcnow)

    # Relationships
    bookings = db.relationship('Booking', backref='shift', lazy=True)

    def __repr__(self):
        return f'<Shift {self.role_needed} on {self.shift_date}>'

    @property
    def shift_type_label(self):
        hour = self.start_time.hour
        if 5 <= hour < 12:
            return 'Morning Shift'
        elif 12 <= hour < 17:
            return 'Day Shift'
        elif 17 <= hour < 21:
            return 'Evening Shift'
        else:
            return 'Night Shift'

    @property
    def duration_hours(self):
        start_minutes = self.start_time.hour * 60 + self.start_time.minute
        end_minutes = self.end_time.hour * 60 + self.end_time.minute
        if end_minutes <= start_minutes:
            end_minutes += 24 * 60
        return (end_minutes - start_minutes) / 60

    @property
    def duration_display(self):
        start_minutes = self.start_time.hour * 60 + self.start_time.minute
        end_minutes = self.end_time.hour * 60 + self.end_time.minute
        if end_minutes <= start_minutes:
            end_minutes += 24 * 60
        total_minutes = end_minutes - start_minutes
        hours, minutes = divmod(total_minutes, 60)
        if minutes == 0:
            return f'{hours}h'
        return f'{hours}h {minutes}m'

    @property
    def total_pay(self):
        return self.pay_rate * Decimal(str(self.duration_hours))



# BOOKINGS
class Booking(db.Model):
    __tablename__ = 'bookings'

    booking_id     = db.Column(db.Integer, primary_key=True, autoincrement=True)
    shift_id       = db.Column(db.Integer, db.ForeignKey('shifts.shift_id'),   nullable=False)
    worker_id      = db.Column(db.Integer, db.ForeignKey('workers.worker_id'), nullable=False)
    booking_status = db.Column(
                        db.Enum('pending', 'confirmed', 'cancelled', 'completed'),
                        nullable=False,
                        default='pending'
                    )
    booked_at      = db.Column(db.TIMESTAMP, default=datetime.utcnow)

    # Relationships
    review   = db.relationship('Review',        backref='booking', uselist=False, lazy=True)
    payment  = db.relationship('Payment',       backref='booking', uselist=False, lazy=True)
    location = db.relationship('WorkerLocation', backref='booking', uselist=False, lazy=True)

    def __repr__(self):
        return f'<Booking {self.booking_id} — status: {self.booking_status}>'


# REVIEWS

class Review(db.Model):
    __tablename__ = 'reviews'

    review_id   = db.Column(db.Integer, primary_key=True, autoincrement=True)
    booking_id  = db.Column(db.Integer, db.ForeignKey('bookings.booking_id'), nullable=False, unique=True)
    rating      = db.Column(db.SmallInteger, nullable=False)  # TINYINT
    comment     = db.Column(db.Text, nullable=True)
    reviewed_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)

    def __repr__(self):
        return f'<Review {self.review_id} — rating: {self.rating}>'



# PAYMENTS

class Payment(db.Model):
    __tablename__ = 'payments'

    payment_id      = db.Column(db.Integer, primary_key=True, autoincrement=True)
    booking_id      = db.Column(db.Integer, db.ForeignKey('bookings.booking_id'), nullable=False, unique=True)
    amount_held     = db.Column(db.Numeric(10, 2), nullable=False)
    commission      = db.Column(db.Numeric(10, 2), nullable=False)
    worker_payout   = db.Column(db.Numeric(10, 2), nullable=False)
    payment_method  = db.Column(db.String(50),     nullable=False)
    paystack_reference = db.Column(db.String(100), nullable=True, unique=True)
    payment_status  = db.Column(
                        db.Enum('pending', 'held', 'released', 'refunded'),
                        nullable=False,
                        default='pending'
                    )
    paid_at         = db.Column(db.TIMESTAMP, nullable=True)
    released_at     = db.Column(db.TIMESTAMP, nullable=True)
    refunded_at     = db.Column(db.TIMESTAMP, nullable=True)

    def __repr__(self):
        return f'<Payment {self.payment_id} — {self.payment_status}>'



# WORKER LOCATIONS

class WorkerLocation(db.Model):
    __tablename__ = 'worker_locations'

    location_id  = db.Column(db.Integer, primary_key=True, autoincrement=True)
    worker_id    = db.Column(db.Integer, db.ForeignKey('workers.worker_id'),   nullable=False)
    booking_id   = db.Column(db.Integer, db.ForeignKey('bookings.booking_id'), nullable=False)
    latitude     = db.Column(db.Numeric(10, 8), nullable=False)
    longitude    = db.Column(db.Numeric(11, 8), nullable=False)
    recorded_at  = db.Column(db.TIMESTAMP, default=datetime.utcnow)

    def __repr__(self):
        return f'<WorkerLocation worker={self.worker_id} at ({self.latitude}, {self.longitude})>'