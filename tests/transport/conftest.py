#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
import datetime
import ssl
import tempfile
from typing import Generator

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.x509.oid import NameOID
from http_test import HTTPSTestServer, HTTPTestServer


@pytest.fixture(name="test_server", scope="module")
def test_server_fixture() -> Generator[HTTPTestServer, None, None]:
    with HTTPTestServer() as server:
        yield server


@pytest.fixture(name="private_key", scope="module")
def private_key_fixture() -> Ed25519PrivateKey:
    return Ed25519PrivateKey.generate()


@pytest.fixture(name="self_signed_certificate", scope="module")
def self_signed_certificate_fixture(private_key: Ed25519PrivateKey) -> x509.Certificate:
    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Meatie"),
            x509.NameAttribute(NameOID.COMMON_NAME, "github.com/pmateusz/meatie"),
        ]
    )
    return (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.now(datetime.timezone.utc))
        .not_valid_after(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=10))
        .add_extension(
            x509.SubjectAlternativeName(
                [
                    x509.DNSName("localhost"),
                ]
            ),
            critical=False,
        )
        .sign(private_key, None)
    )


@pytest.fixture(name="temp_dir", scope="module")
def temp_dir_fixture() -> Generator[str, None, None]:
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture(name="untrusted_context", scope="module")
def untrusted_context_fixture(
    temp_dir: str, private_key: Ed25519PrivateKey, self_signed_certificate: x509.Certificate
) -> ssl.SSLContext:
    key_file = temp_dir + "/key.pem"
    key_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    with open(key_file, "wb") as fs:
        fs.write(key_bytes)

    cert_bytes = self_signed_certificate.public_bytes(encoding=serialization.Encoding.PEM)
    cert_file = temp_dir + "/certificate.pem"
    with open(cert_file, "wb") as fs:
        fs.write(cert_bytes)

    context = ssl.SSLContext(protocol=ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(keyfile=key_file, certfile=cert_file)
    return context


@pytest.fixture(name="test_tls_server", scope="module")
def test_tls_server_fixture(
    untrusted_context: ssl.SSLContext,
) -> Generator[HTTPSTestServer, None, None]:
    with HTTPSTestServer(untrusted_context) as server:
        yield server
