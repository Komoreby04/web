from flask import Flask, render_template, request
import re
import pyodbc
from datetime import datetime
import bcrypt
import os
from dotenv import load_dotenv
from flask import session, jsonify

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)
app.secret_key = 'ed683531301ab6208a95e0222fbbef9a790e66253eaf2e09'

@app.route('/')  # Página principal
def index():
    return render_template('index.html')


# Conexión a la base de datos
def connect_to_db():
    try:
        conn = pyodbc.connect(
            "DRIVER={SQL Server};"
            "SERVER=ITZEL\\SQLEXPRESS01;"
            "DATABASE=estadia;"
            "UID=ITZEL;"
            "Trusted_Connection=yes;"
        )
        return conn
    except Exception as e:
        print("Error de conexión a la base de datos:", e)
        return None
from flask import session

# Lógica de inicio de sesión
def login(username, password):
    conn = connect_to_db()
    if conn is None:
        return None

    cursor = conn.cursor()
    try:
        cursor.execute("SELECT DB_NAME()")
        current_db = cursor.fetchone()
        print("Base de datos actual:", current_db[0])

        cursor.execute("SELECT password_hash, role FROM Usuarios WHERE username = ?", (username,))
        result = cursor.fetchone()
        print("Resultado de la base de datos:", result)

        if result:
            stored_hash, role = result
            print("Hash almacenado:", stored_hash)
            print("Rol del usuario:", role)

            if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
                print("¡Contraseña válida!")
                return role
            else:
                print("Contraseña inválida.")
    except Exception as e:
        print("Error al consultar la base de datos:", e)
    finally:
        if conn:
            conn.close()

    return None

@app.route('/login', methods=['POST'])
def login_api():
    username = request.form['username']
    password = request.form['password']

    print(f"Usuario recibido: {username}, Contraseña recibida: {password}")  # Depuración

    role = login(username, password)  # Llama a la función de autenticación
    print(f"Rol obtenido desde la base de datos: {role}")  # Depuración

    if role:
        session['role'] = role  # Guarda el rol en la sesión
        session.modified = True  # Asegura que la sesión se actualiza
        return jsonify({"status": "success", "role": role})
    else:
        return jsonify({"status": "error", "message": "Credenciales inválidas."})


# Ruta para obtener el rol desde la sesión (puedes usar esto en tu frontend):
@app.route('/get_role', methods=['GET'])
def get_role():
    role = session.get('role', None)  # Recupera el rol desde la sesión
    print(f"Rol recuperado desde la sesión: {role}")  # Depuración adicional
    if role:
        return jsonify({"status": "success", "role": role})
    else:
        return jsonify({"status": "error", "message": "No hay un rol definido."})


    
@app.route('/logout', methods=['GET'])
def logout():
    session.clear()  # Limpia todos los datos de la sesión
    return redirect('/')  # Redirige al usuario a la página de login

    
    
@app.route('/consultor', methods=['GET'])
def acceso_consultor():
    session.clear()  # Limpia la sesión para evitar conflictos
    session['role'] = 'consultor'  # Asigna el rol 'consultor' explícitamente
    print(f"Sesión configurada para rol: {session['role']}")
    return redirect('/menu')  # Redirige al área de consulta


@app.route('/menu')
def menu():
    return render_template('menu.html')


@app.route('/inicio')
def inicio():
    # Configurar la localización para español
    try:
        locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')  # Unix/Linux
    except locale.Error as e:
        return f"Error al configurar la localización: {str(e)}", 500

    # Obtener la fecha actual y el rango del mes
    hoy = datetime.now()
    primeros_dia_del_mes = datetime(hoy.year, hoy.month, 1)
    if hoy.month == 12:
        ultimo_dia_del_mes = datetime(hoy.year + 1, 1, 1) - timedelta(days=1)
    else:
        ultimo_dia_del_mes = datetime(hoy.year, hoy.month + 1, 1) - timedelta(days=1)

    try:
        # Conexión a la base de datos
        conn = pyodbc.connect(
            "DRIVER={SQL Server};"
            "SERVER=ITZEL\\SQLEXPRESS01;"  # Ajusta este parámetro según tu configuración
            "DATABASE=estadia;"  # Ajusta este parámetro según tu base de datos
            "UID=ITZEL;"
            "Trusted_Connection=yes;"
        )
        cursor = conn.cursor()

        # Consulta para obtener el Top 9 de agencias con más recuperación
        query_top_9 = """
        SELECT TOP 9 a.nombre_agencia, SUM(t.total) AS recuperacion_total
        FROM Reporte_ivee t
        JOIN Fecha f ON t.id_fecha = f.id_fecha
        JOIN Agencia a ON t.id_agencia = a.id_agencia
        WHERE f.fecha BETWEEN ? AND ?
        GROUP BY a.nombre_agencia
        ORDER BY recuperacion_total DESC;
        """
        cursor.execute(query_top_9, (primeros_dia_del_mes, ultimo_dia_del_mes))
        agencias_top_9 = cursor.fetchall()

        # Procesar resultados
        agencias = []
        for row in agencias_top_9:
            agencias.append({
                'nombre_agencia': row[0],
                'recuperacion_total': round(float(row[1]), 2)
            })

        # Verificar los datos antes de pasarlos a la plantilla
        print(agencias)  # Esto te ayudará a verificar si los datos están llegando correctamente

        return render_template('inicio.html', agencias=agencias, mes=hoy.strftime("%B").capitalize())

    except pyodbc.Error as e:
        return f"Error al conectar con la base de datos: {str(e)}", 500
    except Exception as e:
        return f"Error inesperado: {str(e)}", 500


@app.route('/reporte_ivee')  # Reporte IVEE
def reporte_ivee():
    user_role = session.get('role', None)
    return render_template('reporte_ivee.html', user_role=user_role)  # Contenido cargado en el iframe


def obtener_conexion():
    conexion = pyodbc.connect(
        "DRIVER={SQL Server};"
        "SERVER=ITZEL\\SQLEXPRESS01;"    # Reemplaza con tu servidor
        "DATABASE=estadia;"    # Reemplaza con tu base de datos
        "UID=ITZEL;"    # Reemplaza con tu usuario
        "Trusted_Connection=yes;")
    
    return conexion
