import bcrypt
from connection import get_sqlserver_connection
from auth import Role

def create_user(username, password, role='viewer'):
    """
    Crea un nuevo usuario con rol específico.
    
    Args:
        username: Nombre de usuario
        password: Contraseña en texto plano
        role: 'admin', 'editor', o 'viewer' (default: viewer)
    """
    # Validar rol
    valid_roles = [Role.ADMIN, Role.EDITOR, Role.VIEWER]
    if role not in valid_roles:
        print(f"❌ Error: Rol '{role}' no válido. Debe ser: {', '.join(valid_roles)}")
        return False
    
    conn = get_sqlserver_connection()
    try:
        # Verificar si el usuario ya existe
        existing = conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
        if existing:
            print(f"❌ Error: El usuario '{username}' ya existe.")
            return False
        
        # Crear hash de la contraseña
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Insertar usuario con rol
        conn.execute(
            'INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)', 
            (username, password_hash, role)
        )
        conn.commit()
        print(f"✅ Usuario '{username}' creado exitosamente con rol '{role}'.")
        return True
    except Exception as e:
        print(f"❌ Error creando usuario: {e}")
        return False
    finally:
        conn.close()

def list_users():
    """Lista todos los usuarios y sus roles"""
    conn = get_sqlserver_connection()
    cursor = conn.connection.cursor()  # Acceder al cursor real de pyodbc
    
    try:
        cursor.execute('SELECT id, username, role FROM users ORDER BY id')
        users = cursor.fetchall()
        
        print("\n" + "=" * 60)
        print("USUARIOS REGISTRADOS")
        print("=" * 60)
        
        if not users:
            print("No hay usuarios registrados.")
        else:
            for user in users:
                print(f"ID: {user[0]:3} | Usuario: {user[1]:20} | Rol: {user[2]}")
        
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"❌ Error listando usuarios: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("CREACIÓN DE USUARIOS - Videogames Database")
    print("=" * 60)
    print("\nRoles disponibles:")
    print("  - admin:  Acceso total (crear, editar, eliminar)")
    print("  - editor: Crear y editar (no puede eliminar)")
    print("  - viewer: Solo ver (sin modificaciones)")
    print("\n" + "=" * 60)
    
    # Listar usuarios existentes
    list_users()
    
    # Ejemplos de creación
    # Descomentar y modificar según necesites:
    
    # Crear administrador
    # create_user("admin2", "admin123", "admin")
    
    # Crear editor
    # create_user("editor", "editor123", "editor")
    
    # Crear viewer
    # create_user("viewer", "viewer123", "viewer")
    
    print("\n💡 Para crear usuarios, descomenta las líneas en create_user.py")
    print("   o modifica el script según tus necesidades.\n")