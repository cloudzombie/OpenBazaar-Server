# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: countries.proto

import sys

_b = sys.version_info[0] < 3 and (lambda x: x) or (lambda x: x.encode('latin1'))
from google.protobuf.internal import enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()

DESCRIPTOR = _descriptor.FileDescriptor(
    name='countries.proto',
    package='',
    serialized_pb=_b(
        '\n\x0f\x63ountries.proto*\xed\x01\n\x0b\x43ountryCode\x12\x06\n\x02NA\x10\x00\x12\x07\n\x03\x41LL\x10\x01\x12\x11\n\rNORTH_AMERICA\x10\x02\x12\x11\n\rSOUTH_AMERICA\x10\x03\x12\n\n\x06\x45UROPE\x10\x04\x12\n\n\x06\x41\x46RICA\x10\x05\x12\x08\n\x04\x41SIA\x10\x06\x12\r\n\tAUSTRALIA\x10\x07\x12\x11\n\rUNITED_STATES\x10\x08\x12\t\n\x05\x43HINA\x10\t\x12\t\n\x05JAPAN\x10\n\x12\x0b\n\x07GERMANY\x10\x0b\x12\x12\n\x0eUNITED_KINGDOM\x10\x0c\x12\n\n\x06\x46RANCE\x10\r\x12\n\n\x06\x42RAZIL\x10\x0e\x12\t\n\x05ITALY\x10\x0f\x12\t\n\x05INDIA\x10\x10')
)
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

_COUNTRYCODE = _descriptor.EnumDescriptor(
    name='CountryCode',
    full_name='CountryCode',
    filename=None,
    file=DESCRIPTOR,
    values=[
        _descriptor.EnumValueDescriptor(
            name='NA', index=0, number=0,
            options=None,
            type=None),
        _descriptor.EnumValueDescriptor(
            name='ALL', index=1, number=1,
            options=None,
            type=None),
        _descriptor.EnumValueDescriptor(
            name='NORTH_AMERICA', index=2, number=2,
            options=None,
            type=None),
        _descriptor.EnumValueDescriptor(
            name='SOUTH_AMERICA', index=3, number=3,
            options=None,
            type=None),
        _descriptor.EnumValueDescriptor(
            name='EUROPE', index=4, number=4,
            options=None,
            type=None),
        _descriptor.EnumValueDescriptor(
            name='AFRICA', index=5, number=5,
            options=None,
            type=None),
        _descriptor.EnumValueDescriptor(
            name='ASIA', index=6, number=6,
            options=None,
            type=None),
        _descriptor.EnumValueDescriptor(
            name='AUSTRALIA', index=7, number=7,
            options=None,
            type=None),
        _descriptor.EnumValueDescriptor(
            name='UNITED_STATES', index=8, number=8,
            options=None,
            type=None),
        _descriptor.EnumValueDescriptor(
            name='CHINA', index=9, number=9,
            options=None,
            type=None),
        _descriptor.EnumValueDescriptor(
            name='JAPAN', index=10, number=10,
            options=None,
            type=None),
        _descriptor.EnumValueDescriptor(
            name='GERMANY', index=11, number=11,
            options=None,
            type=None),
        _descriptor.EnumValueDescriptor(
            name='UNITED_KINGDOM', index=12, number=12,
            options=None,
            type=None),
        _descriptor.EnumValueDescriptor(
            name='FRANCE', index=13, number=13,
            options=None,
            type=None),
        _descriptor.EnumValueDescriptor(
            name='BRAZIL', index=14, number=14,
            options=None,
            type=None),
        _descriptor.EnumValueDescriptor(
            name='ITALY', index=15, number=15,
            options=None,
            type=None),
        _descriptor.EnumValueDescriptor(
            name='INDIA', index=16, number=16,
            options=None,
            type=None),
    ],
    containing_type=None,
    options=None,
    serialized_start=20,
    serialized_end=257,
)
_sym_db.RegisterEnumDescriptor(_COUNTRYCODE)

CountryCode = enum_type_wrapper.EnumTypeWrapper(_COUNTRYCODE)
NA = 0
ALL = 1
NORTH_AMERICA = 2
SOUTH_AMERICA = 3
EUROPE = 4
AFRICA = 5
ASIA = 6
AUSTRALIA = 7
UNITED_STATES = 8
CHINA = 9
JAPAN = 10
GERMANY = 11
UNITED_KINGDOM = 12
FRANCE = 13
BRAZIL = 14
ITALY = 15
INDIA = 16

DESCRIPTOR.enum_types_by_name['CountryCode'] = _COUNTRYCODE


# @@protoc_insertion_point(module_scope)
