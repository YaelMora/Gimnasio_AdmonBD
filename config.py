# config.py

from flask_mysqldb import MySQL

#Como de crear usuario en MySQL en phpmyadmin
#dentro de phpmyadmin en la pagina de inicio (casita abajo del logo) vamos al apartado de cuentas de usuarios (en medio parte superior)
#abajo de la vista global dice agregar cuenta de usuario
#en nombre de usuario ingresa el de tu preferencia, el mismo que colocaras en la linea 17
#en nombre de host despliegas las opciones y seleccionas Local y automaticamente designa localhost
#ingresa la contraseña que colocaras en la linea 18
#le das todos los privilegios

class Config:
    DEBUG = True  # Modo depuración activado
    SECRET_KEY = 'many random bytes'  # Clave secreta para sesiones de Flask, NO SE CAMBIA
    MYSQL_HOST = 'localhost'  # Host de la base de datos MySQL, NORMALMENTE NO SE CAMBIA
    MYSQL_USER = 'root'  # Usuario de la base de datos recomendado ser root
    MYSQL_PASSWORD = 'root'  # Contraseña del usuario recomendado ser root
    MYSQL_DB = 'gimnasio_BD'  # Nombre de la base de datos MySQL, NOMBRE DE LA BD

mysql = MySQL()
