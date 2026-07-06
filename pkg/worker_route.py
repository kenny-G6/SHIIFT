from flask import render_template, request, redirect, flash, session, url_for

from pkg import app
from pkg.models import db, Worker, Profession, State, Shift, Booking, Payment

@app.get('/worker/dashboard/')
def worker_dashboard():
    if session.get('workeronline') is None:
        flash('You must be logged in to view this page', category='errormsg')
        return redirect(url_for('index'))
    deets = Worker.query.get(session['workeronline'])
    return render_template('worker/worker-dashboard.html', deets=deets)


@app.get('/worker/browse-shifts/')
def browse_shifts():
    if session.get('workeronline') is None:
        flash('You must be logged in to view this page', category='errormsg')
        return redirect(url_for('index'))

    worker_id = session['workeronline']
    applied_shift_ids = [
        b.shift_id for b in Booking.query.filter_by(worker_id=worker_id)
        .filter(Booking.booking_status.in_(['pending', 'confirmed']))
        .all()
    ]

    shifts = (
        Shift.query.filter_by(status='open')
        .filter(~Shift.shift_id.in_(applied_shift_ids))
        .order_by(Shift.shift_date)
        .all()
    )
    professions = Profession.query.order_by(Profession.profession_name).all()
    states = State.query.order_by(State.state_name).all()
    return render_template('worker/browse-shifts.html', shifts=shifts, professions=professions, states=states)


@app.get('/worker/shift/<int:shift_id>/')
def shift_detail(shift_id):
    if session.get('workeronline') is None:
        flash('You must be logged in to view this page', category='errormsg')
        return redirect(url_for('index'))
    shift = Shift.query.get_or_404(shift_id)
    return render_template('worker/shift-detail.html', shift=shift)


@app.post('/worker/shift/<int:shift_id>/book/')
def book_shift(shift_id):
    if session.get('workeronline') is None:
        flash('You must be logged in to do that', category='errormsg')
        return redirect(url_for('index'))

    worker_id = session['workeronline']
    shift = Shift.query.get_or_404(shift_id)

    if shift.status != 'open':
        flash('This shift is no longer open', category='errormsg')
        return redirect(url_for('browse_shifts'))

    existing = Booking.query.filter_by(shift_id=shift_id, worker_id=worker_id).filter(
        Booking.booking_status.in_(['pending', 'confirmed'])
    ).first()
    if existing:
        flash('You have already applied for this shift', category='errormsg')
        return redirect(url_for('browse_shifts'))

    try:
        booking = Booking(shift_id=shift_id, worker_id=worker_id, booking_status='pending')
        db.session.add(booking)
        db.session.commit()
        flash('Application submitted! The facility will review it shortly.', category='feedback')
        return redirect(url_for('my_bookings'))
    except Exception:
        db.session.rollback()
        flash('Error submitting your application', category='errormsg')
        return redirect(url_for('shift_detail', shift_id=shift_id))


@app.get('/worker/my-bookings/')
def my_bookings():
    if session.get('workeronline') is None:
        flash('You must be logged in to view this page', category='errormsg')
        return redirect(url_for('index'))

    worker_id = session['workeronline']
    bookings = Booking.query.filter_by(worker_id=worker_id).order_by(Booking.booked_at.desc()).all()

    upcoming = [b for b in bookings if b.booking_status in ('pending', 'confirmed')]
    completed = [b for b in bookings if b.booking_status == 'completed']
    cancelled = [b for b in bookings if b.booking_status == 'cancelled']

    return render_template(
        'worker/my-bookings.html',
        upcoming=upcoming,
        completed=completed,
        cancelled=cancelled,
    )


@app.get('/worker/profile/')
def worker_profile():
    if session.get('workeronline') is None:
        flash('You must be logged in to view this page', category='errormsg')
        return redirect(url_for('index'))

    worker_id = session['workeronline']
    deets = Worker.query.get(worker_id)

    shifts_done = Booking.query.filter_by(worker_id=worker_id, booking_status='completed').count()
    upcoming_count = Booking.query.filter(
        Booking.worker_id == worker_id,
        Booking.booking_status.in_(['pending', 'confirmed']),
    ).count()

    released_payments = (
        db.session.query(Payment)
        .join(Booking, Payment.booking_id == Booking.booking_id)
        .filter(Booking.worker_id == worker_id, Payment.payment_status == 'released')
        .all()
    )
    total_earned = sum((p.worker_payout for p in released_payments), start=0)

    return render_template(
        'worker/worker-profile.html',
        deets=deets,
        shifts_done=shifts_done,
        upcoming_count=upcoming_count,
        total_earned=total_earned,
    )


@app.post('/worker/profile/bank-details/')
def update_bank_details():
    if session.get('workeronline') is None:
        flash('You must be logged in to do that', category='errormsg')
        return redirect(url_for('index'))

    bank_name = request.form.get('bank_name')
    account_number = request.form.get('bank_account_number')
    account_name = request.form.get('bank_account_name')

    if not all([bank_name, account_number, account_name]):
        flash('All bank detail fields are required', category='errormsg')
        return redirect(url_for('worker_profile'))

    worker = Worker.query.get(session['workeronline'])
    worker.bank_name = bank_name
    worker.bank_account_number = account_number
    worker.bank_account_name = account_name
    db.session.commit()
    flash('Bank details saved', category='feedback')
    return redirect(url_for('worker_profile'))