# Función para procesar el contenido del archivo .txt y evitar duplicados en la base de datos
# Función para procesar el contenido del archivo .txt y evitar duplicados en la base de datos
def procesar_archivo_txt(contenido):
    divisiones = {
        "DK": "DK",
        "OT": "Otra División",
    }

    agencias_permitidas = {
        "XR": ("Tehuantepec", "A"),
        "XS": ("Juchitán", "B"),
        "XT": ("Matías Romero", "C"),
        "XU": ("Salina Cruz", "D"),
        "XV": ("Ixtepec", "E"),
        "XW": ("Union Hidalgo", "F"),
        "XX": ("Tequisistlán", "K"),
        "XY": ("Zanatepec", "W"),
        "YW": ("Sarabia", "X"),
    }

    try:
        # Dividir el contenido en líneas
        lines = contenido.splitlines()

        # Inicializar datos
        total_por_agencia = {
            codigo: {
                "Nombre": nombre,
                "Literal": literal,
                "Zona": '14',
                "División": "",
                "Ingresos": 0,
                "Cobranza Electrónica": 0,
                "DAP": 0,
                "Fecha": ""
            }
            for codigo, (nombre, literal) in agencias_permitidas.items()
        }

        agencia_codigo = None  # Código de la agencia
        concepto = None        # Tipo de concepto (Ingresos, Cobranza Electrónica, DAP)
        fecha_reporte = ""     # Fecha del reporte

        # Procesar línea por línea
        for line in lines:
            line = line.strip()
            # Intentar capturar una póliza
            poliza = re.search(r'(DDK\d{7}[A-Z]{2}[A-Z0-9]\d{2})', line)
            if poliza:
                codigo_prepoliza = poliza.group(1)
                division_codigo = codigo_prepoliza[1:3]
                division = divisiones.get(division_codigo, "División Desconocida")
                agencia_codigo = codigo_prepoliza[10:12]
                concepto = "Ingresos" if codigo_prepoliza[12] == "H" else "Cobranza Electrónica" if codigo_prepoliza[12] == "9" else "DAP" if codigo_prepoliza[12] == "N" else None

                # Extraer la fecha de la póliza
                fecha_str = f"{codigo_prepoliza[3:7]}-{codigo_prepoliza[7:9]}-{codigo_prepoliza[13:16]}"
                
                if agencia_codigo in total_por_agencia:
                    total_por_agencia[agencia_codigo]["Fecha"] = fecha_str
                    total_por_agencia[agencia_codigo]["División"] = division
                    fecha_reporte = fecha_str
                continue

            # Buscar montos en la línea
            monto_en_linea = re.findall(r'([\d,]+\.\d{2})', line)
            if monto_en_linea:
                ultimo_monto = float(monto_en_linea[-1].replace(',', ''))

                if agencia_codigo in total_por_agencia and concepto:
                    # Actualización de montos según el concepto
                    if concepto == "Ingresos":
                        total_por_agencia[agencia_codigo]["Ingresos"] = ultimo_monto
                    elif concepto == "Cobranza Electrónica":
                        total_por_agencia[agencia_codigo]["Cobranza Electrónica"] = ultimo_monto
                    elif concepto == "DAP":
                        total_por_agencia[agencia_codigo]["DAP"] = ultimo_monto

        # Recuperar el rol actual de la sesión
        role = session.get('role')
        print(f"Rol actual desde la sesión en consulta_ivee: {role}")  # Depuración
        is_admin = role == 'administrador'  # Evaluar si es administrador

        # Calcular totales independientemente del rol
        total_ingresos = sum(m['Ingresos'] for m in total_por_agencia.values())
        total_cobranza = sum(m['Cobranza Electrónica'] for m in total_por_agencia.values())
        total_dap = sum(m['DAP'] for m in total_por_agencia.values())
        total_general = total_ingresos + total_cobranza + total_dap

        # Si es administrador, insertar en la base de datos
        if is_admin:
            # Conectar a SQL Server
            conexion = obtener_conexion()
            cursor = conexion.cursor()

            # Verificar si la fecha ya existe en la base de datos
            cursor.execute("SELECT COUNT(*) FROM totales_ivee WHERE id_fecha = (SELECT id_fecha FROM Fecha WHERE fecha = ?)", fecha_reporte)
            existe_reporte = cursor.fetchone()[0] > 0

            if existe_reporte:
                print("El archivo ya ha sido procesado anteriormente. No se realizarán nuevas inserciones.")
                # Consultar los totales desde la tabla totales_ivee
                cursor.execute("""SELECT total_ingresos, total_cobranza, total_dap, total_general FROM totales_ivee WHERE id_fecha = (SELECT id_fecha FROM Fecha WHERE fecha = ?)""", fecha_reporte)
                resultado = cursor.fetchone()
                if resultado:
                    total_ingresos, total_cobranza, total_dap, total_general = resultado
                cursor.close()
                conexion.close()
                return total_por_agencia, total_ingresos, total_cobranza, total_dap, total_general, fecha_reporte

            # *** Inserciones en la base de datos ***
            for codigo, montos in total_por_agencia.items():
                nombre_agencia = montos['Nombre']
                division = montos['División']
                zona = montos['Zona']
                literal = montos['Literal']
                ingresos = montos['Ingresos']
                cobranza = montos['Cobranza Electrónica']
                dap = montos['DAP']
                fecha = montos['Fecha']

                # Insertar la fecha en la tabla Fecha si no existe
                cursor.execute("IF NOT EXISTS (SELECT 1 FROM Fecha WHERE fecha = ?) INSERT INTO Fecha (fecha) VALUES (?)", fecha, fecha)
                cursor.execute("SELECT id_fecha FROM Fecha WHERE fecha = ?", fecha)
                id_fecha = cursor.fetchone()[0]

                # Insertar el reporte en la tabla Reporte_ivee
                cursor.execute("""
                    INSERT INTO Reporte_ivee (
                        id_division, id_zona, id_literal, id_agencia, id_fecha, ingresos, cobranza_electronica, DAP, total
                    )
                    VALUES (
                        (SELECT id_division FROM Division WHERE nombre_division = ?),
                        (SELECT id_zona FROM Zona WHERE nombre_zona = ?),
                        (SELECT id_literal FROM Literal WHERE letra = ?),
                        (SELECT id_agencia FROM Agencia WHERE nombre_agencia = ?),
                        ?, ?, ?, ?, ?
                    )
                """, division, zona, literal, nombre_agencia, id_fecha, ingresos, cobranza, dap, ingresos + cobranza + dap)

            # Calcular totales y almacenarlos en totales_ivee
            cursor.execute("""
                INSERT INTO totales_ivee (
                    id_fecha, total_ingresos, total_cobranza, total_dap, total_general
                )
                VALUES (?, ?, ?, ?, ?)
            """, id_fecha, total_ingresos, total_cobranza, total_dap, total_general)

            # Confirmar cambios en la base de datos
            conexion.commit()
            cursor.close()
            conexion.close()

        # Devolver los totales y resultados
        return total_por_agencia, total_ingresos, total_cobranza, total_dap, total_general, fecha_reporte

    except Exception as e:
        print(f"Error procesando el archivo: {e}")
        return {}, 0, 0, 0, 0, ""



@app.route('/consulta_ivee', methods=['GET', 'POST'])
def consulta_ivee():
    # Verificar el rol del usuario
    role = session.get('role')
    print(f"Rol actual desde la sesión en consulta_ivee: {role}")  # Depuración
    is_admin = role == 'administrador'  # Evaluar si es administrador


    # Obtener la fecha y la sección desde los parámetros de la URL
    fecha = request.args.get('fecha')
    seccion = request.args.get('seccion')

    if not fecha:
        return "No se ha especificado una fecha.", 400

    conexion = obtener_conexion()
    cursor = conexion.cursor()

    if request.method == 'POST':
        archivo = request.files.get('archivo')
        if not archivo:
            return "Por favor, seleccione un archivo para cargar.", 400

    cursor.execute("""
        SELECT r.ingresos, r.cobranza_electronica, r.DAP, 
               r.ingresos + r.cobranza_electronica + r.DAP AS Total, 
               a.nombre_agencia, d.nombre_division, z.nombre_zona, l.letra
        FROM Reporte_ivee r
        JOIN Agencia a ON r.id_agencia = a.id_agencia
        JOIN Division d ON r.id_division = d.id_division
        JOIN Zona z ON r.id_zona = z.id_zona
        JOIN Literal l ON r.id_literal = l.id_literal
        WHERE r.id_fecha = (SELECT id_fecha FROM Fecha WHERE fecha = ?)
    """, (fecha,))

    resultado = cursor.fetchall()
    if not resultado:
        cursor.close()
        conexion.close()
        return "No hay datos disponibles para la fecha especificada.", 400

    total_por_agencia = {}
    for row in resultado:
        agencia, division, zona, literal = row[4], row[5], row[6], row[7]
        total_por_agencia[agencia] = {
            "Nombre": agencia,
            "División": division,
            "Zona": zona,
            "Literal": literal,
            "Ingresos": f"${row[0]:,.2f}",
            "Cobranza Electrónica": f"${row[1]:,.2f}",
            "DAP": f"${row[2]:,.2f}",
            "Total": f"${row[3]:,.2f}"
        }

    cursor.execute("""
        SELECT total_ingresos, total_cobranza, total_dap, total_general
        FROM totales_ivee
        WHERE id_fecha = (SELECT id_fecha FROM Fecha WHERE fecha = ?)
    """, (fecha,))
    total_data = cursor.fetchone()

    if not total_data:
        cursor.close()
        conexion.close()
        return "No se encontraron totales para esta fecha.", 400
    
    total_ingresos, total_cobranza, total_dap, total_general = total_data

    cursor.close()
    conexion.close()

    return render_template(
        'reporte.html',
        fecha_seleccionada=fecha,
        total_por_agencia=total_por_agencia,  # Asegúrate de tener esta variable definida
        total_ingresos=f"${total_ingresos:,.2f}",
        total_cobranza=f"${total_cobranza:,.2f}",
        total_dap=f"${total_dap:,.2f}",
        total_general=f"${total_general:,.2f}",
        is_admin=is_admin  # Enviar esta variable al template
    )

    
    
