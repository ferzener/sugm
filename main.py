import os
import filelock
import json
import datetime
import hashlib
import uuid


# diretorio base dos dados
BASE_DIR = "/tmp/sugm"
# diretorio de usuarios
USERS_BASE_DIR = os.path.join(BASE_DIR, "users/")
# diretorio de grupos
GROUPS_FILE = os.path.join(BASE_DIR, "groups/")
# arquivo de tokens
TOKENS_FILE = os.path.join(BASE_DIR, "auth_tokens.json")
# TTL para os tokens (86400s == 1 dia)
TOKENS_TTL = 86400
USER_TOKENS_CORRELATION_FILE = os.path.join(BASE_DIR, "user_tokens_correlation.json")


# "banco de dados"
# ler arquivo
def read_file(cache_file: str, timeout: int = -1):
    """Safetly read data to cache."""
    with filelock.FileLock(f"{cache_file}.lock", timeout=timeout):
        if not os.path.exists(cache_file):
            return None
        with open(cache_file) as fd:
            try:
                return json.load(fd)
            except Exception:
                pass


# escrever arquivo
def write_file(cache_file: str, data: object, timeout: int = -1):
    """Safetly write data to cache."""
    with filelock.FileLock(f"{cache_file}.lock", timeout=timeout):
        with open(cache_file, "w") as fd:
            json.dump(data, fd)


# deletar arquivo
def delete_file(cache_file: str, timeout: int = -1):
    """Safely delete the cache file."""
    with filelock.FileLock(f"{cache_file}.lock", timeout=timeout):
        if os.path.exists(cache_file):
            os.remove(cache_file)


# gerar hash da senha do usuario
def calculate_sha256(content):
    return hashlib.sha256(content.encode()).hexdigest()


# criar usuario (com username nome sobrenome email e senha)
def create_user(
    username: str, first_name: str, last_name: str, email: str, password: str
):
    user_file_name = USERS_BASE_DIR + username + ".json"

    if os.path.exists(user_file_name):
        return (False, "Username already in use.")

    user = {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "password": calculate_sha256(password),
    }
    write_file(user_file_name, user)
    return (True, "User created with SUCCESS!")


# listar usuarios
def list_users():
    file_list = []
    for f in os.listdir(USERS_BASE_DIR):
        if not ".lock" in f and os.path.isfile(os.path.join(USERS_BASE_DIR, f)):
            file_list.append(f[:-5])
    return (len(file_list), file_list)


# deletar usuario
def delete_user(username):
    delete_file(USERS_BASE_DIR + username + ".json")
    delete_file(USERS_BASE_DIR + username + ".json.lock")


# atualizar dados do usuario (nome sobrenome email)
def update_user_data(username: str, first_name: str, last_name: str, email: str):
    user_file_name = USERS_BASE_DIR + username + ".json"

    if not os.path.exists(user_file_name):
        return (False, "User does not exists.")

    user = read_file(USERS_BASE_DIR + username + ".json")
    user["first_name"] = first_name if first_name else user["first_name"]
    user["last_name"] = last_name if last_name else user["last_name"]
    user["email"] = email if email else user["email"]
    write_file(user_file_name, user)
    return (True, "User data updated with SUCCESS!")


# autenticar usuario
def authenticate_user(username: str, password: str):
    user_file_name = USERS_BASE_DIR + username + ".json"

    if not os.path.exists(user_file_name):
        return (False, "User does not exists.")

    if (
        not calculate_sha256(password)
        == read_file(USERS_BASE_DIR + username + ".json")["password"]
    ):
        return (False, "Incorrect password.")

    token = str(uuid.uuid4())
    current_datetime = datetime.datetime.now()
    tokens = read_file(TOKENS_FILE)
    if not tokens:
        tokens = {}

    # create token and associate username
    tokens[token] = {
        "username": username,
    }
    write_file(TOKENS_FILE, tokens)

    # create user and token correlation and setting the created time of the token
    user_tokens_correlation = read_file(USER_TOKENS_CORRELATION_FILE)
    if not user_tokens_correlation:
        user_tokens_correlation = {}
    if username not in user_tokens_correlation:
        user_tokens_correlation[username] = {}
    user_tokens_correlation[username][token] = {
        "created_at": current_datetime.isoformat()
    }
    write_file(USER_TOKENS_CORRELATION_FILE, user_tokens_correlation)

    return (True, token)


# atualizar senha de usuario
def redefine_user_password(username: str, current_password: str, new_password: str):
    user_file_name = USERS_BASE_DIR + username + ".json"

    if not os.path.exists(user_file_name):
        return (False, "User does not exists.")

    user = read_file(USERS_BASE_DIR + username + ".json")
    if not calculate_sha256(current_password) == user["password"]:
        return (False, "Incorrect password.")

    user["password"] = calculate_sha256(new_password)
    write_file(user_file_name, user)
    return (True, "User password updated with SUCCESS!")


# resetar senha de usuario
# validar se token existe ou se ainda é valido
def is_token_valid(token: str):
    tokens = read_file(TOKENS_FILE) or {}
    user_tokens = read_file(USER_TOKENS_CORRELATION_FILE) or {}

    for user, tokens_map in user_tokens.items():
        if token in tokens_map:
            created_at_str = tokens_map[token]["created_at"]
            created_at = datetime.datetime.fromisoformat(created_at_str)
            now = datetime.datetime.now()
            age = (now - created_at).total_seconds()
            return age < TOKENS_TTL

    return False


# remover usuario

# criar grupo
# adicionar usuario a grupo
# remover usuario de grupo
# listar usuarios de grupo
# remover grupo


# testes
# create user
# print(
#    create_user(
#        "default_username",
#        "default_first_name",
#        "default_last_name",
#        "default_email",
#        "default_password",
#    )
# )
# list users
# print(list_users())
# update user data
# print(
#    update_user_data(
#        "default_username",
#        "default_first_name1",
#        "default_last_name1",
#        "default_email1",
#    )
# )
## delete user
# delete_user("default_username")
# print(list_users())
# create token
# print(authenticate_user("default_username", "default_password"))
# update user password
# redefine_user_password("default_username", "default_password", "default_password_1")
