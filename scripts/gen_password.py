import bcrypt

# Para cada usuario, genera su hash
print("CURADOR1_HASH=" + bcrypt.hashpw("1234".encode(), bcrypt.gensalt()).decode())
print("CURADOR2_HASH=" + bcrypt.hashpw("1234".encode(), bcrypt.gensalt()).decode())
print("CURADOR3_HASH=" + bcrypt.hashpw("1234".encode(), bcrypt.gensalt()).decode())
print("CURADOR4_HASH=" + bcrypt.hashpw("1234".encode(), bcrypt.gensalt()).decode())
print("CURADOR5_HASH=" + bcrypt.hashpw("1234".encode(), bcrypt.gensalt()).decode())
print("COMITE_HASH=" + bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode())