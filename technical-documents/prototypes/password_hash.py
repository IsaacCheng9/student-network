# pip install passlib

from passlib.hash import sha256_crypt

password = sha256_crypt.hash("myPassword123")
password2 = sha256_crypt.hash("myPassword123")

print("password1 -> " + password)
print("password2 -> " + password2)

print(sha256_crypt.verify("myPassword123", password))
print(sha256_crypt.verify("myPassword1234", password))
