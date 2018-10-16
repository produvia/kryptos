import os
import json
from typing import Dict, Tuple
from flask import current_app
from google.cloud import storage, kms_v1
from google.cloud.kms_v1 import enums

from google.api_core.exceptions import NotFound

key_client = kms_v1.KeyManagementServiceClient()
storage_client = storage.Client()


def create_user_exchange_key(user_id: int, exchange_name: str) -> str:
    current_app.logger.info("Creating new crypto key for user {} {} auth")
    keyring_path = key_client.key_ring_path(
        current_app.config["PROJECT_ID"], "global", "exchange_auth"
    )

    crypto_key_id = f"{exchange_name}_{user_id}_key"
    purpose = enums.CryptoKey.CryptoKeyPurpose.ENCRYPT_DECRYPT
    crypto_key = {"purpose": purpose}
    response = key_client.create_crypto_key(keyring_path, crypto_key_id, crypto_key)
    current_app.logger.debug(f"Created crypto key {response.name}")
    return response.name


def encrypt_user_auth(exchange_dict: Dict[str, str], user_id: int) -> bytes:
    exchange_name = exchange_dict["name"]
    current_app.logger.debug(f"Encrypting User {user_id} exchange auth for {exchange_name}")

    key_path = key_client.crypto_key_path_path(
        current_app.config["PROJECT_ID"],
        "global",
        "exchange_auth",
        f"{exchange_name}_{user_id}_key",
    )

    plaintext = json.dumps(exchange_dict).encode()

    try:
        resp = key_client.encrypt(key_path, plaintext)
    except NotFound:
        create_user_exchange_key(user_id, exchange_dict["name"])
        resp = key_client.encrypt(key_path, plaintext)

    current_app.logger.info("Successfully encrypted auth info")
    return resp.ciphertext


def upload_encrypted_auth(encrypted_text: bytes, user_id: int, exchange: str) -> Tuple[str, str]:
    current_app.logger.debug(f"Uploading encrypted {exchange} auth for user {user_id}")

    blob_name = f"auth_{exchange}_{user_id}_json"
    auth_bucket = storage_client.get_bucket("catalyst_auth")
    blob = auth_bucket.blob(blob_name)
    blob.upload_from_string(encrypted_text)
    current_app.logger.info(f"Uploaded encrypted auth with blob name {blob_name}")
    return blob_name, auth_bucket.name


def upload_user_auth(exchange_dict: Dict[str, str], user_id: int) -> Tuple[str, str]:
    encrypted = encrypt_user_auth(exchange_dict, user_id)
    return upload_encrypted_auth(encrypted, user_id, exchange_dict["name"])
