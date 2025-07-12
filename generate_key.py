from cryptography.fernet import Fernet

# Generate a proper Fernet encryption key
key = Fernet.generate_key()
print(f"DATABASE_ENCRYPTION_KEY={key.decode()}")
print(f"\nAdd this line to your .env file:")
print(f"DATABASE_ENCRYPTION_KEY={key.decode()}")