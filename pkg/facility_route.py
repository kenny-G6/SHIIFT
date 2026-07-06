import secrets
from datetime import datetime
from decimal import Decimal

import requests
from flask import render_template, request, redirect, flash, session, url_for

from pkg import app
from pkg.models import db, Facility, Profession, Shift, Booking, Payment

PAYSTACK_BASE_URL = 'https://api.paystack.co'


def _paystack_headers():
    return {
        'Authorization': f"Bearer {app.config['PAYSTACK_SECRET_KEY']}",
        'Content-Type': 'application/json',
    }


@app.get('/facility/dashboard/')
def facility_dashboard():
    if session.get('facilityonline') is None:
        flash('You must be logged in to view this page', category='errormsg')
        return redirect(url_for('index'))
    deets = Facility.query.get(session['facilityonline'])
    recent_shifts = (
        Shift.query.filter_by(facility_id=session['facilityonline'])
        .order_by(Shift.shift_date.desc())
        .limit(5)
        .all()
    )
    open_count = Shift.query.filter_by(facility_id=session['facilityonline'], status='open').count()
    filled_count = Shift.query.filter_by(facility_id=session['facilityonline'], status='filled').count()
    return render_template(
        'facility/facility-dashboard.html',
        deets=deets,
        recent_shifts=recent_shifts,
        open_count=open_count,
        filled_count=filled_count,
    )


@app.route('/facility/post-shift/', methods=['GET', 'POST'])
def post_shift():
    if session.get('facilityonline') is None:
        flash('You must be logged in to post a shift', category='errormsg')
        return redirect(url_for('index'))

    if request.method == 'GET':
        professions = Profession.query.order_by(Profession.profession_name).all()
        return render_template('facility/post-shift.html', professions=professions)

    profession_id = request.form.get('role_needed')
    shift_date = request.form.get('shift_date')
    start_time = request.form.get('start_time')
    end_time = request.form.get('end_time')
    pay_rate = request.form.get('pay_rate')

    if not all([profession_id, shift_date, start_time, end_time, pay_rate]):
        flash('All fields are required', category='errormsg')
        return redirect(url_for('post_shift'))

    profession = Profession.query.get(profession_id)
    if not profession:
        flash('Invalid role selected', category='errormsg')
        return redirect(url_for('post_shift'))

    try:
        shift = Shift(
            facility_id=session['facilityonline'],
            profession_id=profession.profession_id,
            role_needed=profession.profession_name,
            shift_date=datetime.strptime(shift_date, '%Y-%m-%d').date(),
            start_time=datetime.strptime(start_time, '%H:%M').time(),
            end_time=datetime.strptime(end_time, '%H:%M').time(),
            pay_rate=pay_rate,
        )
        db.session.add(shift)
        db.session.commit()
        flash('Shift posted successfully!', category='feedback')
        return redirect(url_for('manage_shifts'))
    except Exception:
        db.session.rollback()
        flash('Error posting shift, please check your details', category='errormsg')
        return redirect(url_for('post_shift'))


@app.get('/facility/manage-shifts/')
def manage_shifts():
    if session.get('facilityonline') is None:
        flash('You must be logged in to view this page', category='errormsg')
        return redirect(url_for('index'))

    shifts = Shift.query.filter_by(facility_id=session['facilityonline']).order_by(Shift.shift_date.desc()).all()

    counts = {
        'all': len(shifts),
        'open': sum(1 for s in shifts if s.status == 'open'),
        'filled': sum(1 for s in shifts if s.status == 'filled'),
        'completed': sum(1 for s in shifts if s.status == 'completed'),
        'cancelled': sum(1 for s in shifts if s.status == 'cancelled'),
    }
    return render_template('facility/manage-shifts.html', shifts=shifts, counts=counts)