@app.route('/eliminar_registros', methods=['POST'])
def eliminar_registros():
    try:
        # Obtener la fecha enviada en la solicitud
        data = request.get_json()
        fecha = data.get('fecha')

        if not fecha:
            return jsonify({'success': False, 'message': 'Fecha no proporcionada'}), 400

        # Conectar a la base de datos
        conn = connect_to_db()
        if conn is None:
            return jsonify({'success': False, 'message': 'No se pudo conectar a la base de datos'}), 500

        cursor = conn.cursor()

        # Primero, eliminar los registros de la tabla Totales_ivee basados en la fecha
        cursor.execute("""
            DELETE FROM Totales_ivee WHERE id_fecha = (
                SELECT id_fecha FROM Fecha WHERE fecha = ?
            )
        """, (fecha,))

        # Luego, eliminar los registros de la tabla Reporte_ivee basados en la fecha
        cursor.execute("""
            DELETE FROM Reporte_ivee WHERE id_fecha = (
                SELECT id_fecha FROM Fecha WHERE fecha = ?
            )
        """, (fecha,))

        # Finalmente, eliminar el registro de la tabla Fecha basados en la fecha
        cursor.execute("""
            DELETE FROM Fecha WHERE fecha = ?
        """, (fecha,))

        # Confirmar los cambios
        conn.commit()

        # Cerrar la conexión
        cursor.close()
        conn.close()

        # Responder con éxito
        return jsonify({'success': True, 'message': 'Registros eliminados exitosamente'}), 200

    except Exception as e:
        print("Error al eliminar los registros:", e)
        return jsonify({'success': False, 'message': 'Error al eliminar los registros'}), 500

@app.route('/cargar_archivo', methods=['POST'])
def cargar_archivo():
    
    role = session.get('role')
    print(f"Rol actual desde la sesión en consulta_ivee: {role}")  # Depuración
    is_admin = role == 'administrador'  # Evaluar si es administrador
    
    archivo = request.files['archivo']
    
    # Verificar que el archivo tenga la extensión .txt
    if archivo and archivo.filename.endswith('.txt'):
        # Leer el contenido del archivo sin guardarlo
        contenido = archivo.read().decode('utf-8')
        
        # Procesar el contenido directamente
        total_por_agencia, total_ingresos, total_cobranza, total_dap, total_general, fecha = procesar_archivo_txt(contenido)  # Capturamos fecha_reporte

        # Si se devuelve un error en `total_por_agencia`, mostrarlo
        if isinstance(total_por_agencia, str):
            return f"Error: {total_por_agencia}", 400

        # Formatear los montos con comas y el símbolo del peso
        for agencia, montos in total_por_agencia.items():
            ingresos = montos['Ingresos']
            cobranza = montos['Cobranza Electrónica']
            dap = montos['DAP']
            montos['Ingresos'] = f"${ingresos:,.2f}"  # Formato: $1,234.56
            montos['Cobranza Electrónica'] = f"${cobranza:,.2f}"  # Formato: $1,234.56
            montos['DAP'] = f"${dap:,.2f}"  # Formato: $1,234.56
            montos['Total'] = f"${ingresos + cobranza + dap:,.2f}"  # Sumar ingresos y cobranza

        # Renderizar la página HTML con los datos
        return render_template('reporte.html', total_por_agencia=total_por_agencia, 
                            total_ingresos=f"${total_ingresos:,.2f}",  
                            total_cobranza=f"${total_cobranza:,.2f}",
                            total_dap=f"${total_dap:,.2f}",
                            total_general=f"${total_general:,.2f}",
                            fecha_seleccionada=fecha,
                            is_admin=is_admin)  # Pasar total_general a la plantilla
    else:
        return "El archivo no es válido o no se ha subido.", 400



from flask import Flask, request, jsonify
from flask_cors import CORS

CORS(app)

@app.route('/verificar_fecha', methods=['POST'])
def verificar_fecha():
    fecha = request.json.get('fecha')
    if not fecha:
        return jsonify({"error": "Fecha no proporcionada"}), 400

    try:
        conexion = obtener_conexion()  # Asegúrate de que esta función esté definida correctamente
        if not conexion:
            return jsonify({"error": "No se pudo conectar a la base de datos"}), 500
        
        cursor = conexion.cursor()

        # Consulta para verificar si la fecha ya existe en los reportes
        cursor.execute("SELECT COUNT(*) FROM totales_ivee WHERE id_fecha = (SELECT id_fecha FROM Fecha WHERE fecha = ?)", (fecha,))
        existe_reporte = cursor.fetchone()[0] > 0

        cursor.close()
        conexion.close()

        # Devolver el resultado
        return jsonify({"existe_reporte": existe_reporte})

    except Exception as e:
        return jsonify({"error": str(e)}), 500



def obtener_reporte_por_fecha(fecha_seleccionada):
    # Conectar a la base de datos
    conexion = pyodbc.connect(
        "DRIVER={SQL Server};"
        "SERVER=ITZEL\\SQLEXPRESS01;"    # Reemplaza con tu servidor
        "DATABASE=estadia;"    # Reemplaza con tu base de datos
        "UID=ITZEL;"    # Reemplaza con tu usuario
        "Trusted_Connection=yes;")
    cursor = conexion.cursor()

    # Verificar si la fecha existe en la base de datos
    cursor.execute("SELECT id_fecha FROM Fecha WHERE fecha = ?", fecha_seleccionada)
    resultado_fecha = cursor.fetchone()

    if not resultado_fecha:
        return "No hay un reporte disponible para esta fecha."

    id_fecha = resultado_fecha[0]

    # Obtener los totales del reporte para la fecha seleccionada
    cursor.execute("""
        SELECT total_ingresos, total_cobranza, total_dap, total_general
        FROM totales_ivee
        WHERE id_fecha = ?
    """, id_fecha)
    
    resultado_totales = cursor.fetchone()
    if not resultado_totales:
        return "No se encontraron datos de reporte para esta fecha."

    total_ingresos, total_cobranza, total_dap, total_general = resultado_totales
    
    # Cerrar la conexión
    cursor.close()
    conexion.close()

    # Retornar los totales en un diccionario
    return {
        "fecha": fecha_seleccionada,
        "total_ingresos": total_ingresos,
        "total_cobranza": total_cobranza,
        "total_dap": total_dap,
        "total_general": total_general
    }
    
@app.route('/reporte')
def reporte():
    # Verificar el rol del usuario
    is_admin = session.get('role') == 'administrador'

    # Cargar los datos del reporte (como en tu lógica actual)
    fecha = request.args.get('fecha')
    if not fecha:
        return "Fecha no proporcionada.", 400

    # Obtener el reporte (simulación con lógica existente)
    reporte_data = obtener_reporte_por_fecha(fecha)
    if isinstance(reporte_data, str):
        return reporte_data, 400  # Manejo de errores

    # Renderizar el template con la variable `is_admin`
    return render_template('reporte.html', is_admin=is_admin, **reporte_data)



from flask import Flask, render_template, request, session
from datetime import datetime, timedelta
import pyodbc
from flask import Flask, render_template, request, session
from datetime import datetime, timedelta
import pyodbc

