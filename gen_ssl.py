# -*- coding: utf-8 -*-
"""Regenerate SSL certificate for current network IP"""
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
import datetime, ipaddress, socket, os

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(('8.8.8.8', 80))
IP = s.getsockname()[0]
s.close()
print(f'Current IP: {IP}')

key = rsa.generate_private_key(65537, 2048, default_backend())
subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'localhost')])
cert = x509.CertificateBuilder() \
    .subject_name(subject) \
    .issuer_name(subject) \
    .public_key(key.public_key()) \
    .serial_number(x509.random_serial_number()) \
    .not_valid_before(datetime.datetime.now(datetime.UTC)) \
    .not_valid_after(datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=365)) \
    .add_extension(x509.SubjectAlternativeName([
        x509.DNSName('localhost'),
        x509.IPAddress(ipaddress.IPv4Address('127.0.0.1')),
        x509.IPAddress(ipaddress.IPv4Address(IP)),
    ]), critical=False) \
    .sign(key, hashes.SHA256(), default_backend())

os.makedirs('ssl', exist_ok=True)
with open('ssl/key.pem', 'wb') as f:
    f.write(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
with open('ssl/cert.pem', 'wb') as f:
    f.write(cert.public_bytes(serialization.Encoding.PEM))

print(f'SSL cert generated for: localhost, 127.0.0.1, {IP}')
print(f'Phone access: https://{IP}:8080')
