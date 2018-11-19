import os
import json
from typing import Dict
from pathlib import Path

import logbook

from kryptos.settings import PROJECT_ID, EXCHANGE_AUTH_KEYRING
from kryptos.utils import storage_client


from google.cloud import kms_v1

key_client = kms_v1.KeyManagementServiceClient()


log = logbook.Logger("ExchangeAuth")


def get_auth_alias_path(user_id: str, exchange_name: str) -> str:
    home_dir = str(Path.home())
    exchange_dir = os.path.join(
        home_dir, ".catalyst/data/exchanges/", exchange_name.lower()
    )
    os.makedirs(exchange_dir, exist_ok=True)
    user_file = f"auth{user_id}.json"
    file_name = os.path.join(exchange_dir, user_file)
    return file_name


def decrypt_auth_key(
    user_id: int, exchange_name: str, ciphertext: bytes
) -> Dict[str, str]:
    """Decrypts auth data using google cloud KMS

    Args:
        user_id (int)
        exchange_name (str)
        ciphertext (bytes): encrypted data

    Returns:
        Dict[str, str]: Description
    """
    log.debug("decrypting exchange auth")
    key_path = key_client.crypto_key_path_path(
        PROJECT_ID, "global", EXCHANGE_AUTH_KEYRING, f"{exchange_name}_{user_id}_key"
    )

    response = key_client.decrypt(key_path, ciphertext)
    log.debug(f"successfully decrypted user {user_id} {exchange_name} auth")
    return json.loads(response.plaintext)


def get_encrypted_auth(user_id: int, exchange_name: str) -> bytes:
    """Fetches encrypted auth data as blob from storage bucket

    Args:
        user_id (int): Description
        exchange_name (str): Description

    Returns:
        bytes: ciphertext - encrypted auth json
    """

    log.debug("Fetching encrypted user exchange auth from storage")
    bucket = storage_client.get_bucket("catalyst_auth")
    blob = bucket.blob(f"auth_{exchange_name}_{user_id}_json")
    encrypted_text = blob.download_as_string()
    log.debug("obtained encrypted auth")
    return encrypted_text


def save_to_catalyst(
    user_id: int, exchange_name: str, auth_dict: Dict[str, str]
) -> None:
    """Saves decrypted auth data to catalyst dir"""
    file_name = get_auth_alias_path(user_id, exchange_name)

    with open(file_name, "w") as f:
        log.debug(f"Writing auth_json_str to {file_name}")
        json.dump(auth_dict, f)


def get_user_auth_alias(user_id: int, exchange_name: str) -> Dict[str, str]:
    """Fetches user exchange auth data and returns the catalyst auth alias

    Args:
        user_id (int): strategy's user ID
        exchange_name (str): name of exchange to to authenticate

    Returns:
        str: auth alias specifying json file for catalyst to use

    Returns:
        Dict[str, str]: auth alias specifying file for catalyst to use
    """
    encrypted = get_encrypted_auth(user_id, exchange_name)
    auth_dict = decrypt_auth_key(user_id, exchange_name, encrypted)
    save_to_catalyst(user_id, exchange_name, auth_dict)
    auth_alias = {exchange_name: f"auth{user_id}"}
    log.info("Fetched user auth and set up auth_alias")

    return auth_alias


def delete_alias_file(user_id: int, exchange_name: str) -> None:
    log.debug(f"Deleting user {user_id}'s {exchange_name} auth alias file")
    file_name = get_auth_alias_path(user_id, exchange_name)
    os.remove(file_name)