@app.route('/mensual_ivee', methods=['GET'])
def mensual_ivee():
    user_role = session.get('role', None)
    is_admin = user_role == 'administrador'
    print(f"El rol del usuario es: {user_role}")  # Verifica el valor del rol
    print(f"Es admin: {is_admin}")  # Verifica el valor de is_admin

    selected_month = request.args.get('month')
    meses_en_espanol = [
        'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
        'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
    ]

    if selected_month:
        year, month = selected_month.split('-')
        start_date = datetime(int(year), int(month), 1)
        end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        month_name = meses_en_espanol[int(month) - 1]

        conexion = obtener_conexion()
        cursor = conexion.cursor()

        try:
            fechas_totales = [(start_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range((end_date - start_date).days + 1)]
            print(f"Fechas totales para la consulta: {fechas_totales}")  # Verifica las fechas que se están usando en la consulta

            query_meta = """
            SELECT fecha_meta, meta_ivee
            FROM metas
            WHERE fecha_meta IN ({})
            """.format(",".join("?" for _ in fechas_totales))
            print(f"Consulta SQL de metas: {query_meta}")  # Verifica la consulta SQL generada
            
            cursor.execute(query_meta, fechas_totales)
            metas = cursor.fetchall()
            print(f"Metas obtenidas: {metas}")  # Verifica qué metas se han recuperado de la base de datos

            if not metas:
                print("No se encontraron metas para las fechas seleccionadas.")  # Mensaje si no se encuentran metas
                return render_template('mensual_ivee.html', meta_ivee=None, selected_month=f"{month_name} / {year}", mensaje="No se encontraron metas para el mes seleccionado.", is_admin=is_admin)

            # Si hay metas, las almacenamos en un diccionario
            meta_dict = {meta[0]: meta[1] for meta in metas}
            total_meta_ivee = sum(meta_dict.values())
            print(f"Total de metas: {total_meta_ivee}")  # Verifica la suma de las metas

            query_totales = """
            SELECT ti.total_ingresos, ti.total_cobranza, ti.total_dap, ti.total_general, f.fecha
            FROM totales_ivee ti
            INNER JOIN Fecha f ON ti.id_fecha = f.id_fecha
            WHERE f.fecha BETWEEN ? AND ?
            """
            cursor.execute(query_totales, (start_date, end_date))
            totales = cursor.fetchall()

            if not totales:
                return render_template('mensual_ivee.html', meta_ivee=meta_dict, selected_month=f"{month_name} / {year}", mensaje="No se encontraron datos para el mes seleccionado.", is_admin=is_admin)

            datos_totales = []
            total_ingresos_sum = total_cobranza_sum = total_dap_sum = total_general_sum = 0

            for total in totales:
                fecha_obj = datetime.strptime(total[4], '%Y-%m-%d')
                meta_para_fecha = meta_dict.get(fecha_obj.strftime('%Y-%m-%d'), 0)

                datos_totales.append({
                    'Ingresos': f"${total[0]:,.2f}",
                    'Cobranza Electrónica': f"${total[1]:,.2f}",
                    'DAP': f"${total[2]:,.2f}",
                    'Total': f"${total[3]:,.2f}",
                    'Fecha': fecha_obj.strftime('%Y-%m-%d'),
                    'Meta': f"${meta_para_fecha:,.2f}"
                })

                total_ingresos_sum += total[0]
                total_cobranza_sum += total[1]
                total_dap_sum += total[2]
                total_general_sum += total[3]

            if total_meta_ivee != 0:
                cumplimiento_total_calculado = (total_general_sum / total_meta_ivee) * 100
            else:
                cumplimiento_total_calculado = 0

            return render_template(
                'mensual_ivee.html',
                is_admin=is_admin,  # Se pasa el rol al template
                meta_ivee=meta_dict,
                total_meta_ivee=f"${total_meta_ivee:,.2f}",
                cumplimiento_total_calculado=f"{cumplimiento_total_calculado:.2f}%" if total_meta_ivee != 0 else "No se puede calcular",
                datos_totales=datos_totales,
                total_ingresos_sum=f"${total_ingresos_sum:,.2f}",
                total_cobranza_sum=f"${total_cobranza_sum:,.2f}",
                total_dap_sum=f"${total_dap_sum:,.2f}",
                total_general_sum=f"${total_general_sum:,.2f}",
                selected_month=f"{month_name} / {year}",
                mensaje=None
            )

        finally:
            cursor.close()
            conexion.close()

    return render_template('mensual_ivee.html', mensaje="Por favor, selecciona un mes para consultar los datos.", is_admin=is_admin)






from flask import Flask, request, render_template
from datetime import datetime, timedelta
import pyodbc


@app.route('/reporte_mensual_agencia', methods=['GET'])
def reporte_mensual_agencia():
    # Configurar la localización para español
    try:
        locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')  # Para sistemas Unix/Linux
        # locale.setlocale(locale.LC_TIME, 'Spanish_Spain.1252')  # Para sistemas Windows
    except locale.Error as e:
        return f"Error al configurar la localización: {str(e)}", 500

    # Obtener la fecha y el nombre de la agencia desde los parámetros de la URL
    fecha = request.args.get('fecha')
    nombre_agencia = request.args.get('nombre_agencia')

    # Verificar si se ha proporcionado la fecha y el nombre de la agencia
    if not fecha or not nombre_agencia:
        return "No se ha especificado una fecha o una agencia.", 400

    # Convertir la fecha a un objeto datetime
    try:
        fecha_obj = datetime.strptime(fecha, "%Y-%m-%d")
        mes_seleccionado = fecha_obj.strftime("%B")  # Mes en formato textual
        año_seleccionado = fecha_obj.year  # Año
    except ValueError:
        return "Fecha inválida. Asegúrate de que esté en formato 'YYYY-MM-DD'.", 400

    # Obtener los primeros y últimos días del mes
    try:
        primeros_dia_del_mes = datetime(año_seleccionado, fecha_obj.month, 1)
        ultimo_dia_del_mes = datetime(año_seleccionado, fecha_obj.month + 1, 1) - timedelta(days=1)
    except ValueError:
        return "Error al calcular el rango del mes.", 400

    # Conexión a la base de datos
    try:
        conn = pyodbc.connect(
            "DRIVER={SQL Server};"
            "SERVER=ITZEL\\SQLEXPRESS01;"  # Cambia esto según tu configuración
            "DATABASE=estadia;"
            "UID=ITZEL;"  # Cambia el usuario según sea necesario
            "Trusted_Connection=yes;")
        cursor = conn.cursor()

        # Consulta ajustada para obtener los datos del reporte mensual por agencia
        query_agencia = "SELECT id_agencia FROM Agencia WHERE nombre_agencia = ?"
        cursor.execute(query_agencia, nombre_agencia)
        id_agencia = cursor.fetchone()

        if not id_agencia:
            return f"No se encontró la agencia con el nombre '{nombre_agencia}'.", 400

        id_agencia = id_agencia[0]  # Extraer el id_agencia de la tupla

        # Consulta para obtener los datos del reporte mensual
        query_reporte = """
        SELECT f.fecha, t.ingresos, t.cobranza_electronica, t.DAP, t.total, 
            m.meta_ivee_agencia, a.nombre_agencia
        FROM Reporte_ivee t
        JOIN Fecha f ON t.id_fecha = f.id_fecha
        LEFT JOIN metas_ivee_agencia m ON f.fecha = m.fecha_meta_agencia AND t.id_agencia = m.id_agencia
        JOIN Agencia a ON t.id_agencia = a.id_agencia
        WHERE f.fecha BETWEEN ? AND ? AND t.id_agencia = ?
        ORDER BY f.fecha;
        """
        cursor.execute(query_reporte, (primeros_dia_del_mes, ultimo_dia_del_mes, id_agencia))
        resultados = cursor.fetchall()

        # Inicialización de los totales
        total_ingresos = 0
        total_cobranza = 0
        total_dap = 0
        total_total = 0
        meta_total = 0

        # Construir el diccionario total_por_dia
        total_por_dia = {}
        for row in resultados:
            fecha = row[0]  # La fecha ya está en formato de cadena
            ingresos = float(row[1]) if row[1] is not None else 0
            cobranza = float(row[2]) if row[2] is not None else 0
            dap = float(row[3]) if row[3] is not None else 0
            total = float(row[4]) if row[4] is not None else 0
            meta = float(row[5]) if row[5] is not None else 0  # Asegurar que meta sea 0 si es None

            total_por_dia[fecha] = {
                'Ingresos': ingresos,
                'Cobranza Electrónica': cobranza,
                'DAP': dap,
                'Total': total,
                'meta': meta,
                'nombre_agencia': row[6]
            }

            # Acumulando los totales
            total_ingresos += ingresos
            total_cobranza += cobranza
            total_dap += dap
            total_total += total
            meta_total += meta

        # Verificar si meta_total es 0, y en ese caso establecer cumplimiento_total como "Sin cumplimiento"
        if meta_total > 0:
            cumplimiento_total = (total_total / meta_total) * 100
        else:
            cumplimiento_total = "Sin cumplimiento"  # Cambiar a texto en lugar de 0

        return render_template('mensual_ivee_agencia.html',
                               total_por_dia=total_por_dia,
                               mes_seleccionado=mes_seleccionado.capitalize(),  # Capitalizar el mes
                               año_seleccionado=año_seleccionado,
                               nombre_agencia=nombre_agencia,
                               total_ingresos=total_ingresos,
                               total_cobranza=total_cobranza,
                               total_dap=total_dap,
                               total_total=total_total,
                               meta_total=meta_total,
                               cumplimiento_total=cumplimiento_total)

    except pyodbc.Error as e:
        return f"Error al conectar con la base de datos: {str(e)}", 500
    except Exception as e:
        return f"Error al obtener los datos: {str(e)}. Por favor, revisa los parámetros o la plantilla.", 500




def verificar_meta_existente(fecha_base_dt):
    
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM metas WHERE YEAR(fecha_meta) = ? AND MONTH(fecha_meta) = ?",
            (fecha_base_dt.year, fecha_base_dt.month)
        )
        resultado = cursor.fetchone()
        cursor.close()
        conexion.close()
        return resultado[0] > 0
    except Exception as e:
        print(f"Error al verificar metas existentes: {str(e)}")
        return False