@app.post('/facility/shift/<int:shift_id>/cancel/')
def cancel_shift(shift_id):
    if session.get('facilityonline') is None:
        flash('You must be logged in to do that', category='errormsg')
        return redirect(url_for('index'))

    shift = Shift.query.get_or_404(shift_id)
    if shift.facility_id != session['facilityonline']:
        flash('This shift does not belong to you', category='errormsg')
        return redirect(url_for('manage_shifts'))

    # If a confirmed booking on this shift already has money held in escrow, refund it via Paystack first
    confirmed_booking = Booking.query.filter_by(shift_id=shift_id, booking_status='confirmed').first()
    if confirmed_booking and confirmed_booking.payment and confirmed_booking.payment.payment_status == 'held':
        payment = confirmed_booking.payment
        try:
            response = requests.post(
                f'{PAYSTACK_BASE_URL}/refund',
                headers=_paystack_headers(),
                json={'transaction': payment.paystack_reference},
            )
            data = response.json()
        except Exception:
            flash('Could not reach Paystack to process the refund. Please try again.', category='errormsg')
            return redirect(url_for('manage_shifts'))

        if not data.get('status'):
            flash('Refund failed: ' + data.get('message', 'unknown error'), category='errormsg')
            return redirect(url_for('manage_shifts'))

        payment.payment_status = 'refunded'
        payment.refunded_at = datetime.utcnow()
        confirmed_booking.booking_status = 'cancelled'

    shift.status = 'cancelled'
    db.session.commit()
    flash('Shift cancelled', category='feedback')
    return redirect(url_for('manage_shifts'))


@app.get('/facility/shift/<int:shift_id>/applicants/')
def shift_applicants(shift_id):
    if session.get('facilityonline') is None:
        flash('You must be logged in to view this page', category='errormsg')
        return redirect(url_for('index'))

    shift = Shift.query.get_or_404(shift_id)
    if shift.facility_id != session['facilityonline']:
        flash('This shift does not belong to you', category='errormsg')
        return redirect(url_for('manage_shifts'))

    applicants = Booking.query.filter_by(shift_id=shift_id, booking_status='pending').order_by(Booking.booked_at).all()
    return render_template('facility/shift-applicants.html', shift=shift, applicants=applicants)


@app.post('/facility/booking/<int:booking_id>/approve/')
def approve_booking(booking_id):
    if session.get('facilityonline') is None:
        flash('You must be logged in to do that', category='errormsg')
        return redirect(url_for('index'))

    booking = Booking.query.get_or_404(booking_id)
    shift = booking.shift
    if shift.facility_id != session['facilityonline']:
        flash('This booking does not belong to you', category='errormsg')
        return redirect(url_for('manage_shifts'))

    booking.booking_status = 'confirmed'
    shift.status = 'filled'

    # Auto-reject every other pending applicant for this shift
    other_pending = Booking.query.filter(
        Booking.shift_id == shift.shift_id,
        Booking.booking_id != booking.booking_id,
        Booking.booking_status == 'pending',
    ).all()
    for other in other_pending:
        other.booking_status = 'cancelled'

    # Create the escrow payment record now — worker keeps their full quoted rate,
    # the platform commission is added on top of what the facility pays.
    worker_payout = shift.total_pay
    commission = worker_payout * Decimal(str(app.config['COMMISSION_RATE']))
    amount_held = worker_payout + commission

    payment = Payment(
        booking_id=booking.booking_id,
        amount_held=amount_held,
        commission=commission,
        worker_payout=worker_payout,
        payment_method='paystack',
        payment_status='pending',
    )
    db.session.add(payment)
    db.session.commit()

    flash('Applicant approved! Please complete payment to confirm this booking.', category='feedback')
    return redirect(url_for('facility_payment', booking_id=booking.booking_id))


@app.post('/facility/booking/<int:booking_id>/reject/')
def reject_booking(booking_id):
    if session.get('facilityonline') is None:
        flash('You must be logged in to do that', category='errormsg')
        return redirect(url_for('index'))

    booking = Booking.query.get_or_404(booking_id)
    shift = booking.shift
    if shift.facility_id != session['facilityonline']:
        flash('This booking does not belong to you', category='errormsg')
        return redirect(url_for('manage_shifts'))

    booking.booking_status = 'cancelled'
    db.session.commit()
    flash('Applicant rejected', category='feedback')
    return redirect(url_for('shift_applicants', shift_id=shift.shift_id))


