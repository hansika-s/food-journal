from pwdlib import PasswordHash

# Argon2 with the library's recommended settings. Created once and reused.
hasher = PasswordHash.recommended()


# Returns the hash, which includes the salt and settings
def hash_password(password: str) -> str:
    return hasher.hash(password)


# Returns True if the plain password matches the stored hash
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hasher.verify(plain_password, hashed_password)
