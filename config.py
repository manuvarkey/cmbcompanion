import os

WTF_CSRF_ENABLED = True
SECRET_KEY = 'cmbautomiser_secret_cpwdcpesd'
    
basedir = os.path.abspath(os.path.dirname(__file__))

UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
ALLOWED_EXTENSIONS = set(['proj'])
