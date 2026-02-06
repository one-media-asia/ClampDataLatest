from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
import hashlib
import scrypt

# Monkey patch hashlib.scrypt to use the scrypt package since Python may not have it
if not hasattr(hashlib, 'scrypt'):
    def _scrypt(password, salt, n, r, p, buflen=64, maxmem=0):
        return scrypt.hash(password, salt, N=n, r=r, p=p, buflen=buflen)
    hashlib.scrypt = _scrypt

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///clamping_business.db'

# Load SECRET_KEY from environment. If not set, generate a secure runtime
# fallback and warn the operator. The runtime fallback is suitable for
# development and quick local testing but MUST be replaced in production
# by setting the `SECRET_KEY` environment variable to a persistent secret.
import secrets
env_secret = os.environ.get('SECRET_KEY')
if env_secret:
    app.config['SECRET_KEY'] = env_secret
else:
    # generate a cryptographically secure fallback (rotates on restart)
    fallback_secret = secrets.token_urlsafe(48)
    app.config['SECRET_KEY'] = fallback_secret
    print("WARNING: No SECRET_KEY set in environment. Using a runtime-generated fallback secret.")
    print("Set the environment variable SECRET_KEY to a persistent secret to enable stable sessions and to rotate the key safely.")

db = SQLAlchemy(app)


@app.context_processor
def inject_common():
    # provide current year and whether the logged-in user is admin for templates
    try:
        uid = session.get('user_id')
        is_admin = False
        username = None
        if uid:
            try:
                user = User.query.get(uid)
                is_admin = bool(user and user.is_admin)
                username = user.username if user else None
            except Exception:
                is_admin = False
        return {'current_year': datetime.now().year, 'is_admin': is_admin, 'current_username': username}
    except RuntimeError:
        # session or DB not available during some CLI operations
        return {'current_year': datetime.now().year, 'is_admin': False, 'current_username': None}


def _sqlite_db_path_from_uri(uri: str):
    # support forms: sqlite:///relative.db or sqlite:////absolute/path.db
    if not uri.startswith('sqlite:'):
        return None
    # strip prefix
    path = uri.split(':', 1)[1]
    # remove leading ///
    if path.startswith('///'):
        path = path[3:]
    elif path.startswith('//'):
        path = path[2:]
    if path == ':memory:':
        return None
    return os.path.abspath(path)


def ensure_force_password_column():
    """If using SQLite and the `user` table exists without the
    `force_password_change` column, add it via ALTER TABLE.
    This is non-destructive and idempotent.
    """
    uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    candidate_paths = []
    # First, try the path from the SQLALCHEMY URI
    db_path = _sqlite_db_path_from_uri(uri)
    if db_path:
        candidate_paths.append(db_path)
    # Next, try the app instance DB (Flask's instance path)
    try:
        inst_path = os.path.join(app.instance_path or '', 'clamping_business.db')
        candidate_paths.append(inst_path)
    except Exception:
        pass
    # Finally, try current working directory DB
    candidate_paths.append(os.path.abspath('clamping_business.db'))

    # We'll ensure both `user.force_password_change` and `clamp_data.amount_paid` exist
    required = [
        ("user", "force_password_change", "INTEGER", "0"),
        ("clamp_data", "amount_paid", "REAL", "0.0"),
        ("clamp_data", "image_filename", "TEXT", "''"),
        ("clamp_data", "time_called", "TEXT", "''"),
        ("clamp_data", "car_type", "TEXT", "''"),
        ("clamp_data", "color", "TEXT", "''"),
        ("clamp_data", "clamp_ref", "TEXT", "''"),
    ]
    import sqlite3
    for path in candidate_paths:
        if not path or not os.path.exists(path):
            continue
        try:
            conn = sqlite3.connect(path)
            migrated_any = False
            for table, col, coltype, default in required:
                try:
                    cur = conn.execute(f"PRAGMA table_info('{table}')")
                    cols = [r[1] for r in cur.fetchall()]
                except sqlite3.OperationalError:
                    # table doesn't exist in this DB, skip
                    continue
                if col in cols:
                    continue
                # Add the column
                sql = f"ALTER TABLE {table} ADD COLUMN {col} {coltype} DEFAULT {default}"
                conn.execute(sql)
                migrated_any = True
                print(f"Migration: added column {col} to {table} in {path}")
            if migrated_any:
                conn.commit()
            conn.close()
            if migrated_any:
                return
        except Exception as e:
            try:
                conn.close()
            except Exception:
                pass
            print(f'Migration warning for {path}: could not ensure schema columns: {e}')
    # nothing migrated

