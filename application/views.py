from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_required, login_user, logout_user, current_user
from . import (
    login_manager,
    Session,
)
from application.models import (
    User,
    Car,
    Vote,
)
from functools import wraps
from werkzeug.utils import secure_filename
from sqlalchemy import func

main = Blueprint('main', __name__)


def admin_required(view_func):
    @wraps(view_func)
    def decorated_view(*args, **kwargs):
        if current_user.is_authenticated and current_user.role == 'Admin':
            return view_func(*args, **kwargs)
        else:
            flash('You do not have permission to access this page.', 'error')
            return redirect(url_for('main.index'))
    return decorated_view


@main.route('/')
def index():
    return render_template('index.html')


@main.route('/register', methods=['POST'])
def register():
    try:
        sessiondb = Session()
        data = request.form
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        role = 'User'

        # Check if user with the provided email already exists
        existing_user = sessiondb.query(User).filter(
            User.email == email,
        ).first()

        if existing_user:
            flash('User with the provided email already exists.', 'error')

        new_user = User(name=name, email=email, password=password, role=role, account_status='Pending')
        sessiondb.add(new_user)
        try:
            sessiondb.commit()
        except Exception as e:
            sessiondb.rollback()
            sessiondb.close()
            flash('Error creating user.', 'error')

        flash('Your account has been created. Please wait for an admin to approve your account.', 'success')

    except Exception as e:
        flash('Error creating user.', 'error')
    return redirect(url_for('main.index'))


@main.route('/login', methods=['POST'])
def login():
    try:
        sessiondb = Session()
        data = request.form
        email = data.get('email')
        password = data.get('password')

        # Check if user with the provided email already exists
        existing_user = sessiondb.query(User).filter(
            User.email == email,
            User.password == password,
        ).first()

        if existing_user:
            if existing_user.account_status == 'Approved':
                login_user(existing_user)
                return redirect(url_for('main.cars'))
            else:
                flash('Your account has not been approved yet.', 'error')
        else:
            flash('Invalid email or password.', 'error')
            sessiondb.close()

    except Exception as e:
        flash('Error logging in.', 'error')
    return redirect(url_for('main.index'))


@main.route('/cars')
def cars():
    try:
        sessiondb = Session()

        # Join the Cars and Votes tables to calculate the number of votes for each car
        cars = sessiondb.query(Car, func.count(Vote.id).label('vote_count')) \
            .outerjoin(Vote, Car.id == Vote.car_id) \
            .group_by(Car.id) \
            .order_by(func.count(Vote.id).desc()) \
            .all()

        sessiondb.close()
        return render_template('cars.html', cars=cars)
    except Exception as e:
        print(e)
        flash('Error getting cars.', 'error')
    return redirect(url_for('main.index'))


@main.route('/vote', methods=['POST'])
@login_required
def vote():
    try:
        sessiondb = Session()
        data = request.form
        car_id = data.get('car_id')
        user_id = current_user.id

        # Check if user has already voted for the car
        existing_vote = sessiondb.query(Vote).filter(
            Vote.user_id == user_id,
            Vote.car_id == car_id,
        ).first()

        if existing_vote:
            flash('You have already voted for this car.', 'error')
        else:
            # Check the user's voting limit (20% of total cars)
            total_cars = sessiondb.query(Car).count()
            user_votes = sessiondb.query(Vote).filter(Vote.user_id == user_id).count()

            if user_votes >= (total_cars * 0.2):
                flash('You have reached the maximum number of votes.', 'error')
            else:
                new_vote = Vote(user_id=user_id, car_id=car_id, vote_status='Cast')
                sessiondb.add(new_vote)

                try:
                    sessiondb.commit()
                    flash('Your vote has been cast.', 'success')
                except Exception as e:
                    sessiondb.rollback()
                    flash('Error voting for car.', 'error')
                finally:
                    sessiondb.close()

    except Exception as e:
        flash('Error voting for car.', 'error')
    return redirect(url_for('main.cars'))


