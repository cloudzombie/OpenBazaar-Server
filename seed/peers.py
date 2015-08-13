# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: peers.proto

import sys

_b = sys.version_info[0] < 3 and (lambda x: x) or (lambda x: x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()

DESCRIPTOR = _descriptor.FileDescriptor(
    name='peers.proto',
    package='',
    serialized_pb=_b(
        '\n\x0bpeers.proto\"<\n\x08PeerData\x12\x12\n\nip_address\x18\x01 \x02' \
        '(\t\x12\x0c\n\x04port\x18\x02 \x02(\r\x12\x0e\n\x06vendor\x18\x03 \x02' \
        '(\x08\"1\n\tPeerSeeds\x12\x11\n\tpeer_data\x18\x01 \x03(\x0c\x12\x11\n\t' \
        'signature\x18\x02 \x02(\x0c')
)
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

_PEERDATA = _descriptor.Descriptor(
    name='PeerData',
    full_name='PeerData',
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(
            name='ip_address', full_name='PeerData.ip_address', index=0,
            number=1, type=9, cpp_type=9, label=2,
            has_default_value=False, default_value=_b("").decode('utf-8'),
            message_type=None, enum_type=None, containing_type=None,
            is_extension=False, extension_scope=None,
            options=None),
        _descriptor.FieldDescriptor(
            name='port', full_name='PeerData.port', index=1,
            number=2, type=13, cpp_type=3, label=2,
            has_default_value=False, default_value=0,
            message_type=None, enum_type=None, containing_type=None,
            is_extension=False, extension_scope=None,
            options=None),
        _descriptor.FieldDescriptor(
            name='vendor', full_name='PeerData.vendor', index=2,
            number=3, type=8, cpp_type=7, label=2,
            has_default_value=False, default_value=False,
            message_type=None, enum_type=None, containing_type=None,
            is_extension=False, extension_scope=None,
            options=None),
    ],
    extensions=[
    ],
    nested_types=[],
    enum_types=[
    ],
    options=None,
    is_extendable=False,
    extension_ranges=[],
    oneofs=[
    ],
    serialized_start=15,
    serialized_end=75,
)

_PEERSEEDS = _descriptor.Descriptor(
    name='PeerSeeds',
    full_name='PeerSeeds',
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(
            name='peer_data', full_name='PeerSeeds.peer_data', index=0,
            number=1, type=12, cpp_type=9, label=3,
            has_default_value=False, default_value=[],
            message_type=None, enum_type=None, containing_type=None,
            is_extension=False, extension_scope=None,
            options=None),
        _descriptor.FieldDescriptor(
            name='signature', full_name='PeerSeeds.signature', index=1,
            number=2, type=12, cpp_type=9, label=2,
            has_default_value=False, default_value=_b(""),
            message_type=None, enum_type=None, containing_type=None,
            is_extension=False, extension_scope=None,
            options=None),
    ],
    extensions=[
    ],
    nested_types=[],
    enum_types=[
    ],
    options=None,
    is_extendable=False,
    extension_ranges=[],
    oneofs=[
    ],
    serialized_start=77,
    serialized_end=126,
)

DESCRIPTOR.message_types_by_name['PeerData'] = _PEERDATA
DESCRIPTOR.message_types_by_name['PeerSeeds'] = _PEERSEEDS

PeerData = _reflection.GeneratedProtocolMessageType('PeerData', (_message.Message,), dict(
    DESCRIPTOR=_PEERDATA,
    __module__='peers_pb2'
    # @@protoc_insertion_point(class_scope:PeerData)
))
_sym_db.RegisterMessage(PeerData)

PeerSeeds = _reflection.GeneratedProtocolMessageType('PeerSeeds', (_message.Message,), dict(
    DESCRIPTOR=_PEERSEEDS,
    __module__='peers_pb2'
    # @@protoc_insertion_point(class_scope:PeerSeeds)
))
_sym_db.RegisterMessage(PeerSeeds)


# @@protoc_insertion_point(module_scope)
