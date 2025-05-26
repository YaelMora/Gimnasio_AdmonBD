# Gimnasio_AdmonBD

Este proyecto es un prototipo de un sistema de reconocimiento facial de control de acceso para gimnasios con la finalidad de modernizar el proceso de registro y control de acceso de los usuarios
Este sistema tendrá una interfaz que permita a los administradores del gimnasio registrar nuevos usuarios, gestionar membresías y revisar registros de acceso, utilizando una base de datos relacional para almacenar la información de los usuarios y datos relacionados al gimnasio
Contará con un control de acceso por medio de un sistema de reconocimiento facial para identificar y autenticar a los usuarios.

Como Ejecutar
Es importante tener
-Camara web integrada o virtual
-instalar Python 3.11 o superior
-asegurar que este la ruta de instalación de Python en la variable path dentro de las variables de entorno
-Base de datos con mariDB
	Gestor de BD
		heidiDB
	Copiar o importat archivo database.sql y pegarlo en el gestor de SQL  y ejecutar todas las líneas de código

-IDE que ejecute python(recomendado Visual Studio Code)
instalar flask
	pip install flask
instalar flask-sql
	pip install flask-mysqldb
instalar openCV
	pip install opencv-python
	pip install opencv-contrib-python

instalar imutils
	pip install imutils
instalar bcrypt	
	pip install bcrypt


Ejecucion
para registrar un gerente la contraseña del admin es "admin"

Al usar el reconocimiento facial una ventana de python se abre, para ver mejor el reconocimeinto puedes abrirla, pero no es necesario interactuar