@main.route('/admin', methods=['GET', 'POST'])
def admin():
    try:
        if current_user.is_authenticated and current_user.role == 'Admin':
            return redirect(url_for('main.admin_dashboard'))
        if request.method == 'POST':
            sessiondb = Session()
            data = request.form
            email = data.get('email')
            password = data.get('password')

            # Check if user with the provided email already exists
            existing_user = sessiondb.query(User).filter(
                User.email == email,
                User.password == password,
                User.role == 'Admin',
            ).first()

            if existing_user:
                login_user(existing_user)
                return redirect(url_for('main.admin_dashboard'))
            else:
                flash('Invalid email or password.', 'error')
                sessiondb.close()
    except Exception as e:
        flash('Error logging in.', 'error')
    return render_template('admin.html')


@main.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    try:
        sessiondb = Session()
        users = sessiondb.query(User).filter(
            User.role == 'User',
        ).all()
        total_users = len(users)
        total_approved_users = len([user for user in users if user.account_status == 'Approved'])
        total_pending_users = len([user for user in users if user.account_status == 'Pending'])
        unapproved_users = [user for user in users if user.account_status == 'Pending']
        stats = {
            'total_users': total_users,
            'total_approved_users': total_approved_users,
            'total_pending_users': total_pending_users,
        }
        sessiondb.close()
        return render_template('admin_dashboard.html', stats=stats, unapproved_users=unapproved_users)
    except Exception as e:
        print(e)
        flash('Error getting admin dashboard.', 'error')
    return redirect(url_for('main.admin'))


@main.route('/approve_user', methods=['POST'])
@admin_required
def approve_user():
    try:
        sessiondb = Session()
        data = request.form
        user_id = data.get('user_id')
        user = sessiondb.query(User).filter(
            User.id == user_id,
        ).first()
        user.account_status = 'Approved'
        sessiondb.commit()
        sessiondb.close()
        flash('User approved.', 'success')
    except Exception as e:
        print(e)
        flash('Error approving user.', 'error')
    return redirect(url_for('main.admin_dashboard'))


@main.route('/admin/manage_cars')
@admin_required
def manage_cars():
    try:
        sessiondb = Session()
        cars = sessiondb.query(Car).all()
        sessiondb.close()
        return render_template('manage_cars.html', cars=cars)
    except Exception as e:
        print(e)
        flash('Error getting cars.', 'error')
    return redirect(url_for('main.admin_dashboard'))


@main.route('/add_car', methods=['POST'])
@admin_required
def add_car():
    try:
        sessiondb = Session()
        data = request.form
        name = data.get('name')
        description = data.get('description')
        image = request.files.get('image')
        filename = secure_filename(image.filename)
        image.save('application/static/images/' + filename)
        new_car = Car(car_name=name, car_details=description, image_url=filename)
        sessiondb.add(new_car)
        try:
            sessiondb.commit()
        except Exception as e:
            sessiondb.rollback()
            sessiondb.close()
            flash('Error adding car.', 'error')
    except Exception as e:
        print(e)
        flash('Error adding car.', 'error')
    return redirect(url_for('main.manage_cars'))


@main.route('/delete_car', methods=['POST'])
@admin_required
def delete_car():
    try:
        sessiondb = Session()
        data = request.form
        car_id = data.get('car_id')
        car = sessiondb.query(Car).filter(
            Car.id == car_id,
        ).first()
        sessiondb.delete(car)
        sessiondb.commit()
        sessiondb.close()
        flash('Car deleted.', 'success')
    except Exception as e:
        print(e)
        flash('Error deleting car.', 'error')
    return redirect(url_for('main.manage_cars'))


@main.route('/edit_car', methods=['POST'])
@admin_required
def edit_car():
    try:
        sessiondb = Session()
        data = request.form
        car_id = data.get('car_id')
        name = data.get('name')
        description = data.get('description')
        image = request.files.get('image')
        car: Car = sessiondb.query(Car).filter(
            Car.id == car_id,
        ).first()

        if image:
            filename = secure_filename(image.filename)
            image.save('application/static/images/' + filename)
            car.image_url = filename

        car.car_name = name
        car.car_details = description
        try:
            sessiondb.commit()
        except Exception as e:
            sessiondb.rollback()
            flash('Error editing car.', 'error')
        sessiondb.close()
        flash('Car edited.', 'success')
    except Exception as e:
        print(e)
        flash('Error editing car.', 'error')
    return redirect(url_for('main.manage_cars'))


@login_required
@main.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))


@login_manager.user_loader
def load_user(user_id):
    if user_id is not None:
        sessiondb = Session()
        user_id = sessiondb.query(User).get(user_id)
        sessiondb.close()
        return user_id
    return None
