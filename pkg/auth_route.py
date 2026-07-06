import os
import secrets
from flask import render_template, request, redirect, flash, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash

from pkg import app
from pkg.models import db, State, Profession, Facility, Worker

UPLOAD_FOLDER = 'pkg/static/uploads/'


def _save_upload(fileobj):
    if not fileobj or not fileobj.filename:
        return None
    name, extension = os.path.splitext(fileobj.filename)
    newname = secrets.token_hex(10) + extension
    fileobj.save(UPLOAD_FOLDER + newname)
    return newname


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/register/', methods=['GET', 'POST'])
def register():
    reg_type = request.values.get('type', 'worker')

    if request.method == 'GET':
        states = State.query.order_by(State.state_name).all()
        if reg_type == 'facility':
            return render_template('auth/register-facility.html', states=states)
        else:
            professions = Profession.query.order_by(Profession.profession_name).all()
            return render_template('auth/register-worker.html', states=states, professions=professions)

    # POST
    if reg_type == 'facility':
        facility_name = request.form.get('facility_name')
        state_id = request.form.get('state')
        city = request.form.get('city')
        address = request.form.get('address')
        contact_phone = request.form.get('contact_phone')
        contact_email = request.form.get('contact_email')
        plan = request.form.get('plan')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        cac_file = request.files.get('cac_document')
        operating_licence_file = request.files.get('operating_licence_document')

        if not all([facility_name, state_id, city, address, contact_phone, contact_email, password]):
            flash('All required fields must be filled', category='errormsg')
            return redirect(url_for('register', type='facility'))
        elif password != confirm_password:
            flash('The two passwords must match', category='errormsg')
            return redirect(url_for('register', type='facility'))
        elif not cac_file or not operating_licence_file:
            flash('Both verification documents are required', category='errormsg')
            return redirect(url_for('register', type='facility'))

        state = State.query.get(state_id)
        if not state:
            flash('Invalid state selected', category='errormsg')
            return redirect(url_for('register', type='facility'))

        hashed = generate_password_hash(password)
        try:
            facility = Facility(
                state_id=state.state_id,
                facility_name=facility_name,
                facility_address=address,
                city=city,
                contact_email=contact_email,
                contact_phone=contact_phone,
                password=hashed,
                plan=plan or 'basic',
                cac_document=_save_upload(cac_file),
                operating_licence_document=_save_upload(operating_licence_file),
                status='pending',
            )
            db.session.add(facility)
            db.session.commit()
            flash('Facility account submitted! Our team will review your documents within 24 hours.', category='feedback')
            return redirect(url_for('index'))
        except Exception:
            db.session.rollback()
            flash('Error creating account, choose another email', category='errormsg')
            return redirect(url_for('register', type='facility'))

    else:  # worker
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email_address = request.form.get('email_address')
        phone_number = request.form.get('phone_number')
        state_id = request.form.get('state')
        profession_id = request.form.get('profession')
        licence_number = request.form.get('licence_number')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        licence_file = request.files.get('licence_document')
        qualification_file = request.files.get('qualification_document')
        id_file = request.files.get('id_document')
        passport_file = request.files.get('passport_photo')

        if not all([first_name, last_name, email_address, phone_number, state_id, profession_id, password]):
            flash('All required fields must be filled', category='errormsg')
            return redirect(url_for('register', type='worker'))
        elif password != confirm_password:
            flash('The two passwords must match', category='errormsg')
            return redirect(url_for('register', type='worker'))
        elif not all([licence_file, qualification_file, id_file, passport_file]):
            flash('All verification documents are required', category='errormsg')
            return redirect(url_for('register', type='worker'))

        state = State.query.get(state_id)
        profession = Profession.query.get(profession_id)
        if not state or not profession:
            flash('Invalid state or profession selected', category='errormsg')
            return redirect(url_for('register', type='worker'))

        hashed = generate_password_hash(password)
        try:
            worker = Worker(
                profession_id=profession.profession_id,
                state_id=state.state_id,
                first_name=first_name,
                last_name=last_name,
                email_address=email_address,
                phone_number=phone_number,
                licence_number=licence_number,
                password=hashed,
                licence_document=_save_upload(licence_file),
                qualification_document=_save_upload(qualification_file),
                id_document=_save_upload(id_file),
                passport_photo=_save_upload(passport_file),
                status='pending',
            )
            db.session.add(worker)
            db.session.commit()
            flash('Worker account submitted! Our team will review your documents within 24 hours.', category='feedback')
            return redirect(url_for('index'))
        except Exception:
            db.session.rollback()
            flash('Error creating account, choose another email', category='errormsg')
            return redirect(url_for('register', type='worker'))


@app.route('/login/', methods=['POST'])
def login():
    role = request.form.get('role')
    email = request.form.get('email')
    password = request.form.get('password')

    if role == 'facility':
        acct = Facility.query.filter_by(contact_email=email).first()
        if not acct or not check_password_hash(acct.password, password):
            flash('Invalid email or password', category='errormsg')
            return redirect(url_for('index'))
        if acct.status == 'pending':
            flash('Your facility account is still under review. We will notify you once approved.', category='errormsg')
            return redirect(url_for('index'))
        if acct.status != 'active':
            flash('Your facility account is not active. Please contact support.', category='errormsg')
            return redirect(url_for('index'))
        session['facilityonline'] = acct.facility_id
        return redirect(url_for('facility_dashboard'))

    else:  # worker
        acct = Worker.query.filter_by(email_address=email).first()
        if not acct or not check_password_hash(acct.password, password):
            flash('Invalid email or password', category='errormsg')
            return redirect(url_for('index'))
        if acct.status == 'pending':
            flash('Your account is still under review. We will notify you once approved.', category='errormsg')
            return redirect(url_for('index'))
        if acct.status != 'active':
            flash('Your account is not active. Please contact support.', category='errormsg')
            return redirect(url_for('index'))
        session['workeronline'] = acct.worker_id
        return redirect(url_for('worker_dashboard'))


@app.get('/facility/logout/')
def facility_logout():
    if session.get('facilityonline'):
        session.pop('facilityonline', None)
        session.clear()
    return redirect(url_for('index'))


@app.get('/worker/logout/')
def worker_logout():
    if session.get('workeronline'):
        session.pop('workeronline', None)
        session.clear()
    return redirect(url_for('index'))