@app.get('/facility/payment/<int:booking_id>/')
def facility_payment(booking_id):
    if session.get('facilityonline') is None:
        flash('You must be logged in to view this page', category='errormsg')
        return redirect(url_for('index'))

    booking = Booking.query.get_or_404(booking_id)
    shift = booking.shift
    if shift.facility_id != session['facilityonline']:
        flash('This booking does not belong to you', category='errormsg')
        return redirect(url_for('manage_shifts'))

    payment = booking.payment
    if not payment:
        flash('No payment record found for this booking', category='errormsg')
        return redirect(url_for('manage_shifts'))

    return render_template('facility/facility-payment.html', booking=booking, shift=shift, payment=payment)


@app.post('/facility/payment/<int:booking_id>/initialize/')
def initialize_payment(booking_id):
    if session.get('facilityonline') is None:
        flash('You must be logged in to do that', category='errormsg')
        return redirect(url_for('index'))

    booking = Booking.query.get_or_404(booking_id)
    shift = booking.shift
    if shift.facility_id != session['facilityonline']:
        flash('This booking does not belong to you', category='errormsg')
        return redirect(url_for('manage_shifts'))

    payment = booking.payment
    if not payment or payment.payment_status != 'pending':
        flash('This payment cannot be initialized', category='errormsg')
        return redirect(url_for('manage_shifts'))

    facility = Facility.query.get(session['facilityonline'])
    reference = f"shiift-{payment.payment_id}-{secrets.token_hex(6)}"
    amount_kobo = int(payment.amount_held * 100)

    try:
        response = requests.post(
            f'{PAYSTACK_BASE_URL}/transaction/initialize',
            headers=_paystack_headers(),
            json={
                'email': facility.contact_email,
                'amount': amount_kobo,
                'reference': reference,
                'callback_url': url_for('verify_payment', _external=True),
            },
        )
        data = response.json()
    except Exception:
        flash('Could not reach Paystack. Please try again.', category='errormsg')
        return redirect(url_for('facility_payment', booking_id=booking_id))

    if not data.get('status'):
        flash('Payment initialization failed: ' + data.get('message', 'unknown error'), category='errormsg')
        return redirect(url_for('facility_payment', booking_id=booking_id))

    payment.paystack_reference = reference
    db.session.commit()

    return redirect(data['data']['authorization_url'])


@app.get('/facility/payment/verify/')
def verify_payment():
    reference = request.args.get('reference') or request.args.get('trxref')
    if not reference:
        flash('Missing payment reference', category='errormsg')
        return redirect(url_for('manage_shifts'))

    payment = Payment.query.filter_by(paystack_reference=reference).first()
    if not payment:
        flash('Payment record not found', category='errormsg')
        return redirect(url_for('manage_shifts'))

    try:
        response = requests.get(
            f'{PAYSTACK_BASE_URL}/transaction/verify/{reference}',
            headers=_paystack_headers(),
        )
        data = response.json()
    except Exception:
        flash('Could not verify payment with Paystack', category='errormsg')
        return redirect(url_for('facility_payment', booking_id=payment.booking_id))

    if data.get('status') and data['data']['status'] == 'success':
        payment.payment_status = 'held'
        payment.paid_at = datetime.utcnow()
        db.session.commit()
        flash('Payment successful! Funds are held in escrow.', category='feedback')
    else:
        flash('Payment was not successful. Please try again.', category='errormsg')

    return redirect(url_for('manage_shifts'))


@app.post('/facility/booking/<int:booking_id>/complete/')
def mark_complete(booking_id):
    if session.get('facilityonline') is None:
        flash('You must be logged in to do that', category='errormsg')
        return redirect(url_for('index'))

    booking = Booking.query.get_or_404(booking_id)
    shift = booking.shift
    if shift.facility_id != session['facilityonline']:
        flash('This booking does not belong to you', category='errormsg')
        return redirect(url_for('manage_shifts'))

    if booking.booking_status != 'confirmed':
        flash('Only confirmed bookings can be marked complete', category='errormsg')
        return redirect(url_for('manage_shifts'))

    booking.booking_status = 'completed'
    shift.status = 'completed'
    db.session.commit()
    flash('Shift marked as completed', category='feedback')
    return redirect(url_for('manage_shifts'))
