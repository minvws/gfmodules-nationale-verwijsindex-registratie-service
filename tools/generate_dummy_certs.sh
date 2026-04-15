#!/bin/bash
set -e

#
# Script to generate dummy certificates for local development of the NVI-RS.
# Creates self-signed CA certificates and dummy UZI/LDN server certificates
# in the secrets/ directory, which are used for mTLS authentication.
#
# Usage: ./tools/generate_dummy_certs.sh [URA_NUMBER]
# Example: ./tools/generate_dummy_certs.sh 12345678
#

URA_NUMBER=${1:-12345678}
SECRET_DIR=secrets

echo "Generating dummy certificates for local development (URA: $URA_NUMBER)."

mkdir -p "$SECRET_DIR"

create_ca() {
    local name=$1
    openssl req -x509 -newkey rsa:2048 -sha256 -nodes \
        -keyout "$SECRET_DIR/$name.key" \
        -out "$SECRET_DIR/$name.crt" \
        -days 500 \
        -subj "/C=NL/O=$name/CN=dummy $name Root CA" \
        -addext "basicConstraints=critical,CA:TRUE" \
        -addext "keyUsage=critical,keyCertSign,cRLSign" \
        -addext "subjectKeyIdentifier=hash" 2>/dev/null
}

sign_cert() {
    local cert_name=$1
    local ca_name=$2

    openssl x509 -req -days 500 -sha256 \
        -in "$SECRET_DIR/$cert_name.csr" \
        -CA "$SECRET_DIR/$ca_name.crt" \
        -CAkey "$SECRET_DIR/$ca_name.key" \
        -CAcreateserial \
        -copy_extensions copyall \
        -out "$SECRET_DIR/$cert_name.crt" 2>/dev/null
}

# Create CA certificates
create_ca "uzi-server-ca"
create_ca "ldn-server-ca"

# Create a dummy UZI server certificate (contains URA number in SAN)
openssl req -nodes -newkey rsa:2048 \
    -keyout "$SECRET_DIR/dummy-uzi.key" \
    -out "$SECRET_DIR/dummy-uzi.csr" \
    -subj "/C=NL/O=MockTest Cert/CN=test.example.org/serialNumber=$URA_NUMBER" \
    -addext "subjectAltName = otherName:2.5.5.5;IA5STRING:2.16.528.1.1003.1.3.5.5.2-1-$URA_NUMBER-S-$URA_NUMBER-00.000-00000000" \
    2>/dev/null
sign_cert dummy-uzi uzi-server-ca

# Create a dummy LDN server certificate
openssl req -nodes -newkey rsa:2048 \
    -keyout "$SECRET_DIR/dummy-ldn.key" \
    -out "$SECRET_DIR/dummy-ldn.csr" \
    -subj "/C=NL/O=MockTest Cert/CN=test.example.org/serialNumber=$URA_NUMBER" \
    -addext "keyUsage=critical,digitalSignature,keyEncipherment" \
    -addext "basicConstraints=critical,CA:FALSE" \
    -addext "extendedKeyUsage=serverAuth,clientAuth" \
    2>/dev/null
sign_cert dummy-ldn ldn-server-ca

rm -f "$SECRET_DIR"/*.csr "$SECRET_DIR"/*.srl

echo "Done. Generated files:"
ls "$SECRET_DIR"
