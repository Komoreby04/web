import bcrypt

# Generar el hash de la contraseña
password = 'admi123'  # Contraseña que deseas almacenar
salt = bcrypt.gensalt()  # Genera una sal para el hash
password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

# Ahora puedes insertar el hash generado en tu base de datos:
print(password_hash)
