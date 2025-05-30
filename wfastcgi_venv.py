import os
import sys

# Ruta al entorno virtual
venv_base = r"C:\DV_APP_IIS\dv_importmoca\.venv"

# Añadir site-packages y Scripts a sys.path
sys.path.insert(0, os.path.join(venv_base, 'Lib', 'site-packages'))
sys.path.insert(0, os.path.join(venv_base, 'Scripts'))

# Añadir también el directorio del proyecto
sys.path.insert(0, r"C:\DV_APP_IIS\dv_importmoca")

# Establecer VIRTUAL_ENV y PATH
os.environ['VIRTUAL_ENV'] = venv_base
os.environ['PATH'] = os.path.join(venv_base, 'Scripts') + ';' + os.environ['PATH']

# Forzar el subdirectorio de esta app
os.environ['SCRIPT_NAME'] = '/importmoca'

# Lanzar wfastcgi
try:
    from wfastcgi import main
    main()
except Exception as e:
    sys.stderr.write("Error ejecutando wfastcgi: {}\n".format(e))
    raise