from flask import Flask, request, jsonify
import pandas as pd
from datetime import datetime
import pyodbc
import calendar  # Importar el módulo calendar
from flask import Flask, request, jsonify
import pandas as pd
from datetime import datetime
import pyodbc
import calendar
from flask import redirect, url_for, flash
from datetime import datetime
import calendar
import pandas as pd
from flask import request, jsonify
from flask import abort

from flask import session, request, abort
import pandas as pd
import calendar
from datetime import datetime

@app.route('/cargar-meta', methods=['POST'])
def cargar_meta():
    user_role = session.get('role', 'user')  # Obtener el rol del usuario desde la sesión

    fecha_base = request.args.get('fecha')
    if not fecha_base:
        return {"status": "error", "message": "No se ha especificado una fecha base en la URL"}, 400

    # Si la fecha es en formato 'Mes / Año' (por ejemplo, 'Septiembre / 2024')
    if ' / ' in fecha_base:
        # Separar el mes y el año
        month_name, year = fecha_base.split(' / ')
        month_name = month_name.strip().lower()  # Convertir el mes a minúsculas para que sea más fácil buscarlo
        year = year.strip()
        
        # Meses en español, mapeados al número correspondiente
        meses_en_espanol = {
            'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4, 'mayo': 5, 'junio': 6,
            'julio': 7, 'agosto': 8, 'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
        }
        
        # Verificar si el mes es válido
        if month_name in meses_en_espanol:
            month = meses_en_espanol[month_name]
            # Utilizar solo el formato 'YYYY-MM', sin agregar día
            fecha_base = f"{year}-{month:02d}"
        else:
            return {"status": "error", "message": f"Mes '{month_name}' no es válido"}, 400

    # Verificar si la fecha base ahora está en formato 'YYYY-MM' (sin día)
    try:
        fecha_base_dt = datetime.strptime(fecha_base, '%Y-%m')  # Solo necesitamos año y mes
    except ValueError as e:
        return {"status": "error", "message": f"Error en el formato de la fecha: {str(e)}"}, 400
    
    # Verificar si ya existen metas para el mes seleccionado
    if verificar_meta_existente(fecha_base_dt):
        return {"status": "error", "message": "Ya existen metas registradas para este mes"}, 400

    # Si no hay metas para el mes, pedir cargar un archivo Excel
    archivo_excel = request.files.get('archivo_excel')
    if not archivo_excel or archivo_excel.filename == '':
        return {"status": "error", "message": "Archivo no seleccionado"}, 400

    try:
        print("Cargando archivo Excel...")
        excel_file = pd.ExcelFile(archivo_excel)
        if 'Concentrado' not in excel_file.sheet_names:
            return {"status": "error", "message": "La hoja 'Concentrado' no existe en el archivo"}, 400

        df_concentrado = excel_file.parse('Concentrado')
        if len(df_concentrado) <= 11:
            return {"status": "error", "message": "La fila 12 no existe o el archivo está incompleto"}, 400

        fila_12 = df_concentrado.iloc[11, 3:37].dropna()
        metas = [round(valor * 1_000_000.00, 2) for valor in fila_12]
        if metas:
            metas.pop()

        # No es necesario obtener de nuevo 'fecha_base', ya está procesada
        año = fecha_base_dt.year
        mes = fecha_base_dt.month
        max_dia = calendar.monthrange(año, mes)[1]

        print("Conectando a la base de datos...")
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        print("Conexión establecida.")

        for dia, meta in zip(range(1, len(metas) + 1), metas):
            if dia > max_dia:
                print(f"El día {dia} no es válido para el mes {mes} del año {año}")
                continue

            fecha_completa = datetime(año, mes, dia).date()
            meta_formateada = f"${meta:,.2f}"
            print(f"Procesando fecha: {fecha_completa} con meta: {meta_formateada}")

            cursor.execute(
                "INSERT INTO metas (fecha_meta, meta_ivee) VALUES (?, ?)",
                (fecha_completa.strftime('%Y-%m-%d'), meta)
            )

            print(f"Meta insertada: {meta_formateada} para la fecha {fecha_completa}")

        # Procesar las metas por agencia
        agencias = df_concentrado.iloc[2:11, 1].tolist()
        metas_diarias = df_concentrado.iloc[2:11, 3:34].values.tolist()

        metas_por_agencia = {}
        for i, agencia in enumerate(agencias):
            if not pd.isna(agencia):
                metas = [
                    round(valor * 1_000_000.00, 2) if not pd.isna(valor) else None
                    for valor in metas_diarias[i]
                ]
                metas_por_agencia[agencia] = metas

        correccion_nombres = {
            "juchitan": "Juchitán",
            "matias romero": "Matías Romero",
            "tequisistlan": "Tequisistlán",
            "tehuantepec": "Tehuantepec"
        }

        metas_por_agencia_corregido = {}
        for nombre_agencia, metas in metas_por_agencia.items():
            nombre_normalizado = nombre_agencia.strip().lower()
            nombre_corregido = correccion_nombres.get(nombre_normalizado, nombre_agencia)
            metas_por_agencia_corregido[nombre_corregido] = metas

        insertar_metas_por_agencia(metas_por_agencia_corregido, fecha_base_dt)

        conexion.commit()
        cursor.close()
        conexion.close()
        print("Conexión cerrada.")

        return render_template('mensual_ivee.html', user_role=user_role, message="Datos cargados exitosamente.")


    except Exception as e:
        return {"status": "error", "message": f"Error al procesar el archivo: {str(e)}"}, 500


def insertar_metas_por_agencia(metas_por_agencia, fecha_base_dt):
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute("SELECT id_agencia, nombre_agencia FROM Agencia")
        agencias_db = {row.nombre_agencia.strip().lower(): row.id_agencia for row in cursor.fetchall()}
        print("Agencias en la base de datos:", agencias_db)

        max_dia = calendar.monthrange(fecha_base_dt.year, fecha_base_dt.month)[1]
        agencias_validas = ['tehuantepec', 'juchitán', 'matías romero', 'salina cruz', 'ixtepec', 'union hidalgo', 'tequisistlán', 'zanatepec', 'sarabia']

        for agencia, metas in metas_por_agencia.items():
            agencia_normalizada = agencia.strip().lower()
            if agencia_normalizada in agencias_validas:
                id_agencia = agencias_db[agencia_normalizada]
                for dia, meta in enumerate(metas, start=1):
                    if meta is not None and dia <= max_dia:
                        fecha_meta = datetime(fecha_base_dt.year, fecha_base_dt.month, dia).date()
                        meta_formateada = f"${meta:,.2f}"
                        cursor.execute(
                            """
                            INSERT INTO metas_ivee_agencia (fecha_meta_agencia, id_agencia, meta_ivee_agencia)
                            VALUES (?, ?, ?)
                            """,
                            fecha_meta.strftime('%Y-%m-%d'),
                            id_agencia,
                            meta
                        )
                        print(f"Meta ingresada: Agencia {agencia_normalizada} (ID {id_agencia}), Fecha {fecha_meta}, Meta {meta_formateada}")

        conexion.commit()
        cursor.close()
        conexion.close()
        print("Metas por agencia insertadas exitosamente.")

    except Exception as e:
        print(f"Error al insertar metas por agencia: {str(e)}")
        raise
    
    
import pyodbc
from flask import request, jsonify
from datetime import datetime, timedelta

# Función para conectar a la base de datos
def connect_to_db():
    try:
        conn = pyodbc.connect(
            "DRIVER={SQL Server};"
            "SERVER=ITZEL\\SQLEXPRESS01;"  # Cambia esto según tu configuración de servidor
            "DATABASE=estadia;"            # Asegúrate de que el nombre de la base de datos sea correcto
            "UID=ITZEL;"                  # Usuario para la conexión
            "Trusted_Connection=yes;"     # Usar autenticación de Windows (esto depende de tu configuración)
        )
        return conn
    except pyodbc.Error as e:
        # Captura los errores específicos de pyodbc y muestra el mensaje
        print("Error de conexión a la base de datos:", e)
        return None
    except Exception as e:
        # Captura cualquier otro error general
        print("Error inesperado:", e)
        return None

