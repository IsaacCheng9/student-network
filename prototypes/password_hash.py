import bcrypt

password = input("Enter password: ")
hash_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
print(hash_password)
