import os
import sqlite3
import bcrypt
import logging
from flask import Flask, render_template, request, redirect, flash, session, url_for, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import  CSRFProtect 
from functools import wraps
from dotenv import load_dotenv
from connection import get_db_connection, get_sqlserver_connection
from auth import User, permission_required, admin_required, editor_required, Role

# Load environment variables
load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default_secretpass')  # Fallback for development
app.config['SECRET_KEY'] = app.secret_key

# Configuration CSRF Protection

csrf = CSRFProtect(app)

# Configuration Rate Limiting

# Función personalizada para rate limiting
def get_limiter_key():
    """Usa sesión en lugar de IP para rate limiting"""
    return session.get('_id', request.remote_addr)

limiter = Limiter(
    app=app,
    key_func=get_limiter_key,  # ← CAMBIADO
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Configuration Flask-Login

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Debes de iniciar sesion para acceder a esta pagina'
login_manager.login_message_category = 'error'

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@login_manager.user_loader
def load_user(user_id):
    """Carga usuario desde la base de datos"""
    conn = get_sqlserver_connection()
    try:
        user_data = conn.execute('SELECT id, username, password_hash, role FROM users WHERE id = ?', (user_id,)).fetchone()
        if user_data:
            return User (
                id = user_data['id'],
                username = user_data['username'],
                password_hash = user_data['password_hash'],
                role = user_data.get('role', 'viewer')  
            )
    except Exception as e:
        logger.error(f"Error loading user: {e}")
    finally:
        conn.close()
    return None

#@app.before_request
#def apply_rate_limiting():
#    """Aplica rate limiting solo a POST /login"""
#    if request.endpoint == 'login' and request.method == 'POST':
#        # Aplicar rate limit de 5 intentos por minuto
#        try:
#            limiter.check()
#        except:
#            pass  # Se maneja en la función login()

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Si ya está autenticado, redirigir a index
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        # Rate limiting solo para POST (intentos de login)
        #try:
        #    limiter.check()
        #except Exception:
        #    flash('Demasiados intentos de login. Espera 1 minuto.', 'error')
        #    return render_template('login.html'), 429
        
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash('Usuario y contraseña son requeridos.', 'error')
            return render_template('login.html')

        conn = get_sqlserver_connection()
        try:
            user_data = conn.execute('SELECT id, username, password_hash, role FROM users WHERE username = ?', (username,)).fetchone()
        finally:
            conn.close()

        if user_data and user_data['password_hash']:
            password_hash = user_data['password_hash']
            if isinstance(password_hash, str):
                password_hash = password_hash.encode('utf-8')
            
            if bcrypt.checkpw(password.encode('utf-8'), password_hash):
                user = User(
                    id=user_data['id'],
                    username=user_data['username'],
                    password_hash=user_data['password_hash'],
                    role=user_data.get('role', 'viewer')
                )
                login_user(user)
                logger.info(f"Usuario {username} inició sesión con rol {user.role}")
                flash(f'Bienvenido {username}!', 'success')
                
                # Redirigir a página solicitada o index
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('index'))
        
        flash('Usuario o contraseña incorrectos.', 'error')
        logger.warning(f"Intento de login fallido para usuario: {username}")
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    username = current_user.username
    logout_user()
    flash(f'Sesion cerrada. Hasta Pronto {username}!', 'info')
    logger.info(f"Usuario {username} cerro la sesion")
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    conn = get_sqlserver_connection()
    search_query = request.args.get('q', '')


    try:
        if search_query:
            games = conn.execute(
                '''
                SELECT * FROM games
                WHERE LOWER(title) LIKE ? OR LOWER(genre) LIKE ? OR LOWER(platform) LIKE ?
                ''',
                tuple(['%' + search_query.lower() + '%'] * 3)
            ).fetchall()
        else:
            games = conn.execute('SELECT * FROM games').fetchall()

        consoles = conn.execute('SELECT * FROM consoles').fetchall()
    finally:
        conn.close()

    return render_template('index.html', games=games, consoles=consoles, query=search_query)

