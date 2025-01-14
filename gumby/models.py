import enum
import uuid

from elasticsearch_dsl import (
    Boolean,
    Date,
    Document,
    GeoPoint,
    Index,
    InnerDoc,
    Keyword,
    Nested,
    ValidationException,
)


# FFF Ported from Python >=3.10
class StrEnum(str, enum.Enum):
    """
    Enum where members are also (and must be) strings
    """

    def __new__(cls, *values):
        if len(values) > 3:
            raise TypeError('too many arguments for str(): %r' % (values, ))
        if len(values) == 1:
            # it must be a string
            if not isinstance(values[0], str):
                raise TypeError('%r is not a string' % (values[0], ))
        if len(values) >= 2:
            # check that encoding argument is a string
            if not isinstance(values[1], str):
                raise TypeError('encoding must be a string, not %r' % (values[1], ))
        if len(values) == 3:
            # check that errors argument is a string
            if not isinstance(values[2], str):
                raise TypeError('errors must be a string, not %r' % (values[2]))
        value = str(*values)
        member = str.__new__(cls, value)
        member._value_ = value
        return member

    __str__ = str.__str__

    def _generate_next_value_(name, start, count, last_values):
        """
        Return the lower-cased version of the member name.
        """
        return name.lower()


class Sex(StrEnum):
    unknown = enum.auto()
    non_binary = 'non-binary'
    female = enum.auto()
    male = enum.auto()


class EnumField(Keyword):
    """Custom keyword field"""
    _coerce = True

    def __init__(self, enum, *args, **kwargs):
        self._enum = enum
        super().__init__(*args, **kwargs)

    def clean(self, data):
        super().clean(data)
        if not (data in list(self._enum) or data is None):
            valid_options = ', '.join([str(n) for n in self._enum])
            raise ValidationException(f"'{data}' is not one the the valid options: {valid_options}")
        return data

    def _deserialize(self, data):
        if data is None:
            return None
        elif isinstance(data, self._enum):
            return data
        # Key name may not match string value name, otherwise `self._enum[data]` would work.
        return [x for x in self._enum if str(x) == data][0]

    def _serialize(self, data):
        if data is None:
            return None
        elif isinstance(data, self._enum):
            return str(data)
        return str(data)


class UUIDField(Keyword):
    """Custom UUID keyword field"""
    _coerce = True

    def _deserialize(self, data):
        if data is None:
            return None
        elif isinstance(data, uuid.UUID):
            return data
        return uuid.UUID(data)

    def _serialize(self, data):
        if data is None:
            return None
        elif isinstance(data, uuid.UUID):
            return str(data)
        return str(data)


class Encounter(InnerDoc):
    id = UUIDField(required=True)
    point = GeoPoint(required=True)
    animate_status = Keyword()
    sex = EnumField(Sex, required=False)
    submitter_id = Keyword(required=True)
    date_occurred = Date()
    genus = Keyword()
    species = Keyword()
    has_annotation = Boolean(required=True)


class Individual(Document):
    id = UUIDField(required=True)
    name = Keyword()
    alias = Keyword()
    genus = Keyword()
    species = Keyword()
    last_sighting = Date()
    sex = EnumField(Sex, required=False)

    encounters = Nested(Encounter)

    class Index:
        name = 'individuals'