import locale
@app.route('/eliminar_meta', methods=['POST'])
def eliminar_meta():
    try:
        # Obtener la fecha enviada en el formulario
        fecha_str = request.form.get('fecha')

        # Depurar la fecha recibida
        print(f"Fecha recibida: {fecha_str}")  # Esto te permitirá ver qué valor llega

        # Verificar si la fecha fue proporcionada
        if not fecha_str:
            return jsonify({'success': False, 'message': 'Fecha no proporcionada'}), 400

        # Limpiar espacios y asegurarnos de que el formato sea correcto
        fecha_str = fecha_str.strip()  # Eliminar posibles espacios en los extremos

        # Establecer la localización en español para que el mes se reconozca correctamente
        locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')  # Esto es para Linux/Unix, puede variar en Windows

        # Convertir la fecha del formato "Mes / Año" (por ejemplo "Septiembre / 2024") a un objeto datetime
        try:
            # Intentar separar el mes y el año por el delimitador " / "
            mes, anio = fecha_str.split(" / ")

            # Convertir el nombre del mes a su número correspondiente (por ejemplo, "Septiembre" -> 9)
            mes = datetime.strptime(mes, '%B').month  # Convierte el nombre del mes a número
            anio = int(anio)  # Asegurarse de que el año se convierte a un número entero
            
            # Obtener el primer y último día del mes
            primer_dia_mes = datetime(anio, mes, 1)  # Primer día del mes
            ultimo_dia_mes = (primer_dia_mes.replace(month=mes % 12 + 1, day=1) - timedelta(days=1))  # Último día del mes
            print(f"Primer día del mes: {primer_dia_mes}")
            print(f"Último día del mes: {ultimo_dia_mes}")
        except ValueError as e:
            # Si hay algún problema al convertir el mes o el año, enviar el error
            return jsonify({'success': False, 'message': f'Formato de fecha inválido: {e}'}), 400

        # Conectar a la base de datos
        conn = connect_to_db()
        if conn is None:
            return jsonify({'success': False, 'message': 'No se pudo conectar a la base de datos'}), 500

        # Usar un cursor para ejecutar consultas
        cursor = conn.cursor()

        # Eliminar registros de la tabla metas_ivee_agencia basados en el rango de fechas (mes completo)
        cursor.execute("""
            DELETE FROM metas_ivee_agencia
            WHERE fecha_meta_agencia BETWEEN ? AND ?
        """, (primer_dia_mes, ultimo_dia_mes))

        # Eliminar registros de la tabla metas basados en el rango de fechas (mes completo)
        cursor.execute("""
            DELETE FROM metas
            WHERE fecha_meta BETWEEN ? AND ?
        """, (primer_dia_mes, ultimo_dia_mes))

        # Confirmar los cambios
        conn.commit()

        # Cerrar el cursor y la conexión
        cursor.close()
        conn.close()

        # Redirigir al template con un mensaje
        return render_template('mensual_ivee.html', 
                            message=f"Metas eliminadas para el mes de {primer_dia_mes.strftime('%B / %Y')}")


    except Exception as e:
        # Si ocurre un error, imprímelo y responder con error
        print(f"Error al eliminar la meta: {e}")
        return jsonify({'success': False, 'message': 'Error al eliminar las metas'}), 500





@app.template_filter('currency')
def currency_format(value):
    """
    Formatea un número como moneda con el signo de peso y comas.
    Ejemplo: 1234567.89 -> $1,234,567.89
    """
    if isinstance(value, (int, float)):
        return f"${value:,.2f}"
    return value

from datetime import datetime

@app.template_filter('datetime')
def format_datetime(value, format="%d"):
    """
    Filtra una fecha para mostrarla en el formato especificado.
    Por defecto, muestra solo el día (%d).
    """
    try:
        return datetime.strptime(value, "%Y-%m-%d").strftime(format)
    except (ValueError, TypeError):
        return value

def verificar_registros_mes(año, mes):
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()

        query = """
        SELECT COUNT(*) FROM metas 
        WHERE YEAR(fecha_meta) = ? AND MONTH(fecha_meta) = ?
        """
        cursor.execute(query, (año, mes))
        resultado = cursor.fetchone()

        cursor.close()
        conexion.close()

        return resultado[0] > 0
    except Exception as e:
        print(f"Error al verificar los registros del mes: {str(e)}")
        raise