@app.route('/games/<platform>')
@login_required
def games_by_platform(platform):
    conn = get_sqlserver_connection()
    page = request.args.get('page', 1, type=int)
    per_page = 50
    offset = (page - 1) * per_page
    normalized_platform = platform.replace(' ', '').lower()

    try:
        games = conn.execute(
            '''
            SELECT * FROM games
            WHERE platform_normalized = ?
            ORDER BY  id
            OFFSET ? ROWS
            FETCH NEXT ? ROWS ONLY
            ''',
            (normalized_platform, offset, per_page)
        ).fetchall()

        total = conn.execute(
            'SELECT COUNT(*) as count FROM games WHERE platform_normalized = ?',
            (normalized_platform,)
        ).fetchone()['count']

    finally:
        conn.close()

    return render_template('index.html', games=games, consoles=[], query='', platform=platform,
                           page=page, per_page=per_page, total=total)

@app.route('/consoles/<model>')
@login_required
def console_by_model(model):
    conn = get_sqlserver_connection()
    page = request.args.get('page', 1, type=int)
    per_page = 50
    offset = (page - 1) * per_page
    normalized_model = model.replace(' ', '').lower()

    try:
        consoles = conn.execute(
            '''
            SELECT * FROM consoles
            WHERE model_normalized = ?
            ORDER BY id
            OFFSET ? ROWS
            FETCH NEXT ? ROWS ONLY
            ''',
            (normalized_model, offset, per_page)
        ).fetchall()

        total = conn.execute(
            'SELECT COUNT(*) as count FROM consoles WHERE model_normalized = ?',
            (normalized_model,)
        ).fetchone()['count']

    finally:
        conn.close()

    return render_template('index.html', games=[], consoles=consoles, query='', model=model,
                           page=page, per_page=per_page, total=total)

@app.route('/add', methods=['GET', 'POST'])
@login_required
@permission_required('create') # solo admin y editor
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
        conn = get_sqlserver_connection()
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
            logger.info(f"Usuario {current_user.username} agrego juego: {title}")
        except Exception as e:
            logger.error(f"Error adding game: {e}")
            flash(f'Error al añadir juego: {e}', 'error')
        
        finally:
            conn.close()

        return redirect(url_for('index'))
    
    return redirect(url_for('index'))  # Redirect to index where modal forms reside

@app.route('/add_console', methods=['GET', 'POST'])
@login_required
@permission_required('create') # Solo admin y editor
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
        conn = get_sqlserver_connection()
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
            logger.info(f"Usuario {current_user.username} agrego consola: {name} - {model}")
        except Exception as e:
            logger.error(f"Error adding console: {e}")
            flash(f'Error al añadir consola: {e}', 'error')
        
        finally:
            conn.close()

        return redirect(url_for('index'))

    return redirect(url_for('index'))  # Redirect to index where modal forms reside

@app.route('/edit/<int:game_id>', methods=['GET', 'POST'])
@login_required
@permission_required('edit')
def edit_game(game_id):
    conn = get_sqlserver_connection()

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

        if not all ([title, release_date, manufacturer, description, genre, platform, score, complete_in_box, condition, inventory, ]):
            flash('Every field is required', 'error')
            conn.close()
            return redirect(url_for('index'))
        
        try:
            score = int(score)
            inventory = int(inventory)
            if not (0 <= score <=10):
                raise ValueError("Score must be beetwen 1 & 10")
            if inventory < 0:
                raise ValueError("Inventory can't be negative")
        except ValueError as e:
            flash(str(e), 'error')
            conn.close()
            return redirect(url_for('index'))
        
        platform_normalized = platform.replace(' ', '').lower()

        try:
            conn.execute('''
                UPDATE games SET
                    title = ?, release_date = ?, manufacturer = ?, description = ?,
                    genre = ?, platform = ?, platform_normalized = ?, score = ?,
                    complete_in_box = ?, condition = ?, inventory = ?, sealed = ?
                WHERE id = ?
            ''', (title, release_date, manufacturer, description, genre, platform,
                  platform_normalized, score, complete_in_box, condition, inventory,
                  sealed, game_id))
            conn.commit()
            flash('✅ ¡Juego actualizado exitosamente!', 'success')
            logger.info(f"Usuario {current_user.username} edito juego ID: {game_id}")
        except Exception as e:
            logger.error(f"error updating game: {e}")
            flash(f'Error al actualizar juego: {e}', 'error')
        finally:
            conn.close()

        return redirect(url_for('index'))
    
    try: 
        game = conn.execute('SELECT * FROM games WHERE id = ?', (game_id)).fetchone()
    finally:
        conn.close()

    if not game:
        flash('Juego no encontrado', 'error')
        return redirect(url_for('index'))
    
    return render_template('edit_game.html', game=game)

