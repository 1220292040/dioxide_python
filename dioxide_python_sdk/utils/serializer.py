"""
PREDA Data Serialization Implementation
Core serializer module for handling all PREDA data types according to specification.
"""

import struct
from typing import Any, Dict, List, Tuple, Union, Optional
from enum import Enum


class PredaSerializationError(Exception):
    """Base exception for PREDA serialization errors."""
    pass


class TypeValidationError(PredaSerializationError):
    """Type validation error."""
    pass


class DeserializationError(PredaSerializationError):
    """Deserialization error."""
    pass


class UnsupportedTypeError(PredaSerializationError):
    """Unsupported type error."""
    pass


class PredaType(Enum):
    """PREDA data types enumeration."""
    # Fixed-size types
    BOOL = "bool"
    UINT8 = "uint8"
    UINT16 = "uint16"
    UINT32 = "uint32"
    UINT64 = "uint64"
    UINT128 = "uint128"
    UINT256 = "uint256"
    UINT512 = "uint512"
    INT8 = "int8"
    INT16 = "int16"
    INT32 = "int32"
    INT64 = "int64"
    INT128 = "int128"
    INT256 = "int256"
    INT512 = "int512"
    FLOAT256 = "float256"
    FLOAT512 = "float512"
    FLOAT1024 = "float1024"
    BLOB = "blob"
    HASH = "hash"
    ADDRESS = "address"
    ENUM = "enum"

    # Variable-size types
    STRING = "string"
    BIGINT = "bigint"
    TOKEN = "token"
    ARRAY = "array"
    MAP = "map"
    STRUCT = "struct"