# Database Model
class ClampData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(200), nullable=False)
    registration = db.Column(db.String(100))
    clamp_date = db.Column(db.Date, nullable=False)
    time_in = db.Column(db.Time, nullable=False)
    time_called = db.Column(db.Time)
    time_released = db.Column(db.Time)
    car_type = db.Column(db.String(100))
    color = db.Column(db.String(100))
    clamp_ref = db.Column(db.String(200))
    image_filename = db.Column(db.String(300))
    offense = db.Column(db.String(300), nullable=False)
    payment_status = db.Column(db.String(50), default='Processing')  # Paid, Not Paid, Processing
    amount_paid = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ClampData {self.id}>'

# Appeals Model
class Appeal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    clamp_id = db.Column(db.Integer, db.ForeignKey('clamp_data.id'), nullable=False)
    clamp = db.relationship('ClampData', backref='appeals')
    appeal_date = db.Column(db.Date, nullable=False, default=datetime.today)
    appeal_reason = db.Column(db.Text, nullable=False)
    appeal_status = db.Column(db.String(50), default='Pending')  # Pending, Approved, Rejected
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Appeal {self.id}>'


# Simple user model for authentication
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    force_password_change = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('user_id'):
            return redirect(url_for('login', next=request.path))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        uid = session.get('user_id')
        if not uid:
            return redirect(url_for('login', next=request.path))
        user = User.query.get(uid)
        # If the user is not found or not an admin, show a friendly access denied page
        if not user or not user.is_admin:
            # Provide a helpful message and HTTP 403 status
            message = 'Admin access required to view this page.'
            return render_template('access_denied.html', message=message), 403
        return f(*args, **kwargs)
    return decorated


# Enforce login for all routes except a small whitelist (login, static files, service worker)
# @app.before_request
# def require_login():
#     # endpoints that may be accessed without authentication
#     whitelist = {'login', 'static', 'service_worker'}
#     # If endpoint is None (can happen) allow to proceed (Flask will handle 404)
#     ep = request.endpoint
#     if not ep:
#         return
#     # allow whitelisted endpoints
#     if ep.split('.')[-1] in whitelist:
#         return
#     # allow if user is logged in
#     if session.get('user_id'):
#         return
#     # otherwise redirect to login
#     return redirect(url_for('login', next=request.path))

# Routes
@app.route('/')
def index():
    clamps = ClampData.query.all()
    # include users for admin tab rendering so admins can manage users from the dashboard
    try:
        users = User.query.order_by(User.created_at.desc()).all()
    except Exception:
        users = []
    return render_template('index.html', clamps=clamps, users=users)


# Compatibility routes referenced by templates
@app.route('/dashboard')
def dashboard():
    clamps = ClampData.query.all()
    return render_template('dashboard.html', clamps=clamps)


@app.route('/clamp_form')
@app.route('/clamp-form')
def clamp_form():
    # Render the clamp form for adding a new clamp (edit=False)
    return render_template('clamp_form.html', edit=False)


@app.route('/clamp_list')
@app.route('/clamp-list')
def clamp_list():
    clamps = ClampData.query.all()
    return render_template('clamp_list.html', clamps=clamps)

