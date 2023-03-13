#!/usr/bin/env python3

"""
./speculos.py --log-level automation:DEBUG --automation file:$HOME/app-xrp/tests/automation.json ~/app-xrp/bin/app.elf &

export LEDGER_PROXY_ADDRESS=127.0.0.1 LEDGER_PROXY_PORT=9999
pytest-3 -v -s
"""
import os
import pytest
import pathlib
from contextlib import contextmanager
from time import sleep
from xrp import XRPClient, DEFAULT_PATH
from ledgerwallet.params import Bip32Path
from ragger.backend import RaisePolicy
from ragger.error import ExceptionRAPDU


def test_sign_too_large(backend, firmware, navigator):
    xrp = XRPClient(backend, firmware, navigator)
    max_size = 10001
    path = Bip32Path.build(DEFAULT_PATH)
    payload = path + b"a" * (max_size - 4)
    try:
        backend.raise_policy = RaisePolicy.RAISE_ALL_BUT_0x9000
        xrp.sign(payload, False)
    except ExceptionRAPDU as rapdu:
        assert rapdu.status in [0x6700, 0x6813]


def test_sign_invalid_tx(backend, firmware, navigator):
    xrp = XRPClient(backend, firmware, navigator)
    path = Bip32Path.build(DEFAULT_PATH)
    payload = path + b"a" * (40)
    try:
        backend.raise_policy = RaisePolicy.RAISE_ALL_BUT_0x9000
        xrp.sign(payload, False)
    except ExceptionRAPDU as rapdu:
        assert rapdu.status in [0x6803, 0x6807]


def test_path_too_long(backend, firmware, navigator):
    xrp = XRPClient(backend, firmware, navigator)
    path = Bip32Path.build(DEFAULT_PATH + "/0/0/0/0/0/0")
    try:
        xrp.get_pubkey(default_path=False, path=path)
    except ExceptionRAPDU as rapdu:
        assert rapdu.status == 0x6A80


def test_get_public_key(backend, firmware, navigator):
    xrp = XRPClient(backend, firmware, navigator)
    xrp.get_pubkey()


@contextmanager
def test_sign_valid_tx_and_compare_screens(backend, raw_tx_path, firmware, navigator):
    if firmware.device == "nanosp":
        pytest.skip(f"TODO : add tests for nanosp")
    sleep(1)
    xrp = XRPClient(backend, firmware, navigator)

    prefix = (
        os.path.dirname(os.path.realpath(__file__)) + f"/snapshots/{firmware.device}/"
    )
    full_snappath = pathlib.Path(
        raw_tx_path.replace("/testcases/", f"/snapshots/{firmware.device}/")
    ).with_suffix("")
    no_prefix_snappath = str(full_snappath)[len(prefix) :]

    if raw_tx_path.endswith("19-really-stupid-tx.raw"):
        pytest.skip(f"skip invalid tx {raw_tx_path}")

    with open(raw_tx_path, "rb") as fp:
        tx = fp.read()

    path = Bip32Path.build(DEFAULT_PATH)
    payload = path + tx
    xrp.sign(payload, True, no_prefix_snappath)
    assert xrp._client.last_async_response.status == 0x9000

    # Verify tx signature (Does not work...)
    # key = xrp.get_pubkey()
    # print(f"RECEIVED PUBKEY : {key}")
    # print(f"RECEIVED PUBKEY binascii: {binascii.hexlify(key)}")
    # print(f"RECEIVED PUBKEY binascii str:")
    # print(str(binascii.hexlify(key), encoding="utf-8"))
    # xrp.verify_ecdsa_secp256k1(tx, signature, str(binascii.hexlify(b'22'), encoding="utf-8"))
