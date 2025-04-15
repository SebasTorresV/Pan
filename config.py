import os

class Config:
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = '1234'
    MYSQL_DATABASE = 'panaderia_bernal'

    SECRET_KEY = 'f9f92d6f84ee16d730922d67780fe6ad'

    # Configuración para carga de imágenes
    UPLOAD_FOLDER = os.path.join('app', 'static', 'uploads')
    MAX_CONTENT_LENGTH = 20 * 1024 * 1024  # 20 MB
