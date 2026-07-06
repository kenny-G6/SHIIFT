from datetime import datetime
from decimal import Decimal
from flask import render_template, request, redirect, session, flash, url_for
from werkzeug.security import check_password_hash

from pkg import app
from pkg.models import db, Admin, Worker, Facility, Shift, Booking, Payment

@app.route('/admin/login/', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        admin = Admin.query.filter_by(email=email).first()

        if not email or not password:
            flash('All fields are required', category='errormsg')
            return redirect(url_for('admin_login'))
        elif not admin or not check_password_hash(admin.password, password):
            flash('Invalid admin login details', category='errormsg')
            return redirect(url_for('admin_login'))
        else:
            session['adminlogin'] = admin.admin_id
            flash('You are now logged in as an Admin', category='feedback')
            return redirect(url_for('admin_dashboard'))

    return render_template('admin/admin-login.html')


@app.get('/admin/dashboard/')
def admin_dashboard():
    if session.get('adminlogin') is None:
        flash('You must be logged in as an admin', category='errormsg')
        return redirect(url_for('admin_login'))

    pending_workers = Worker.query.filter_by(status='pending').order_by(Worker.created_at).all()
    pending_facilities = Facility.query.filter_by(status='pending').order_by(Facility.created_at).all()

    releasable_payments = (
        db.session.query(Payment)
        .join(Booking, Payment.booking_id == Booking.booking_id)
        .filter(Payment.payment_status == 'held', Booking.booking_status == 'completed')
        .all()
    )
    recently_released = Payment.query.filter_by(payment_status='released').order_by(Payment.released_at.desc()).limit(5).all()

    return render_template(
        'admin/admin-dashboard.html',
        pending_workers=pending_workers,
        pending_facilities=pending_facilities,
        releasable_payments=releasable_payments,
        recently_released=recently_released,
        commission_rate=app.config['COMMISSION_RATE'],
    )


@app.get('/admin/logout/')
def admin_logout():
    if session.get('adminlogin'):
        session.pop('adminlogin', None)
        session.clear()
    return redirect(url_for('admin_login'))


@app.get('/admin/worker/<int:worker_id>/')
def worker_detail(worker_id):
    if session.get('adminlogin') is None:
        flash('You must be logged in as an admin', category='errormsg')
        return redirect(url_for('admin_login'))

    worker = Worker.query.get_or_404(worker_id)
    bookings = Booking.query.filter_by(worker_id=worker_id).order_by(Booking.booked_at.desc()).all()

    shifts_done = sum(1 for b in bookings if b.booking_status == 'completed')
    upcoming_count = sum(1 for b in bookings if b.booking_status in ('pending', 'confirmed'))

    released_payments = (
        db.session.query(Payment)
        .join(Booking, Payment.booking_id == Booking.booking_id)
        .filter(Booking.worker_id == worker_id, Payment.payment_status == 'released')
        .all()
    )
    total_earned = sum((p.worker_payout for p in released_payments), start=Decimal('0'))

    return render_template(
        'admin/worker-detail.html',
        worker=worker,
        bookings=bookings,
        shifts_done=shifts_done,
        upcoming_count=upcoming_count,
        total_earned=total_earned,
    )


@app.get('/admin/facility/<int:facility_id>/')
def facility_detail(facility_id):
    if session.get('adminlogin') is None:
        flash('You must be logged in as an admin', category='errormsg')
        return redirect(url_for('admin_login'))

    facility = Facility.query.get_or_404(facility_id)
    shifts = Shift.query.filter_by(facility_id=facility_id).order_by(Shift.shift_date.desc()).all()

    open_count = sum(1 for s in shifts if s.status == 'open')
    filled_count = sum(1 for s in shifts if s.status == 'filled')
    completed_count = sum(1 for s in shifts if s.status == 'completed')

    shift_ids = [s.shift_id for s in shifts]
    captured_payments = []
    if shift_ids:
        captured_payments = (
            db.session.query(Payment)
            .join(Booking, Payment.booking_id == Booking.booking_id)
            .filter(Booking.shift_id.in_(shift_ids), Payment.payment_status.in_(['held', 'released']))
            .all()
        )
    total_spent = sum((p.amount_held for p in captured_payments), start=Decimal('0'))

    return render_template(
        'admin/facility-detail.html',
        facility=facility,
        shifts=shifts,
        open_count=open_count,
        filled_count=filled_count,
        completed_count=completed_count,
        total_spent=total_spent,
    )


@app.get('/admin/workers/')
def admin_workers():
    if session.get('adminlogin') is None:
        flash('You must be logged in as an admin', category='errormsg')
        return redirect(url_for('admin_login'))

    workers = Worker.query.order_by(Worker.created_at.desc()).all()
    counts = {
        'all': len(workers),
        'active': sum(1 for w in workers if w.status == 'active'),
        'pending': sum(1 for w in workers if w.status == 'pending'),
        'suspended': sum(1 for w in workers if w.status == 'suspended'),
    }
    return render_template('admin/admin-workers.html', workers=workers, counts=counts)


@app.post('/admin/worker/<int:worker_id>/status/')
def update_worker_status(worker_id):
    if session.get('adminlogin') is None:
        flash('You must be logged in as an admin', category='errormsg')
        return redirect(url_for('admin_login'))

    new_status = request.form.get('status')
    next_page = request.form.get('next')
    fallback = redirect(url_for('worker_detail', worker_id=worker_id)) if next_page == 'detail' else redirect(url_for('admin_workers'))

    if new_status not in ('active', 'suspended'):
        flash('Invalid status', category='errormsg')
        return fallback

    worker = Worker.query.get_or_404(worker_id)
    worker.status = new_status
    db.session.commit()
    flash(f'{worker.first_name} {worker.last_name} is now {new_status}', category='feedback')
    return fallback


@app.get('/admin/facilities/')
def admin_facilities():
    if session.get('adminlogin') is None:
        flash('You must be logged in as an admin', category='errormsg')
        return redirect(url_for('admin_login'))

    facilities = Facility.query.order_by(Facility.created_at.desc()).all()
    counts = {
        'all': len(facilities),
        'active': sum(1 for f in facilities if f.status == 'active'),
        'pending': sum(1 for f in facilities if f.status == 'pending'),
        'suspended': sum(1 for f in facilities if f.status == 'suspended'),
    }
    return render_template('admin/admin-facilities.html', facilities=facilities, counts=counts)


@app.post('/admin/facility/<int:facility_id>/status/')
def update_facility_status(facility_id):
    if session.get('adminlogin') is None:
        flash('You must be logged in as an admin', category='errormsg')
        return redirect(url_for('admin_login'))

    new_status = request.form.get('status')
    next_page = request.form.get('next')
    fallback = redirect(url_for('facility_detail', facility_id=facility_id)) if next_page == 'detail' else redirect(url_for('admin_facilities'))

    if new_status not in ('active', 'suspended'):
        flash('Invalid status', category='errormsg')
        return fallback

    facility = Facility.query.get_or_404(facility_id)
    facility.status = new_status
    db.session.commit()
    flash(f'{facility.facility_name} is now {new_status}', category='feedback')
    return fallback


@app.get('/admin/shifts/')
def admin_shifts():
    if session.get('adminlogin') is None:
        flash('You must be logged in as an admin', category='errormsg')
        return redirect(url_for('admin_login'))

    shifts = Shift.query.order_by(Shift.shift_date.desc()).all()
    counts = {
        'all': len(shifts),
        'open': sum(1 for s in shifts if s.status == 'open'),
        'filled': sum(1 for s in shifts if s.status == 'filled'),
        'completed': sum(1 for s in shifts if s.status == 'completed'),
        'cancelled': sum(1 for s in shifts if s.status == 'cancelled'),
    }
    return render_template('admin/admin-shifts.html', shifts=shifts, counts=counts)


@app.post('/admin/shift/<int:shift_id>/remove/')
def admin_remove_shift(shift_id):
    if session.get('adminlogin') is None:
        flash('You must be logged in as an admin', category='errormsg')
        return redirect(url_for('admin_login'))

    shift = Shift.query.get_or_404(shift_id)
    if shift.status != 'open':
        flash('Only open shifts can be removed this way', category='errormsg')
        return redirect(url_for('admin_shifts'))

    shift.status = 'cancelled'
    db.session.commit()
    flash('Shift removed from the marketplace', category='feedback')
    return redirect(url_for('admin_shifts'))


@app.get('/admin/bookings/')
def admin_bookings():
    if session.get('adminlogin') is None:
        flash('You must be logged in as an admin', category='errormsg')
        return redirect(url_for('admin_login'))

    bookings = Booking.query.order_by(Booking.booked_at.desc()).all()
    counts = {
        'all': len(bookings),
        'upcoming': sum(1 for b in bookings if b.booking_status in ('pending', 'confirmed')),
        'completed': sum(1 for b in bookings if b.booking_status == 'completed'),
        'cancelled': sum(1 for b in bookings if b.booking_status == 'cancelled'),
    }
    return render_template('admin/admin-bookings.html', bookings=bookings, counts=counts)


@app.get('/admin/payments/')
def admin_payments():
    if session.get('adminlogin') is None:
        flash('You must be logged in as an admin', category='errormsg')
        return redirect(url_for('admin_login'))

    payments = Payment.query.order_by(Payment.payment_id.desc()).all()
    counts = {
        'all': len(payments),
        'pending': sum(1 for p in payments if p.payment_status == 'pending'),
        'held': sum(1 for p in payments if p.payment_status == 'held'),
        'released': sum(1 for p in payments if p.payment_status == 'released'),
        'refunded': sum(1 for p in payments if p.payment_status == 'refunded'),
    }
    captured = [p for p in payments if p.payment_status in ('held', 'released')]
    totals = {
        'processed': sum((p.amount_held for p in captured), start=Decimal('0')),
        'commission': sum((p.commission for p in captured), start=Decimal('0')),
        'pending_payout': sum((p.amount_held for p in payments if p.payment_status == 'held'), start=Decimal('0')),
        'refunded': sum((p.amount_held for p in payments if p.payment_status == 'refunded'), start=Decimal('0')),
    }
    return render_template(
        'admin/admin-payments.html',
        payments=payments,
        counts=counts,
        totals=totals,
        commission_rate=app.config['COMMISSION_RATE'],
    )


@app.post('/admin/payment/<int:payment_id>/release/')
def release_payment(payment_id):
    if session.get('adminlogin') is None:
        flash('You must be logged in as an admin', category='errormsg')
        return redirect(url_for('admin_login'))

    payment = Payment.query.get_or_404(payment_id)
    if payment.booking.booking_status != 'completed' or payment.payment_status != 'held':
        flash('This payment is not eligible for release yet', category='errormsg')
        return redirect(url_for('admin_payments'))

    payment.payment_status = 'released'
    payment.released_at = datetime.utcnow()
    db.session.commit()
    flash('Payment marked as released. Make sure you have actually sent the worker their payout.', category='feedback')
    return redirect(url_for('admin_payments'))
