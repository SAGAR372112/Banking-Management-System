import secrets
import string

def generate_secret_key(length=50):
    chars = string.ascii_letters + string.digits + string.punctuation
    secret_key = ''.join(secrets.choice(chars) for _ in range(length))
    return secret_key

if __name__ == "__main__":
    print("Django SECRET_KEY:")
    print(generate_secret_key())