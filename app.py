import os
import sqlite3
import bcrypt
import logging
from flask import Flask, render_template, request, redirect, flash, session, url_for
from functools import wraps
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default_secretpass')  # Fallback for development
app.config['SECRET_KEY'] = app.secret_key

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DATABASE = 'db/videogames.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash('Username and password are required.', 'error')
            return render_template('login.html')

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash']):
            session['user_id'] = user['id']
            flash('Logged in successfully.', 'success')
            return redirect('/')
        else:
            flash('Username or password incorrect.', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Session closed successfully.', 'info')
    return redirect('/login')

@app.route('/')
@login_required
def index():
    conn = get_db_connection()
    search_query = request.args.get('q', '')

    if search_query:
        games = conn.execute(
            '''
            SELECT * FROM games
            WHERE LOWER(title) LIKE ?
               OR LOWER(genre) LIKE ?
               OR LOWER(platform) LIKE ?
            ''',
            tuple(['%' + search_query.lower() + '%'] * 3)
        ).fetchall()
    else:
        games = conn.execute('SELECT * FROM games').fetchall()

    consoles = conn.execute('SELECT * FROM consoles').fetchall()
    conn.close()
    return render_template('index.html', games=games, consoles=consoles, query=search_query)

@app.route('/games/<platform>')
@login_required
def games_by_platform(platform):
    conn = get_db_connection()
    page = request.args.get('page', 1, type=int)
    per_page = 50
    offset = (page - 1) * per_page
    normalized_platform = platform.replace(' ', '').lower()

    games = conn.execute(
        '''
        SELECT * FROM games
        WHERE platform_normalized = ?
        LIMIT ? OFFSET ?
        ''',
        (normalized_platform, per_page, offset)
    ).fetchall()

    total = conn.execute(
        'SELECT COUNT(*) FROM games WHERE platform_normalized = ?',
        (normalized_platform,)
    ).fetchone()[0]

    conn.close()
    return render_template('index.html', games=games, consoles=[], query='', platform=platform,
                           page=page, per_page=per_page, total=total)

@app.route('/consoles/<model>')
@login_required
def console_by_model(model):
    conn = get_db_connection()
    page = request.args.get('page', 1, type=int)
    per_page = 50
    offset = (page - 1) * per_page
    normalized_model = model.replace(' ', '').lower()

    consoles = conn.execute(
        '''
        SELECT * FROM consoles
        WHERE model_normalized = ?
        LIMIT ? OFFSET ?
        ''',
        (normalized_model, per_page, offset)
    ).fetchall()

    total = conn.execute(
        'SELECT COUNT(*) FROM consoles WHERE model_normalized = ?',
        (normalized_model,)
    ).fetchone()[0]

    conn.close()
    return render_template('index.html', games=[], consoles=consoles, query='', model=model,
                           page=page, per_page=per_page, total=total)

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_game():
    if request.method == 'POST':
        title = request.form.get('title')
        release_date = request.form.get('release_date')
        manufacturer = request.form.get('manufacturer')
        description = request.form.get('description')
        genre = request.form.get('genre')
        platform = request.form.get('platform')
        score = request.form.get('score')
        complete_in_box = request.form.get('complete_in_box') == 'on'
        condition = request.form.get('condition')
        inventory = request.form.get('inventory')
        sealed = request.form.get('sealed') == 'on'

        # Validation
        if not all([title, release_date, manufacturer, genre, platform, score, condition, inventory]):
            flash('All fields are required.', 'error')
            return redirect(url_for('index'))

        try:
            score = int(score)
            inventory = int(inventory)
            if not (0 <= score <= 10):
                raise ValueError("Score must be between 0 and 10.")
            if inventory < 0:
                raise ValueError("Inventory cannot be negative.")
        except ValueError as e:
            flash(str(e), 'error')
            return redirect(url_for('index'))

        platform_normalized = platform.replace(' ', '').lower()
        conn = get_db_connection()
        try:
            conn.execute('''
                INSERT INTO games (
                    title, release_date, manufacturer, description, genre,
                    platform, platform_normalized, score, complete_in_box,
                    condition, inventory, sealed
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (title, release_date, manufacturer, description, genre, platform, platform_normalized,
                  score, complete_in_box, condition, inventory, sealed))
            conn.commit()
            flash('Juego añadido exitosamente!', 'success')
            return redirect(url_for('index'))
        except sqlite3.Error as e:
            logger.error(f"Error adding game: {e}")
            flash(f'Error al añadir juego: {e}', 'error')
            return redirect(url_for('index'))
        finally:
            conn.close()
    return redirect(url_for('index'))  # Redirect to index where modal forms reside

@app.route('/add_console', methods=['GET', 'POST'])
@login_required
def add_console():
    if request.method == 'POST':
        name = request.form.get('name')
        model = request.form.get('model')
        release_date = request.form.get('release_date')
        manufacturer = request.form.get('manufacturer')
        serial_number_box = request.form.get('serial_number_box')
        serial_number_console = request.form.get('serial_number_console')
        complete_in_box = request.form.get('complete_in_box') == 'on'
        condition = request.form.get('condition')
        inventory = request.form.get('inventory')
        sealed = request.form.get('sealed') == 'on'

        # Validation
        if not all([name, model, release_date, manufacturer, serial_number_box, serial_number_console, condition, inventory]):
            flash('All fields are required.', 'error')
            return redirect(url_for('index'))

        try:
            inventory = int(inventory)
            if inventory < 0:
                raise ValueError("Inventory cannot be negative.")
        except ValueError as e:
            flash(str(e), 'error')
            return redirect(url_for('index'))

        model_normalized = model.replace(' ', '').lower()
        conn = get_db_connection()
        try:
            existing = conn.execute(
                'SELECT id FROM consoles WHERE serial_number_console = ?',
                (serial_number_console,)
            ).fetchone()

            if existing:
                flash(f'Error: Ya existe una consola con el número de serie "{serial_number_console}".', 'error')
                return redirect(url_for('index'))

            conn.execute('''
                INSERT INTO consoles (
                    name, release_date, manufacturer, serial_number_box,
                    serial_number_console, complete_in_box, condition,
                    inventory, sealed, model, model_normalized
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (name, release_date, manufacturer, serial_number_box, serial_number_console,
                  complete_in_box, condition, inventory, sealed, model, model_normalized))
            conn.commit()
            flash('Consola añadida exitosamente!', 'success')
            return redirect(url_for('index'))
        except sqlite3.Error as e:
            logger.error(f"Error adding console: {e}")
            flash(f'Error al añadir consola: {e}', 'error')
            return redirect(url_for('index'))
        finally:
            conn.close()
    return redirect(url_for('index'))  # Redirect to index where modal forms reside

@app.route('/delete/<int:game_id>', methods=['POST'])
def delete_game(game_id):
    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM games WHERE id = ?', (game_id,))
        conn.commit()
        flash('Juego eliminado exitosamente!', 'success')
    except sqlite3.Error as e:
        logger.error(f"Error deleting game: {e}")
        flash(f'Error al eliminar juego: {e}', 'error')
    finally:
        conn.close()
    return redirect('/')

@app.route('/delete_console/<int:console_id>', methods=['POST'])
def delete_console(console_id):
    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM consoles WHERE id = ?', (console_id,))
        conn.commit()
        flash('Consola eliminada exitosamente!', 'success')
    except sqlite3.Error as e:
        logger.error(f"Error deleting console: {e}")
        flash(f'Error al eliminar consola: {e}', 'error')
    finally:
        conn.close()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