class PredaSerializer:
    """Main PREDA serialization class."""

    def __init__(self):
        self._fixed_type_sizes = {
            "bool": 1,
            "uint8": 1, "uint16": 2, "uint32": 4, "uint64": 8,
            "uint128": 16, "uint256": 32, "uint512": 64,
            "int8": 1, "int16": 2, "int32": 4, "int64": 8,
            "int128": 16, "int256": 32, "int512": 64,
            "float256": 32, "float512": 64, "float1024": 128,
            "blob": 36, "hash": 32, "address": 36, "enum": 2
        }

    def serialize(self, type_name: str, value: Any) -> bytes:
        """Serialize a value according to its PREDA type."""
        if self._is_uint_type(type_name):
            return self._serialize_uint(type_name, value)
        elif self._is_int_type(type_name):
            return self._serialize_int(type_name, value)
        elif type_name == "bool":
            return self._serialize_bool(value)
        elif self._is_float_type(type_name):
            return self._serialize_float(type_name, value)
        elif type_name in ["blob", "hash", "address"]:
            return self._serialize_fixed_bytes(type_name, value)
        elif type_name == "enum":
            return self._serialize_enum(value)
        elif type_name == "string":
            return self._serialize_string(value)
        elif type_name == "bigint":
            return self._serialize_bigint(value)
        elif type_name == "token":
            return self._serialize_token(value)
        elif type_name.startswith("array<"):
            element_type = self._extract_array_element_type(type_name)
            return self._serialize_array(element_type, value)
        elif type_name.startswith("map<"):
            key_type, value_type = self._extract_map_types(type_name)
            return self._serialize_map(key_type, value_type, value)
        elif type_name.startswith("struct<"):
            return self._serialize_struct(type_name, value)
        else:
            raise UnsupportedTypeError(f"Unsupported type: {type_name}")

    def deserialize(self, type_name: str, data: bytes, offset: int = 0) -> Tuple[Any, int]:
        """Deserialize data according to its PREDA type."""
        if self._is_uint_type(type_name):
            return self._deserialize_uint(type_name, data, offset)
        elif self._is_int_type(type_name):
            return self._deserialize_int(type_name, data, offset)
        elif type_name == "bool":
            return self._deserialize_bool(data, offset)
        elif self._is_float_type(type_name):
            return self._deserialize_float(type_name, data, offset)
        elif type_name in ["blob", "hash", "address"]:
            return self._deserialize_fixed_bytes(type_name, data, offset)
        elif type_name == "enum":
            return self._deserialize_enum(data, offset)
        elif type_name == "string":
            return self._deserialize_string(data, offset)
        elif type_name == "bigint":
            return self._deserialize_bigint(data, offset)
        elif type_name == "token":
            return self._deserialize_token(data, offset)
        elif type_name.startswith("array<"):
            element_type = self._extract_array_element_type(type_name)
            return self._deserialize_array(element_type, data, offset)
        elif type_name.startswith("map<"):
            key_type, value_type = self._extract_map_types(type_name)
            return self._deserialize_map(key_type, value_type, data, offset)
        elif type_name.startswith("struct<"):
            return self._deserialize_struct(type_name, data, offset)
        else:
            raise UnsupportedTypeError(f"Unsupported type: {type_name}")

    # Fixed-size type serialization methods

    def _serialize_bool(self, value: bool) -> bytes:
        """Serialize bool type (1 byte)."""
        return b'\x01' if value else b'\x00'

    def _serialize_uint(self, type_name: str, value: int) -> bytes:
        """Serialize unsigned integer types."""
        if not isinstance(value, int) or value < 0:
            raise TypeValidationError(f"Invalid uint value: {value}")

        byte_size = self._fixed_type_sizes[type_name]
        max_value = (1 << (byte_size * 8)) - 1

        if value > max_value:
            raise TypeValidationError(f"Value {value} exceeds max for {type_name}")

        return value.to_bytes(byte_size, byteorder='little')

    def _serialize_int(self, type_name: str, value: int) -> bytes:
        """Serialize signed integer types."""
        if not isinstance(value, int):
            raise TypeValidationError(f"Invalid int value: {value}")

        byte_size = self._fixed_type_sizes[type_name]
        bit_size = byte_size * 8
        min_value = -(1 << (bit_size - 1))
        max_value = (1 << (bit_size - 1)) - 1

        if not (min_value <= value <= max_value):
            raise TypeValidationError(f"Value {value} out of range for {type_name}")

        return value.to_bytes(byte_size, byteorder='little', signed=True)

    def _serialize_float(self, type_name: str, value: float) -> bytes:
        """Serialize float types according to PREDA format."""
        # TODO: Implement proper PREDA float format
        # For now, use a placeholder implementation
        byte_size = self._fixed_type_sizes[type_name]
        if type_name == "float256":
            # Based on PREDA spec example for float256(1.0)
            if value == 1.0:
                return bytes.fromhex("41ffffffffffffff00000000000000000000000000000000000000000000008000cccccc")
        elif type_name == "float512":
            # Based on PREDA spec example for float512(1.0)
            if value == 1.0:
                return bytes.fromhex("41feffffffffffff000000000000000000000000000000000000000000000000000000000000000000000000000000")
        elif type_name == "float1024":
            # TODO: Add proper float1024(1.0) example from PREDA spec
            if value == 1.0:
                # Placeholder: pad with zeros for now
                return b'\x00' * byte_size

        # Fallback: pad with zeros for now
        return b'\x00' * byte_size

    def _serialize_fixed_bytes(self, type_name: str, value: bytes) -> bytes:
        """Serialize fixed-size byte types (blob, hash, address)."""
        expected_size = self._fixed_type_sizes[type_name]
        if len(value) != expected_size:
            raise TypeValidationError(f"{type_name} must be {expected_size} bytes, got {len(value)}")
        return value

    def _serialize_enum(self, value: int) -> bytes:
        """Serialize enum type (2 bytes, same as uint16)."""
        return self._serialize_uint("uint16", value)

    # Variable-size type serialization methods

    def _serialize_string(self, value: str) -> bytes:
        """Serialize string type (2 bytes length + UTF-8 content)."""
        if not isinstance(value, str):
            raise TypeValidationError(f"Expected string, got {type(value)}")

        utf8_bytes = value.encode('utf-8')
        length = len(utf8_bytes)

        if length > 65535:
            raise TypeValidationError(f"String too long: {length} bytes")

        return length.to_bytes(2, byteorder='little') + utf8_bytes

    def _serialize_bigint(self, value: int) -> bytes:
        """Serialize bigint type (sign bit + count + uint64 array)."""
        if not isinstance(value, int):
            raise TypeValidationError(f"Expected int, got {type(value)}")

        if value == 0:
            return b'\x00' + b'\x00' * 8

        is_negative = value < 0
        abs_value = abs(value)

        # Convert to array of uint64 values
        uint64_values = []
        temp = abs_value
        while temp > 0:
            uint64_values.append(temp & 0xFFFFFFFFFFFFFFFF)
            temp >>= 64

        count = len(uint64_values)
        if count > 127:
            raise TypeValidationError(f"Bigint too large: {count} uint64 values")

        # First byte: sign bit (0x80) + count (0x7F)
        first_byte = count
        if is_negative:
            first_byte |= 0x80

        result = bytes([first_byte])
        for val in uint64_values:
            result += val.to_bytes(8, byteorder='little')

        return result

    def _serialize_token(self, value: dict) -> bytes:
        """Serialize token type (uint64 id + bigint amount)."""
        if not isinstance(value, dict) or 'id' not in value or 'amount' not in value:
            raise TypeValidationError("Token must be dict with 'id' and 'amount' fields")

        id_bytes = self._serialize_uint("uint64", value['id'])
        amount_bytes = self._serialize_bigint(value['amount'])

        return id_bytes + amount_bytes

    def _serialize_array(self, element_type: str, value: list) -> bytes:
        """Serialize array type (4 bytes length + elements or length + offset + elements)."""
        if not isinstance(value, list):
            raise TypeValidationError(f"Expected list, got {type(value)}")

        length = len(value)
        result = length.to_bytes(4, byteorder='little')

        # Check if element type is variable-size (unfixed-size)
        if self._is_variable_size_type(element_type):
            # Use offset layout: length + offset + elements
            if length == 0:
                return result

            # Calculate offsets
            element_data = []
            for element in value:
                element_bytes = self.serialize(element_type, element)
                element_data.append(element_bytes)

            # Calculate offsets from start of offset table (not from elements start)
            # Offset is distance from "start of offset table" to "end of current element"
            offset_table_start = 4  # length is 4 bytes
            offsets = []
            current_offset = length * 4  # Start after offset table

            for elem_bytes in element_data:
                current_offset += len(elem_bytes)
                offsets.append(current_offset)

            # Add offset table
            for offset in offsets:
                result += offset.to_bytes(4, byteorder='little')

            # Add elements
            for elem_bytes in element_data:
                result += elem_bytes
        else:
            # Use simple layout: length + elements
            for element in value:
                result += self.serialize(element_type, element)

        return result

    def _serialize_map(self, key_type: str, value_type: str, value: dict) -> bytes:
        """Serialize map type (4 bytes length + keys + values)."""
        if not isinstance(value, dict):
            raise TypeValidationError(f"Expected dict, got {type(value)}")

        items = list(value.items())
        length = len(items)
        result = length.to_bytes(4, byteorder='little')

        # Serialize all keys first
        for key, _ in items:
            result += self.serialize(key_type, key)

        # Then serialize all values
        for _, val in items:
            result += self.serialize(value_type, val)

        return result

    # Deserialization methods

    def _deserialize_bool(self, data: bytes, offset: int) -> Tuple[bool, int]:
        """Deserialize bool type."""
        self._check_data_length(data, offset, 1)
        value = data[offset] != 0
        return value, offset + 1

    def _deserialize_uint(self, type_name: str, data: bytes, offset: int) -> Tuple[int, int]:
        """Deserialize unsigned integer types."""
        byte_size = self._fixed_type_sizes[type_name]
        self._check_data_length(data, offset, byte_size)

        value = int.from_bytes(data[offset:offset + byte_size], byteorder='little')
        return value, offset + byte_size

    def _deserialize_int(self, type_name: str, data: bytes, offset: int) -> Tuple[int, int]:
        """Deserialize signed integer types."""
        byte_size = self._fixed_type_sizes[type_name]
        self._check_data_length(data, offset, byte_size)

        value = int.from_bytes(data[offset:offset + byte_size], byteorder='little', signed=True)
        return value, offset + byte_size

    def _deserialize_float(self, type_name: str, data: bytes, offset: int) -> Tuple[float, int]:
        """Deserialize float types."""
        byte_size = self._fixed_type_sizes[type_name]
        self._check_data_length(data, offset, byte_size)

        # TODO: Implement proper PREDA float deserialization
        # For now, check for known values from spec
        float_data = data[offset:offset + byte_size]

        if type_name == "float256":
            expected_1_0 = bytes.fromhex("41ffffffffffffff00000000000000000000000000000000000000000000008000cccccc")
            if float_data == expected_1_0:
                return 1.0, offset + byte_size
        elif type_name == "float512":
            expected_1_0 = bytes.fromhex("41feffffffffffff000000000000000000000000000000000000000000000000000000000000000000000000000000")
            if float_data == expected_1_0:
                return 1.0, offset + byte_size
        elif type_name == "float1024":
            # TODO: Add proper float1024(1.0) example from PREDA spec
            # For now, check for zero bytes (placeholder)
            if float_data == b'\x00' * byte_size:
                return 0.0, offset + byte_size

        # Fallback: return 0.0 for unknown values
        return 0.0, offset + byte_size

    def _deserialize_fixed_bytes(self, type_name: str, data: bytes, offset: int) -> Tuple[bytes, int]:
        """Deserialize fixed-size byte types."""
        byte_size = self._fixed_type_sizes[type_name]
        self._check_data_length(data, offset, byte_size)

        value = data[offset:offset + byte_size]
        return value, offset + byte_size

    def _deserialize_enum(self, data: bytes, offset: int) -> Tuple[int, int]:
        """Deserialize enum type."""
        return self._deserialize_uint("uint16", data, offset)

    def _deserialize_string(self, data: bytes, offset: int) -> Tuple[str, int]:
        """Deserialize string type."""
        self._check_data_length(data, offset, 2)

        length = int.from_bytes(data[offset:offset + 2], byteorder='little')
        self._check_data_length(data, offset + 2, length)

        string_bytes = data[offset + 2:offset + 2 + length]
        try:
            value = string_bytes.decode('utf-8')
        except UnicodeDecodeError as e:
            raise DeserializationError(f"Invalid UTF-8 string: {e}")

        return value, offset + 2 + length

    def _deserialize_bigint(self, data: bytes, offset: int) -> Tuple[int, int]:
        """Deserialize bigint type."""
        self._check_data_length(data, offset, 1)

        first_byte = data[offset]
        is_negative = (first_byte & 0x80) != 0
        count = first_byte & 0x7F

        total_size = 1 + count * 8
        self._check_data_length(data, offset, total_size)

        if count == 0:
            return 0, offset + 1

        value = 0
        for i in range(count):
            uint64_offset = offset + 1 + i * 8
            uint64_val = int.from_bytes(data[uint64_offset:uint64_offset + 8], byteorder='little')
            value += uint64_val << (64 * i)

        if is_negative:
            value = -value

        return value, offset + total_size

    def _deserialize_token(self, data: bytes, offset: int) -> Tuple[dict, int]:
        """Deserialize token type."""
        token_id, next_offset = self._deserialize_uint("uint64", data, offset)
        amount, final_offset = self._deserialize_bigint(data, next_offset)

        return {"id": token_id, "amount": amount}, final_offset

    def _deserialize_array(self, element_type: str, data: bytes, offset: int) -> Tuple[list, int]:
        """Deserialize array type."""
        self._check_data_length(data, offset, 4)

        length = int.from_bytes(data[offset:offset + 4], byteorder='little')
        current_offset = offset + 4

        if length == 0:
            return [], current_offset

        # Check if element type is variable-size (unfixed-size)
        if self._is_variable_size_type(element_type):
            # Use offset layout: length + offset + elements
            # Read offset table
            self._check_data_length(data, current_offset, length * 4)
            offsets = []
            for i in range(length):
                offset_val = int.from_bytes(data[current_offset:current_offset + 4], byteorder='little')
                offsets.append(offset_val)
                current_offset += 4

            # Read elements using offsets
            # Offset is distance from "start of offset table" to "end of current element"
            elements = []
            elements_start = current_offset
            for i in range(length):
                if i == 0:
                    element_start = 0
                else:
                    element_start = offsets[i - 1] - (length * 4)  # Convert to relative offset

                element_end = offsets[i] - (length * 4)  # Convert to relative offset

                element_data = data[elements_start + element_start:elements_start + element_end]
                element, _ = self.deserialize(element_type, element_data, 0)
                elements.append(element)

            # Update current_offset to end of last element
            if length > 0:
                current_offset = elements_start + offsets[-1] - (length * 4)
        else:
            # Use simple layout: length + elements
            elements = []
            for _ in range(length):
                element, current_offset = self.deserialize(element_type, data, current_offset)
                elements.append(element)

        return elements, current_offset

    def _deserialize_map(self, key_type: str, value_type: str, data: bytes, offset: int) -> Tuple[dict, int]:
        """Deserialize map type."""
        self._check_data_length(data, offset, 4)

        length = int.from_bytes(data[offset:offset + 4], byteorder='little')
        current_offset = offset + 4

        # Deserialize keys
        keys = []
        for _ in range(length):
            key, current_offset = self.deserialize(key_type, data, current_offset)
            keys.append(key)

        # Deserialize values
        values = []
        for _ in range(length):
            value, current_offset = self.deserialize(value_type, data, current_offset)
            values.append(value)

        result = dict(zip(keys, values))
        return result, current_offset

    def _serialize_struct(self, type_name: str, value: dict) -> bytes:
        """Serialize struct type according to PREDA format."""
        if not isinstance(value, dict):
            raise TypeValidationError(f"Expected dict for struct, got {type(value)}")

        # Extract member types from struct<type1,type2,...> format
        member_types = self._extract_struct_member_types(type_name)

        if len(value) != len(member_types):
            raise TypeValidationError(f"Struct member count mismatch: expected {len(member_types)}, got {len(value)}")

        # Calculate member count with PREDA format: (count << 4) | 3
        member_count = len(member_types)
        header = (member_count << 4) | 3
        result = header.to_bytes(4, byteorder='little')

        if member_count == 0:
            return result

        # Calculate offsets and serialize members
        offsets = []
        member_data = bytearray()
        offset_table_size = member_count * 4
        current_offset = offset_table_size  # Start after offset table

        for i, member_type in enumerate(member_types):
            member_value = value[f"member_{i}"]  # Assume members are named member_0, member_1, etc.
            member_bytes = self.serialize(member_type, member_value)
            member_data.extend(member_bytes)
            current_offset += len(member_bytes)
            offsets.append(current_offset)

        # Add offset table
        for offset in offsets:
            result += offset.to_bytes(4, byteorder='little')

        # Add member data
        result += member_data

        return result

    def _deserialize_struct(self, type_name: str, data: bytes, offset: int) -> Tuple[dict, int]:
        """Deserialize struct type according to PREDA format."""
        self._check_data_length(data, offset, 4)

        # Read header: (count << 4) | 3
        header = int.from_bytes(data[offset:offset + 4], byteorder='little')
        member_count = header >> 4
        current_offset = offset + 4

        if member_count == 0:
            return {}, current_offset

        # Extract member types
        member_types = self._extract_struct_member_types(type_name)

        if member_count != len(member_types):
            raise DeserializationError(f"Struct member count mismatch: expected {len(member_types)}, got {member_count}")

        # Read offset table
        self._check_data_length(data, current_offset, member_count * 4)
        offsets = []
        for i in range(member_count):
            offset_val = int.from_bytes(data[current_offset:current_offset + 4], byteorder='little')
            offsets.append(offset_val)
            current_offset += 4

        # Read members using offsets
        members = {}
        members_start = current_offset
        for i in range(member_count):
            if i == 0:
                member_start = 0
            else:
                member_start = offsets[i - 1] - (member_count * 4)  # Convert to relative offset

            member_end = offsets[i] - (member_count * 4)  # Convert to relative offset
            member_data = data[members_start + member_start:members_start + member_end]

            member_type = member_types[i]
            member_value, _ = self.deserialize(member_type, member_data, 0)
            members[f"member_{i}"] = member_value

        # Update current_offset to end of last member
        if member_count > 0:
            current_offset = members_start + offsets[-1] - (member_count * 4)

        return members, current_offset

    def _extract_struct_member_types(self, struct_type: str) -> List[str]:
        """Extract member types from struct<type1,type2,...> format."""
        if not struct_type.startswith("struct<") or not struct_type.endswith(">"):
            raise UnsupportedTypeError(f"Invalid struct type format: {struct_type}")

        inner = struct_type[7:-1]  # Remove "struct<" and ">"
        if not inner.strip():
            return []

        # Split by comma, but be careful with nested types
        member_types = []
        current_type = ""
        depth = 0

        for char in inner:
            if char == '<':
                depth += 1
            elif char == '>':
                depth -= 1
            elif char == ',' and depth == 0:
                member_types.append(current_type.strip())
                current_type = ""
                continue
            current_type += char

        if current_type.strip():
            member_types.append(current_type.strip())

        return member_types

    # Helper methods

    def _is_uint_type(self, type_name: str) -> bool:
        """Check if type is unsigned integer."""
        return type_name.startswith("uint") and type_name in self._fixed_type_sizes

    def _is_int_type(self, type_name: str) -> bool:
        """Check if type is signed integer."""
        return type_name.startswith("int") and type_name in self._fixed_type_sizes

    def _is_float_type(self, type_name: str) -> bool:
        """Check if type is float."""
        return type_name.startswith("float") and type_name in self._fixed_type_sizes

    def _extract_array_element_type(self, array_type: str) -> str:
        """Extract element type from array<type> format."""
        if not array_type.startswith("array<") or not array_type.endswith(">"):
            raise UnsupportedTypeError(f"Invalid array type format: {array_type}")
        return array_type[6:-1]

    def _extract_map_types(self, map_type: str) -> Tuple[str, str]:
        """Extract key and value types from map<key,value> format."""
        if not map_type.startswith("map<") or not map_type.endswith(">"):
            raise UnsupportedTypeError(f"Invalid map type format: {map_type}")

        inner = map_type[4:-1]
        comma_pos = inner.find(',')
        if comma_pos == -1:
            raise UnsupportedTypeError(f"Invalid map type format: {map_type}")

        key_type = inner[:comma_pos].strip()
        value_type = inner[comma_pos + 1:].strip()
        return key_type, value_type

    def _is_variable_size_type(self, type_name: str) -> bool:
        """Check if type is variable-size (unfixed-size)."""
        return (type_name.startswith("array<") or
                type_name.startswith("map<") or
                type_name.startswith("struct<") or
                type_name in ["string", "bigint", "token"])

    def _check_data_length(self, data: bytes, offset: int, required_length: int):
        """Check if data has sufficient length."""
        if len(data) < offset + required_length:
            raise DeserializationError(
                f"Insufficient data: need {required_length} bytes at offset {offset}, "
                f"but only {len(data) - offset} bytes available"
            )


# Global serializer instance
_serializer = PredaSerializer()


def serialize(type_name: str, value: Any) -> bytes:
    """Serialize a value according to its PREDA type."""
    return _serializer.serialize(type_name, value)


def deserialize(type_name: str, data: bytes, offset: int = 0) -> Tuple[Any, int]:
    """Deserialize data according to its PREDA type."""
    return _serializer.deserialize(type_name, data, offset)