def obtener_datos_mes(año, mes):
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT fecha_meta, meta_ivee FROM metas 
            WHERE YEAR(fecha_meta) = ? AND MONTH(fecha_meta) = ?
        """, (año, mes))
        metas = cursor.fetchall()

        cursor.close()
        conexion.close()

        return metas
    except Exception as e:
        print(f"Error al obtener los datos para el mes: {str(e)}")
        raise

@app.route('/consulta-mensual', methods=['GET'])
def consulta_mensual():
    fecha_base = request.args.get('fecha')
    if not fecha_base:
        return jsonify({"status": "error", "message": "No se ha especificado una fecha base en la URL"}), 400

    if len(fecha_base) == 7:  # Ejemplo: "2024-09"
        fecha_base = fecha_base + "-01"  # Añadir el día como "01" si solo es año-mes

    try:
        fecha_base_dt = datetime.strptime(fecha_base, '%Y-%m-%d')
        año = fecha_base_dt.year
        mes = fecha_base_dt.month
    except ValueError:
        return jsonify({"status": "error", "message": "Formato de fecha incorrecto, debe ser YYYY-MM o YYYY-MM-DD"}), 400

    if not verificar_registros_mes(año, mes):
        return jsonify({"status": "success", "message": "No hay registros para ese mes", "data": []}), 200

    metas = obtener_datos_mes(año, mes)

    if not metas:
        return jsonify({"status": "success", "message": "No hay datos para ese mes", "data": []}), 200

    # Verificar y convertir la fecha a datetime.date antes de formatearla
    reporte = []
    for meta in metas:
        fecha_meta = meta[0]
        
        # Asegurarse de que fecha_meta sea un objeto datetime
        if isinstance(fecha_meta, datetime):
            fecha_meta = fecha_meta.date()  # Convertir a solo fecha si es datetime
        elif isinstance(fecha_meta, str):  # Si fecha_meta es un string, convertirlo
            try:
                fecha_meta = datetime.strptime(fecha_meta, '%Y-%m-%d').date()
            except ValueError:
                continue  # Si no se puede convertir, se omite el registro

        # Ahora formatear la fecha correctamente
        reporte.append({"fecha_meta": fecha_meta.strftime('%Y-%m-%d'), "meta_ivee": meta[1]})

    return jsonify({"status": "success", "data": reporte}), 200



import pyodbc

def obtener_datos_por_agencia(fecha_seleccionada):
    # Establecer la conexión a la base de datos
    conexion = pyodbc.connect(
        "DRIVER={SQL Server};"
        "SERVER=ITZEL\\SQLEXPRESS01;"
        "DATABASE=estadia;"
        "UID=ITZEL;"
        "Trusted_Connection=yes;"
    )
    
    # Crear el cursor para ejecutar consultas
    cursor = conexion.cursor()
    
    # Consulta SQL para obtener los datos requeridos
    query = """
    SELECT agencia, ingresos, cobranza, dap
    FROM reporte
    WHERE fecha = ?
    """
    
    # Ejecutar la consulta con el parámetro de la fecha
    cursor.execute(query, (fecha_seleccionada,))
    
    # Obtener los resultados de la consulta
    total_por_agencia = {}
    for row in cursor.fetchall():
        agencia = row.agencia
        ingresos = row.ingresos
        cobranza = row.cobranza
        dap = row.dap
        
        # Guardar los datos en un diccionario
        total_por_agencia[agencia] = {
            'Ingresos': ingresos,
            'Cobranza Electrónica': cobranza,
            'DAP': dap,
            'Total': ingresos + cobranza + dap  # Sumar los montos
        }
    
    # Cerrar la conexión y el cursor
    cursor.close()
    conexion.close()
    
    return total_por_agencia


##CUADRE DE CAJAAAAAA



@app.route('/consulta_cuadre')  # Página principal
def consulta_cuadre():
    return render_template('consulta_cuadre.html')



@app.route('/verificar_fecha_cartera', methods=['POST'])
def verificar_fecha_cartera():
    fecha = request.json.get('fecha')
    if not fecha:
        return jsonify({"error": "Fecha no proporcionada"}), 400

    try:
        # Formatear la fecha si es necesario
        fecha_formateada = datetime.strptime(fecha, "%Y-%m-%d").strftime("%Y-%m-%d")
        print("Fecha formateada:", fecha_formateada)

        conexion = obtener_conexion()
        if not conexion:
            return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

        cursor = conexion.cursor()

        # Consulta SQL
        query = """
            SELECT COUNT(*)
            FROM Fecha_cuadre
            WHERE CAST(fecha_cuadre AS DATE) = CAST(? AS DATE)
        """
        cursor.execute(query, (fecha_formateada,))
        resultado = cursor.fetchone()

        if resultado is None:
            print("No se obtuvo ningún resultado de la consulta.")
            return jsonify({"existe_fecha": False})

        existe_fecha = resultado[0] > 0
        print(f"Resultado de la consulta: {resultado[0]}")

        cursor.close()
        conexion.close()

        return jsonify({"existe_fecha": existe_fecha})

    except Exception as e:
        print(f"Error inesperado: {str(e)}")
        return jsonify({"error": f"Error en la base de datos: {str(e)}"}), 500



@app.route('/consulta_cartera', methods=['GET', 'POST'])
def consulta_cartera():
    print(f"Método recibido: {request.method}")
    fecha = request.args.get('fecha')

    if not fecha:
        return "No se ha especificado una fecha.", 400

    totales_agencia = {}
    total_fresca = 0
    total_vencida = 0
    total_general = 0
    error = None

    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()

        # Consultar totales en la base de datos
        query = """
            SELECT 
                SUM(ta.total_fresca) AS total_fresca,
                SUM(ta.total_vencida) AS total_vencida
            FROM Total_agencia_diario ta
            INNER JOIN Fecha_cuadre fc ON ta.id_fecha_cuadre = fc.id_fecha_cuadre
            WHERE fc.fecha_cuadre = ?  
            GROUP BY fc.fecha_cuadre
        """
        cursor.execute(query, (fecha,))
        resultado = cursor.fetchone()

        if resultado:
            total_fresca = resultado[0]
            total_vencida = resultado[1]
            total_general = total_fresca + total_vencida
        else:
            error = f"No se encontraron datos para la fecha: {fecha}"

        # Consultar totales por agencia
        query_agencias = """
            SELECT 
                a.nombre_agencia AS agencia,
                ta.total_fresca,
                ta.total_vencida
            FROM Total_agencia_diario ta
            INNER JOIN Agencia a ON ta.id_agencia = a.id_agencia
            INNER JOIN Fecha_cuadre fc ON ta.id_fecha_cuadre = fc.id_fecha_cuadre
            WHERE fc.fecha_cuadre = ?
        """
        cursor.execute(query_agencias, (fecha,))
        totales_agencia = {fila[0]: {"Cartera Fresca": fila[1], "Cartera Vencida": fila[2]}
                           for fila in cursor.fetchall()}

    except Exception as db_error:
        print(f"Error al consultar la base de datos: {db_error}")
        error = f"Error al consultar la base de datos: {db_error}"
    finally:
        cursor.close()
        conexion.close()

    return render_template(
        'reporte_cartera.html',
        totales_agencia=totales_agencia,
        fecha=fecha,
        total_fresca=total_fresca,
        total_vencida=total_vencida,
        total_general=total_general,
        error=error
    )





    
    
@app.route('/procesar_archivo_cartera', methods=['POST'])
def procesar_archivo_cartera():
    archivo = request.files.get('archivo')
    fecha = request.args.get('fecha')  # La fecha es pasada como un parámetro en la URL

    if not archivo or not fecha:
        return jsonify({"error": "Archivo o fecha no proporcionado"}), 400

    try:
        # Validar la fecha proporcionada
        try:
            fecha = datetime.strptime(fecha, "%Y-%m-%d")
        except ValueError:
            return jsonify({"error": "Fecha proporcionada no es válida. Use el formato YYYY-MM-DD"}), 400

        # Procesar el archivo
        contenido = archivo.read().decode('utf-8')

        # Aquí puedes procesar el contenido del archivo según tu lógica, pasando la fecha como parámetro
        resultado = procesar_contenido_cartera(contenido, fecha)

        return jsonify({"mensaje": "Archivo procesado exitosamente", "resultado": resultado})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def procesar_contenido_cartera(contenido, fecha_archivo):
    # Definimos las agencias para la clasificación
    agencias = {'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'K': 6, 'W': 7, 'X': 8}
    totales_agencia = {codigo: {'Cartera Fresca': 0.0, 'Cartera Vencida': 0.0, 'Servicios Unicos': set()} 
                    for codigo in agencias.values()}

    # Patrones para extraer las fechas y otros datos
    patron_fecha_importe = r'\b(\d{2})(\d{2})(\d{4})?\b'  # Fecha de los importes (DDMM o DDMMYYYY)
    patron_fecha_cuadre = r'Cuadre De Caja De Operaciones Realizadas El Dia : (\d{2}) De (\w+) De (\d{4})'  # Fecha del cuadre de caja
    patron_rpu = r'\b\d{12}\b'
    patron_importe = r'\b[\d,]+\.\d{2}\b'
    patron_codigo_agencia = r'\b\w{16}\b'

    # Obtener el mes y el año de la fecha de cuadre de caja (fecha_archivo)
    dia_cuadre = fecha_archivo.day
    mes_cuadre = fecha_archivo.month
    anio_cuadre = fecha_archivo.year

    # Procesar las líneas del archivo
    for linea in contenido.splitlines():
        # Buscar la fecha de los importes (puede incluir año)
        fecha_en_linea_importe = re.search(patron_fecha_importe, linea)
        if fecha_en_linea_importe:
            dia = int(fecha_en_linea_importe.group(1))
            mes = int(fecha_en_linea_importe.group(2))
            anio = int(fecha_en_linea_importe.group(3)) if fecha_en_linea_importe.group(3) else anio_cuadre

            # Validar la fecha: ignorar fechas con año 0 o día/mes igual a 0
            if anio == 0 or dia == 0 or mes == 0:
                continue  # Saltar esta línea si la fecha no es válida

            # Verificar si la fecha de los importes es "fresca" o "vencida"
            if (anio < anio_cuadre) or (anio == anio_cuadre and mes < mes_cuadre):
                tipo_cartera = 'Cartera Vencida'
            else:
                tipo_cartera = 'Cartera Fresca'
        else:
            tipo_cartera = 'Desconocida'  # Si no se encuentra la fecha de los importes

        # Buscar el RPU, importe y código de agencia
        rpu = re.search(patron_rpu, linea)
        importe = re.search(patron_importe, linea)
        codigo_agencia = re.search(patron_codigo_agencia, linea)

        if rpu and importe and codigo_agencia:
            rpu = rpu.group()
            try:
                importe = float(importe.group().replace(',', ''))
            except ValueError:
                continue  # Si el importe no se puede convertir, saltamos esta línea

            agencia_char = codigo_agencia.group()[6]  # La agencia está en el 7mo carácter
            agencia_id = agencias.get(agencia_char)

            if agencia_id:
                # Clasificar el importe según la cartera fresca o vencida
                if tipo_cartera == 'Cartera Fresca':
                    totales_agencia[agencia_id]['Cartera Fresca'] += importe
                elif tipo_cartera == 'Cartera Vencida':
                    totales_agencia[agencia_id]['Cartera Vencida'] += importe

                # Agregar el RPU a los servicios únicos de la agencia
                totales_agencia[agencia_id]['Servicios Unicos'].add(rpu)

    # Convertir sets a números
    for agencia_id, datos in totales_agencia.items():
        datos['Servicios Unicos'] = len(datos['Servicios Unicos'])

    # Imprimir totales por agencia
    print("\nAgencia | Cartera Fresca | Cartera Vencida | Servicios Unicos | Total")
    for agencia_id, datos in totales_agencia.items():
        total_fresca = datos['Cartera Fresca']
        total_vencida = datos['Cartera Vencida']
        total_cartera = total_fresca + total_vencida
        total_servicios_unicos = datos['Servicios Unicos']
        print(f"{agencia_id:<7}| {total_fresca:<14.2f}| {total_vencida:<14.2f}| {total_servicios_unicos:<16}| {total_cartera:<10.2f}")

    # Verificar si el usuario es administrador y luego insertar los datos en la base de datos
    user_role = session.get('role', None)
    is_admin = user_role == 'administrador'
    print(f"El rol del usuario es: {user_role}")  # Verifica el valor del rol
    print(f"Es admin: {is_admin}")  # Verifica el valor de is_admin

    if is_admin:
        insertar_datos_base_datos(totales_agencia, fecha_archivo)

    # Mostrar total de servicios únicos procesados
    total_servicios_unicos = sum(datos['Servicios Unicos'] for datos in totales_agencia.values())
    print(f"\nTotal de servicios únicos procesados (RPUs): {total_servicios_unicos}")
    




def insertar_datos_base_datos(totales_agencia, fecha_archivo):
    # Insertar datos en la base de datos
    conn = connect_to_db()
    if conn:
        try:
            cursor = conn.cursor()

            # Insertar la fecha en Fecha_cuadre
            cursor.execute(
                "INSERT INTO Fecha_cuadre (fecha_cuadre) OUTPUT INSERTED.id_fecha_cuadre VALUES (?)",
                (fecha_archivo, )
            )
            id_fecha_cuadre = cursor.fetchone()[0]

            # Insertar totales generales
            total_fresca = sum(datos['Cartera Fresca'] for datos in totales_agencia.values())
            total_vencida = sum(datos['Cartera Vencida'] for datos in totales_agencia.values())
            total_cuadre = total_fresca + total_vencida

            cursor.execute(
                """
                INSERT INTO Total_cuadre (id_fecha_cuadre, total_fresca, total_vencida, total_cuadre)
                VALUES (?, ?, ?, ?)
                """,
                (id_fecha_cuadre, total_fresca, total_vencida, total_cuadre)
            )

            # Insertar totales por agencia
            for agencia_id, datos in totales_agencia.items():
                cursor.execute(
                    """
                    INSERT INTO Total_agencia_diario (id_agencia, id_fecha_cuadre, total_cartera, total_fresca, total_vencida)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (agencia_id, id_fecha_cuadre,
                     datos['Cartera Fresca'] + datos['Cartera Vencida'],
                     datos['Cartera Fresca'], datos['Cartera Vencida'])
                )

            conn.commit()
        except Exception as e:
            print(f"Error al insertar en la base de datos: {e}")
            conn.rollback()
        finally:
            conn.close()



