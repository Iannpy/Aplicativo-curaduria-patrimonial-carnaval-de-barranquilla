from src.database.models import UsuarioModel
import bcrypt

# Crear usuario comité
password = "2026"
hash_pass = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
UsuarioModel.crear_usuario("comite", hash_pass, "comite")
print("Usuario comité creado")
exit()