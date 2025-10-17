import secrets
import string


def generate_password(length=14, use_mixed_case=True, use_symbols=True):
    """Generates a secure password based on specified criteria."""
    alphabet = string.ascii_lowercase
    if use_mixed_case:
        alphabet += string.ascii_uppercase
    if use_symbols:
        alphabet += string.punctuation

    # Ensure the password is complex enough if criteria are set
    password = ""
    while True:
        password = "".join(secrets.choice(alphabet) for _ in range(length))
        if not use_mixed_case and not use_symbols:
            break  # No need to check for complexity

        has_lower = any(c in string.ascii_lowercase for c in password)
        has_upper = not use_mixed_case or any(c in string.ascii_uppercase for c in password)
        has_symbol = not use_symbols or any(c in string.punctuation for c in password)

        if has_lower and has_upper and has_symbol:
            break

    return password