@app.route('/eliminar_registros_cartera', methods=['POST'])
def eliminar_registros_cartera():
    fecha = request.form['fecha']  # Recibe la fecha a eliminar
    conn = connect_to_db()  # Conecta a la base de datos
    
    if conn is None:
        return jsonify({"status": "error", "message": "No se pudo conectar a la base de datos."})

    try:
        cursor = conn.cursor()  # Crea un cursor para ejecutar consultas
        
        # Eliminamos los registros de la tabla 'Total_agencia_diario'
        cursor.execute("""
            DELETE FROM Total_agencia_diario
            WHERE id_fecha_cuadre IN (
                SELECT id_fecha_cuadre FROM Fecha_cuadre WHERE fecha_cuadre = ?
            )
        """, (fecha,))
        
        # Eliminamos los registros de la tabla 'Total_cuadre'
        cursor.execute("""
            DELETE FROM Total_cuadre
            WHERE id_fecha_cuadre IN (
                SELECT id_fecha_cuadre FROM Fecha_cuadre WHERE fecha_cuadre = ?
            )
        """, (fecha,))
        
        # Finalmente, eliminamos los registros de la tabla 'Fecha_cuadre'
        cursor.execute("""
            DELETE FROM Fecha_cuadre
            WHERE fecha_cuadre = ?
        """, (fecha,))
        
        # Confirmamos los cambios
        conn.commit()
        
        return redirect(url_for('consulta_cuadre'))  # Correcto
    
    except Exception as e:
        # Si ocurre un error, hacemos rollback
        conn.rollback()
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": "Ocurrió un error al eliminar los registros."})
    
    finally:
        conn.close()  # Cerramos la conexión




@app.route('/cargar_archivo_cartera', methods=['POST'])
def cargar_archivo_cartera():
    try:
        # Verificar el rol del usuario desde la sesión
        role = session.get('role')  # Flask maneja session por ti
        print(f"Rol actual desde la sesión en Cargar_archivo_cartera: {role}")  # Depuración
        
        # Verificar que el archivo sea proporcionado y tenga la extensión correcta
        archivo = request.files.get('archivo')  # Flask maneja request por ti
        if not archivo or not archivo.filename.endswith('.txt'):
            return jsonify({"error": "El archivo debe ser de tipo .txt"}), 400
        
        # Leer el contenido del archivo sin guardarlo
        try:
            contenido = archivo.read().decode('utf-8')
        except UnicodeDecodeError as e:
            print(f"Error de decodificación al leer el archivo: {e}")
            return jsonify({"error": "Error al leer el archivo. Asegúrate de que el archivo esté en formato UTF-8."}), 400

        # Fecha actual para determinar si es "fresca" o "vencida"
        fecha_archivo = datetime.now()

        # Llamar a la función de procesamiento del archivo
        totales_agencia, fecha_archivo = procesar_archivo_cartera(contenido)

        # Si el rol es administrador, proceder a insertar los datos en la base de datos
        if role == 'administrador':
            try:
                insertar_datos_base_datos(totales_agencia, fecha_archivo)
            except Exception as e:
                # Error durante la inserción en la base de datos
                print(f"Error al insertar los datos en la base de datos: {e}")
                return jsonify({"error": f"Error al insertar los datos en la base de datos: {e}"}), 500
            
            # Si es administrador, puede insertar los datos y devolver el mensaje de éxito
            return render_template('reporte_cartera.html', 
                                   mensaje="Archivo procesado e insertado exitosamente", 
                                   totales_agencia=totales_agencia, 
                                   fecha_archivo=fecha_archivo)

        # Si no es administrador, solo devolver el procesamiento sin insertar
        return render_template('reporte_cartera.html', 
                               mensaje="Archivo procesado exitosamente", 
                               totales_agencia=totales_agencia, 
                               fecha_archivo=fecha_archivo)

    except Exception as e:
        # Manejo de errores generales
        print(f"Error general al cargar el archivo: {e}")
        return jsonify({"error": f"Error al cargar el archivo: {e}"}), 500



@app.route('/agencia/<int:agencia_id>', methods=['GET'])
def mostrar_servicios_agencia(agencia_id):
    # Obtener los totales de las agencias desde la sesión
    totales_agencia = session.get('totales_agencia', None)

    if not totales_agencia:
        return "No se han procesado datos", 404
    
    # Obtener los datos de la agencia específica
    datos_agencia = totales_agencia.get(agencia_id, None)
    
    # Si no hay datos para esa agencia
    if not datos_agencia:
        return "Agencia no encontrada", 404
    
    # Renderizar la plantilla con los datos
    return render_template('reporte_cartera.html', agencia_id=agencia_id, datos=datos_agencia)





@app.route('/reporte_cartera', methods=['GET', 'POST'])
def reporte_cartera():
    fecha_archivo = None
    totales_agencia = {}
    total_fresca = 0.0
    total_vencida = 0.0
    total_general = 0.0

    if request.method == 'POST':
        archivo = request.files.get('archivo')

        try:
            contenido = archivo.read().decode('utf-8')
            print("Procesando contenido del archivo...")

            # Llama a procesar_contenido_cartera y captura el resultado
            totales_agencia, fecha_archivo = procesar_contenido_cartera(contenido, datetime.now())

            # Depuración: imprime la fecha extraída o indica si no se encontró
            if fecha_archivo:
                print(f"Fecha extraída del archivo: {fecha_archivo.strftime('%Y-%m-%d')}")
            else:
                print("No se encontró una fecha válida en el archivo.")

            # Si no se encontró fecha, asigna "No disponible"
            if fecha_archivo is None:
                fecha_archivo = "No disponible"

            
            # Calcular totales
            for datos in totales_agencia.values():
                total_fresca += datos['Cartera Fresca']
                total_vencida += datos['Cartera Vencida']
            total_general = total_fresca + total_vencida

        except ValueError as ve:
            print(f"Error de valor: {ve}")
            return render_template('reporte_cartera.html', error=str(ve))
        except Exception as e:
            print(f"Error inesperado: {e}")
            return render_template('reporte_cartera.html', error=f"Error procesando el archivo: {str(e)}")

    return render_template(
        'reporte_cartera.html',
        totales_agencia=totales_agencia,
        fecha_archivo=fecha_archivo,
        total_fresca=total_fresca,
        total_vencida=total_vencida,
        total_general=total_general
    )





if __name__ == '__main__':
    app.run(debug=True)
    