@app.route('/edit_console/<int:console_id>', methods=['GET', 'POST'])
@login_required
@permission_required('edit')
def edit_console(console_id):
    conn = get_sqlserver_connection()
    
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
            flash('Todos los campos son requeridos.', 'error')
            conn.close()
            return redirect(url_for('index'))

        try:
            inventory = int(inventory)
            if inventory < 0:
                raise ValueError("El inventario no puede ser negativo.")
        except ValueError as e:
            flash(str(e), 'error')
            conn.close()
            return redirect(url_for('index'))

        model_normalized = model.replace(' ', '').lower()
        
        try:
            # Verificar que el serial no esté en uso por otra consola
            existing = conn.execute(
                'SELECT id FROM consoles WHERE serial_number_console = ? AND id != ?',
                (serial_number_console, console_id)
            ).fetchone()

            if existing:
                flash(f'❌ Error: Ya existe otra consola con el número de serie "{serial_number_console}".', 'error')
                conn.close()
                return redirect(url_for('index'))

            conn.execute('''
                UPDATE consoles SET
                    name = ?, model = ?, model_normalized = ?, release_date = ?,
                    manufacturer = ?, serial_number_box = ?, serial_number_console = ?,
                    complete_in_box = ?, condition = ?, inventory = ?, sealed = ?
                WHERE id = ?
            ''', (name, model, model_normalized, release_date, manufacturer,
                  serial_number_box, serial_number_console, complete_in_box,
                  condition, inventory, sealed, console_id))
            conn.commit()
            flash('✅ ¡Consola actualizada exitosamente!', 'success')
            logger.info(f"Usuario {current_user.username} editó consola ID: {console_id}")
        except Exception as e:
            logger.error(f"Error updating console: {e}")
            flash(f'❌ Error al actualizar consola: {e}', 'error')
        finally:
            conn.close()
        
        return redirect(url_for('index'))
    
    # GET: Obtener datos de la consola
    try:
        console = conn.execute('SELECT * FROM consoles WHERE id = ?', (console_id,)).fetchone()
    finally:
        conn.close()
    
    if not console:
        flash('❌ Consola no encontrada.', 'error')
        return redirect(url_for('index'))
    
    return render_template('edit_console.html', console=console)


@app.route('/delete/<int:game_id>', methods=['POST'])
@login_required
@permission_required('delete') # Solo admin puede eliminar
def delete_game(game_id):
    conn = get_sqlserver_connection()
    try:

        # Obtener info del juego antes de eliminar
        game = conn.execute('SELECT title FROM games WHERE id = ?', (game_id,)).fetchone()

        conn.execute('DELETE FROM games WHERE id = ?', (game_id,))
        conn.commit()
        flash('Juego eliminado exitosamente!', 'success')

        if game:
            logger.info(f"Usuario {current_user.username} elimino juego: {game ['title']}")

    except Exception as e:
        logger.error(f"Error deleting game: {e}")
        flash(f'Error al eliminar juego: {e}', 'error')
    finally:
        conn.close()
    return redirect(url_for('index'))

@app.route('/delete_console/<int:console_id>', methods=['POST'])
@login_required
@permission_required('delete') # Solo admin puede eliminar
def delete_console(console_id):
    conn = get_sqlserver_connection()
    try:

        # Obtener info de la consola antes de eliminar 
        console = conn.execute('SELECT name, model FROM consoles WHERE id = ?', (console_id,)).fetchone()

        conn.execute('DELETE FROM consoles WHERE id = ?', (console_id,))
        conn.commit()
        flash('Consola eliminada exitosamente!', 'success')

        if console:
            logger.info(f"Usuario {current_user.username} elimino consola: {console['name']} - {console['model']}")

    except Exception as e:
        logger.error(f"Error deleting console: {e}")
        flash(f'Error al eliminar consola: {e}', 'error')
    finally:
        conn.close()
    return redirect(url_for('index'))

# Manejador de errores 403 (Forbidden)
@app.errorhandler(403)
def not_found(e):
    return render_template('403.html'), 403

# Manejador de errores 404 (Not Found)
@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

#Manejador de errores 429 (Too Many Requests)
@app.errorhandler(429)
def ratelimit_handler(e):
    return render_template('429.html', retry_after=e.description), 429

if __name__ == '__main__':
    app.run(debug=True)