@app.route('/add-clamp', methods=['POST'])
def add_clamp():
    try:
        # Create new clamp record with extra fields
        new_clamp = ClampData(
            location=request.form['location'],
            registration=request.form.get('registration',''),
            clamp_date=datetime.strptime(request.form['clamp_date'], '%Y-%m-%d').date(),
            time_in=datetime.strptime(request.form['time_in'], '%H:%M').time(),
            time_called=datetime.strptime(request.form['time_called'], '%H:%M').time() if request.form.get('time_called') else None,
            time_released=datetime.strptime(request.form['time_released'], '%H:%M').time() if request.form.get('time_released') else None,
            offense=request.form['offense'],
            payment_status=request.form['payment_status'],
            car_type=request.form.get('car_type',''),
            color=request.form.get('color',''),
            clamp_ref=request.form.get('clamp_ref','')
        )
        # optional amount_paid
        try:
            amt = request.form.get('amount_paid')
            if amt is not None and amt != '':
                new_clamp.amount_paid = float(amt)
        except Exception:
            pass
        # handle image upload
        image = request.files.get('image')
        if image and image.filename:
            upload_folder = os.path.join(app.root_path, 'static', 'images', 'uploads')
            os.makedirs(upload_folder, exist_ok=True)
            fname = secure_filename(image.filename)
            timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S%f')
            saved_name = f"{timestamp}_{fname}"
            path = os.path.join(upload_folder, saved_name)
            image.save(path)
            new_clamp.image_filename = os.path.join('images', 'uploads', saved_name)
        db.session.add(new_clamp)
        db.session.commit()
        flash('Clamp data added successfully!', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        # If AJAX caller, return JSON error
        xhr = request.headers.get('X-Requested-With','')
        accept = request.headers.get('Accept','')
        if 'application/json' in accept or xhr == 'XMLHttpRequest':
            return jsonify({'error': str(e)}), 400
    
    return redirect(url_for('index'))

@app.route('/delete-clamp/<int:id>')
@admin_required
def delete_clamp(id):
    try:
        clamp = ClampData.query.get_or_404(id)
        # Prevent deleting a clamp that has associated appeals to avoid foreign-key integrity errors.
        if getattr(clamp, 'appeals', None):
            if len(clamp.appeals) > 0:
                flash('Cannot delete clamp: there are appeals linked to this record. Delete appeals first.', 'error')
                return redirect(url_for('index'))
        db.session.delete(clamp)
        db.session.commit()
        flash('Clamp data deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    
    return redirect(url_for('index'))

@app.route('/edit-clamp/<int:id>', methods=['GET'])
def edit_clamp_form(id):
    clamp = ClampData.query.get_or_404(id)
    return render_template('clamp_form.html', edit=True, clamp=clamp)


@app.route('/edit-clamp/<int:id>', methods=['POST'])
@admin_required
def edit_clamp(id):
    try:
        clamp = ClampData.query.get_or_404(id)
        clamp.location = request.form['location']
        clamp.registration = request.form.get('registration','')
        clamp.clamp_date = datetime.strptime(request.form['clamp_date'], '%Y-%m-%d').date()
        clamp.time_in = datetime.strptime(request.form['time_in'], '%H:%M').time()
        clamp.time_called = datetime.strptime(request.form['time_called'], '%H:%M').time() if request.form.get('time_called') else None
        clamp.time_released = datetime.strptime(request.form['time_released'], '%H:%M').time() if request.form.get('time_released') else None
        clamp.car_type = request.form.get('car_type','')
        clamp.color = request.form.get('color','')
        clamp.clamp_ref = request.form.get('clamp_ref','')
        # handle image upload (replace existing)
        image = request.files.get('image')
        if image and image.filename:
            upload_folder = os.path.join(app.root_path, 'static', 'images', 'uploads')
            os.makedirs(upload_folder, exist_ok=True)
            fname = secure_filename(image.filename)
            timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S%f')
            saved_name = f"{timestamp}_{fname}"
            path = os.path.join(upload_folder, saved_name)
            image.save(path)
            # Optionally remove old file
            try:
                if clamp.image_filename:
                    old_path = os.path.join(app.root_path, 'static', clamp.image_filename)
                    if os.path.exists(old_path):
                        os.remove(old_path)
            except Exception:
                pass
            clamp.image_filename = os.path.join('images', 'uploads', saved_name)
        clamp.offense = request.form['offense']
        clamp.payment_status = request.form['payment_status']
        # optional amount_paid update
        try:
            amt = request.form.get('amount_paid')
            if amt is not None and amt != '':
                clamp.amount_paid = float(amt)
        except Exception:
            pass
        db.session.commit()
        flash('Clamp data updated successfully!', 'success')
        # If the client expects JSON (AJAX/modal submit), return the updated clamp as JSON
        accept = request.headers.get('Accept','')
        xhr = request.headers.get('X-Requested-With','')
        if 'application/json' in accept or xhr == 'XMLHttpRequest':
            def time_str_local(t):
                try:
                    return t.strftime('%H:%M') if t else None
                except Exception:
                    return None
            return jsonify({
                'id': clamp.id,
                'location': clamp.location,
                'registration': clamp.registration or '',
                'clamp_date': clamp.clamp_date.strftime('%Y-%m-%d') if clamp.clamp_date else None,
                'time_in': time_str_local(clamp.time_in),
                'time_called': time_str_local(clamp.time_called),
                'time_released': time_str_local(clamp.time_released),
                'car_type': clamp.car_type or '',
                'color': clamp.color or '',
                'clamp_ref': clamp.clamp_ref or '',
                'offense': clamp.offense or '',
                'amount_paid': float(clamp.amount_paid or 0.0),
                'payment_status': clamp.payment_status,
                'image_filename': clamp.image_filename or None,
                'image_url': url_for('static', filename=clamp.image_filename) if clamp.image_filename else None,
            })
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    
    return redirect(url_for('index'))

@app.route('/invoicing')
@admin_required
def invoicing():
    paid_clamps = ClampData.query.filter_by(payment_status='Paid').all()
    total_amount = sum((c.amount_paid or 0.0) for c in paid_clamps)
    return render_template('invoicing.html', paid_clamps=paid_clamps, now=datetime.now(), total_amount=total_amount)


@app.route('/presentation/invoice/<int:id>')
@admin_required
def presentation_invoice(id):
    clamp = ClampData.query.get_or_404(id)
    return render_template('presentation_invoice.html', clamp=clamp, now=datetime.now())


@app.route('/service-worker.js')
def service_worker():
    return send_from_directory('static', 'service-worker.js')

@app.route('/appeals')
@admin_required
def appeals():
    all_appeals = Appeal.query.all()
    return render_template('appeals.html', appeals=all_appeals)

@app.route('/add-appeal', methods=['POST'])
def add_appeal():
    try:
        clamp_id = request.form.get('clamp_id')
        if not clamp_id:
            flash('Please select a clamp record for the appeal.', 'error')
            return redirect(url_for('index'))
        try:
            clamp_id = int(clamp_id)
        except ValueError:
            flash('Invalid clamp id.', 'error')
            return redirect(url_for('index'))

        clamp = ClampData.query.get(clamp_id)
        if not clamp:
            flash('Selected clamp record not found.', 'error')
            return redirect(url_for('index'))

        new_appeal = Appeal(
            clamp_id=clamp_id,
            appeal_reason=request.form.get('appeal_reason', '').strip(),
            appeal_status=request.form.get('appeal_status', 'Pending')
        )
        db.session.add(new_appeal)
        db.session.commit()
        flash('Appeal added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'error')

    return redirect(url_for('appeals'))

@app.route('/delete-appeal/<int:id>')
def delete_appeal(id):
    try:
        appeal = Appeal.query.get_or_404(id)
        db.session.delete(appeal)
        db.session.commit()
        flash('Appeal deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    
    return redirect(url_for('appeals'))

@app.route('/edit-appeal/<int:id>', methods=['POST'])
def edit_appeal(id):
    try:
        appeal = Appeal.query.get_or_404(id)
        appeal.appeal_reason = request.form['appeal_reason']
        appeal.appeal_status = request.form['appeal_status']
        appeal.notes = request.form.get('notes', '')
        db.session.commit()
        flash('Appeal updated successfully!', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    
    return redirect(url_for('appeals'))

@app.route('/api/clamp/<int:id>')
def get_clamp_details(id):
    """Return clamp location and registration as JSON for AJAX calls"""
    clamp = ClampData.query.get(id)
    if not clamp:
        return {'error': 'Clamp not found'}, 404
    # provide a richer JSON payload for client-side features
    def time_str(t):
        try:
            return t.strftime('%H:%M') if t else None
        except Exception:
            return None

    return {
        'id': clamp.id,
        'location': clamp.location,
        'registration': clamp.registration or '',
        'clamp_date': clamp.clamp_date.strftime('%Y-%m-%d') if clamp.clamp_date else None,
        'time_in': time_str(clamp.time_in),
        'offense': clamp.offense or '',
        'time_called': time_str(clamp.time_called),
        'time_released': time_str(clamp.time_released),
        'car_type': clamp.car_type or '',
        'color': clamp.color or '',
        'clamp_ref': clamp.clamp_ref or '',
        'amount_paid': float(clamp.amount_paid or 0.0),
        'payment_status': clamp.payment_status,
        'image_filename': clamp.image_filename or None,
        'image_url': url_for('static', filename=clamp.image_filename) if clamp.image_filename else None,
    }

@app.route('/clamp/<int:id>/appeals')
def clamp_appeals(id):
    """Return JSON list of appeals linked to a clamp."""
    clamp = ClampData.query.get_or_404(id)
    appeals = []
    for a in clamp.appeals:
        appeals.append({
            'id': a.id,
            'appeal_date': a.appeal_date.strftime('%Y-%m-%d') if a.appeal_date else None,
            'appeal_reason': a.appeal_reason,
            'appeal_status': a.appeal_status,
            'notes': a.notes or ''
        })
    return jsonify({'clamp_id': clamp.id, 'appeals': appeals})


@app.route('/delete-clamp-with-appeals/<int:id>', methods=['POST'])
@admin_required
def delete_clamp_with_appeals(id):
    """Delete all appeals for a clamp then delete the clamp itself. Returns JSON for AJAX callers."""
    try:
        clamp = ClampData.query.get_or_404(id)
        # delete appeals first
        Appeal.query.filter_by(clamp_id=clamp.id).delete()
        db.session.delete(clamp)
        db.session.commit()
        # return success JSON for AJAX
        return jsonify({'status': 'ok', 'message': 'Deleted clamp and its appeals', 'id': id})
    except Exception as e:
        db.session.rollback()
        xhr = request.headers.get('X-Requested-With','')
        if request.headers.get('Accept','').find('application/json') != -1 or xhr == 'XMLHttpRequest':
            return jsonify({'error': str(e)}), 400
        flash(f'Error deleting clamp and appeals: {e}', 'error')
        return redirect(url_for('index'))
       


# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Logged in successfully', 'success')
            # force password change flow
            if user.force_password_change:
                return redirect(url_for('change_password'))
            nxt = request.args.get('next') or url_for('index')
            return redirect(nxt)
        flash('Invalid username or password', 'error')
    return render_template('login.html')


@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    user = User.query.get(session.get('user_id'))
    if request.method == 'POST':
        current = request.form.get('current_password')
        newpw = request.form.get('new_password')
        confirm = request.form.get('confirm_password')
        if not user.check_password(current):
            flash('Current password incorrect', 'error')
            return redirect(url_for('change_password'))
        if not newpw or newpw != confirm:
            flash('New passwords do not match', 'error')
            return redirect(url_for('change_password'))
        user.password_hash = generate_password_hash(newpw)
        user.force_password_change = False
        db.session.commit()
        flash('Password changed successfully', 'success')
        return redirect(url_for('index'))
    return render_template('change_password.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out', 'success')
    return redirect(url_for('login'))


@app.route('/users')
@admin_required
def users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('users.html', users=users)


@app.route('/users/add', methods=['POST'])
@admin_required
def add_user():
    username = request.form.get('username')
    password = request.form.get('password')
    is_admin = bool(request.form.get('is_admin'))
    if not username or not password:
        flash('Username and password required', 'error')
        return redirect(url_for('users'))
    if User.query.filter_by(username=username).first():
        flash('User already exists', 'error')
        return redirect(url_for('users'))
    user = User(username=username, password_hash=generate_password_hash(password), is_admin=is_admin) # pyright: ignore[reportCallIssue]
    db.session.add(user)
    db.session.commit()
    flash('User added', 'success')
    return redirect(url_for('users'))


@app.route('/users/delete/<int:id>')
@admin_required
def delete_user(id):
    user = User.query.get_or_404(id)
    if user.username == 'admin':
        flash('Cannot delete default admin', 'error')
        return redirect(url_for('users'))
    db.session.delete(user)
    db.session.commit()
    flash('User deleted', 'success')
    return redirect(url_for('users'))

if __name__ == '__main__':
    with app.app_context():
        # Ensure DB schema is migrated for the new `force_password_change` column
        try:
            ensure_force_password_column()
        except Exception as _:
            # migration issues should not block startup here; they'll be visible in logs
            pass
        db.create_all()
        # create default admin user if missing
        try:
            if not User.query.filter_by(username='admin').first():
                default_pw = os.environ.get('DEFAULT_ADMIN_PASSWORD')
                if default_pw:
                    pw_hash = generate_password_hash(default_pw)
                    force_change = False
                    print('Default admin created with provided DEFAULT_ADMIN_PASSWORD env var')
                else:
                    # fallback to an insecure default but require immediate change on first login
                    pw_hash = generate_password_hash('admin')
                    force_change = True
                    print('Default admin created with fallback password; force_password_change=True')
                admin = User(username='admin', password_hash=pw_hash, is_admin=True, force_password_change=force_change)
                db.session.add(admin)
                db.session.commit()
                if force_change:
                    print('Default admin password is insecure. Set DEFAULT_ADMIN_PASSWORD or change password after first login.')
        except Exception:
            # if migrations or tables are not ready, ignore
            pass
    app.run(debug=True)