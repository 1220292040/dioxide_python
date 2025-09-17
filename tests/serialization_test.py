"""
PREDA数据序列化测试
基于PREDA规范的完整测试用例
"""

import pytest
from dioxide_python_sdk.utils.serializer import (
    serialize, deserialize, PredaSerializer,
    TypeValidationError, DeserializationError, UnsupportedTypeError
)


class TestPredaSpecCompliance:
    """PREDA规范符合性测试"""
    
    def test_integer_examples_from_spec(self):
        """测试PREDA规范中的整数示例"""
        test_cases = [
            ("int32", -1024, "00fcffff"),
            ("int128", -1024, "00fcffffffffffffffffffffffffffff"),
            ("uint64", 1023, "ff03000000000000"),
            ("uint256", 2047, "ff07000000000000000000000000000000000000000000000000000000000000"),
        ]
        
        for type_name, value, expected_hex in test_cases:
            # 测试序列化
            serialized = serialize(type_name, value)
            assert serialized.hex().lower() == expected_hex.lower(), \
                f"Serialization failed for {type_name}({value})"
            
            # 测试反序列化
            data = bytes.fromhex(expected_hex)
            deserialized, next_pos = deserialize(type_name, data, 0)
            assert deserialized == value, \
                f"Deserialization failed for {type_name}"
            assert next_pos == len(data), \
                f"Position mismatch for {type_name}"
    
    def test_float_examples_from_spec(self):
        """测试PREDA规范中的浮点数示例"""
        test_cases = [
            ("float256", 1.0, "41ffffffffffffff00000000000000000000000000000000000000000000008000cccccc"),
            ("float512", 1.0, "41feffffffffffff000000000000000000000000000000000000000000000000000000000000000000000000000000"),
        ]
        
        for type_name, value, expected_hex in test_cases:
            # 测试序列化
            serialized = serialize(type_name, value)
            assert serialized.hex().lower() == expected_hex.lower(), \
                f"Float serialization failed for {type_name}({value})"
            
            # 测试反序列化
            data = bytes.fromhex(expected_hex)
            deserialized, next_pos = deserialize(type_name, data, 0)
            assert abs(deserialized - value) < 1e-10, \
                f"Float deserialization failed for {type_name}"
    
    def test_array_example_from_spec(self):
        """测试PREDA规范中的数组示例: array<uint32> [1,2,3]"""
        expected_hex = "03000000010000000200000003000000"
        expected_value = [1, 2, 3]
        
        # 测试序列化
        serialized = serialize("array<uint32>", expected_value)
        assert serialized.hex().lower() == expected_hex.lower(), \
            "Array serialization failed"
        
        # 测试反序列化
        data = bytes.fromhex(expected_hex)
        deserialized, next_pos = deserialize("array<uint32>", data, 0)
        assert deserialized == expected_value, \
            "Array deserialization failed"
        assert next_pos == len(data), \
            "Array position mismatch"
    
    def test_map_example_from_spec(self):
        """测试PREDA规范中的映射示例: map<uint32,uint32> {0:1,100:2,400:5}"""
        expected_hex = "03000000000000006400000090010000010000000200000005000000"
        expected_value = {0: 1, 100: 2, 400: 5}
        
        # 测试序列化
        serialized = serialize("map<uint32,uint32>", expected_value)
        assert serialized.hex().lower() == expected_hex.lower(), \
            "Map serialization failed"
        
        # 测试反序列化
        data = bytes.fromhex(expected_hex)
        deserialized, next_pos = deserialize("map<uint32,uint32>", data, 0)
        assert deserialized == expected_value, \
            "Map deserialization failed"
        assert next_pos == len(data), \
            "Map position mismatch"
    
    def test_string_example_from_spec(self):
        """测试PREDA规范中的字符串示例: "hello" """
        expected_hex = "050068656c6c6f"
        expected_value = "hello"
        
        # 测试序列化
        serialized = serialize("string", expected_value)
        assert serialized.hex().lower() == expected_hex.lower(), \
            "String serialization failed"
        
        # 测试反序列化
        data = bytes.fromhex(expected_hex)
        deserialized, next_pos = deserialize("string", data, 0)
        assert deserialized == expected_value, \
            "String deserialization failed"
        assert next_pos == len(data), \
            "String position mismatch"
    
    def test_token_example_from_spec(self):
        """测试PREDA规范中的token示例: id=1, amount=4"""
        expected_hex = "0100000000000000010400000000000000"
        expected_value = {"id": 1, "amount": 4}
        
        # 测试序列化
        serialized = serialize("token", expected_value)
        assert serialized.hex().lower() == expected_hex.lower(), \
            "Token serialization failed"
        
        # 测试反序列化
        data = bytes.fromhex(expected_hex)
        deserialized, next_pos = deserialize("token", data, 0)
        assert deserialized == expected_value, \
            "Token deserialization failed"
        assert next_pos == len(data), \
            "Token position mismatch"
    
    def test_bigint_example_from_spec(self):
        """测试PREDA规范中的bigint示例"""
        # 正数bigint示例
        spec_hex = "03c7711cc7711c0b4de3051d6b170fb62c38743f9a07000000"
        
        # 测试反序列化结构
        data = bytes.fromhex(spec_hex)
        deserialized, next_pos = deserialize("bigint", data, 0)
        
        # 验证是正数且有正确的结构
        assert isinstance(deserialized, int), "Bigint should be integer"
        assert deserialized > 0, "Spec example should be positive"
        assert next_pos == len(data), "Position should match data length"
        
        # 测试简单bigint值的往返
        simple_cases = [
            0, 1, 4, 255, 65535, 4294967295, -1, -4, -255
        ]
        
        for value in simple_cases:
            serialized = serialize("bigint", value)
            deserialized, _ = deserialize("bigint", serialized, 0)
            assert deserialized == value, f"Bigint round-trip failed for {value}"


class TestFixedSizeTypes:
    """固定大小类型测试"""
    
    def test_bool_type(self):
        """测试bool类型"""
        test_cases = [
            (True, "01"),
            (False, "00"),
        ]
        
        for value, expected_hex in test_cases:
            serialized = serialize("bool", value)
            assert serialized.hex().lower() == expected_hex.lower()
            
            data = bytes.fromhex(expected_hex)
            deserialized, next_pos = deserialize("bool", data, 0)
            assert deserialized == value
            assert next_pos == 1
    
    def test_uint_types(self):
        """测试无符号整数类型"""
        test_cases = [
            ("uint8", 255, "ff"),
            ("uint16", 65535, "ffff"),
            ("uint32", 4294967295, "ffffffff"),
            ("uint64", 1023, "ff03000000000000"),  # 来自PREDA规范
        ]
        
        for type_name, value, expected_hex in test_cases:
            serialized = serialize(type_name, value)
            assert serialized.hex().lower() == expected_hex.lower()
            
            data = bytes.fromhex(expected_hex)
            deserialized, next_pos = deserialize(type_name, data, 0)
            assert deserialized == value
    
    def test_int_types(self):
        """测试有符号整数类型"""
        test_cases = [
            ("int8", -1, "ff"),
            ("int16", -1, "ffff"),
            ("int32", -1024, "00fcffff"),  # 来自PREDA规范
            ("int64", -1, "ffffffffffffffff"),
        ]
        
        for type_name, value, expected_hex in test_cases:
            serialized = serialize(type_name, value)
            assert serialized.hex().lower() == expected_hex.lower()
            
            data = bytes.fromhex(expected_hex)
            deserialized, next_pos = deserialize(type_name, data, 0)
            assert deserialized == value
    
    def test_fixed_bytes_types(self):
        """测试固定字节类型: blob, hash, address"""
        test_cases = [
            ("hash", b"\x64" + b"\x00" * 31, 32),
            ("address", b"\x00\x63" + b"\x00" * 34, 36),
            ("blob", b"\x64" + b"\x00" * 35, 36),
        ]
        
        for type_name, test_data, expected_size in test_cases:
            assert len(test_data) == expected_size
            
            serialized = serialize(type_name, test_data)
            assert serialized == test_data
            
            deserialized, next_pos = deserialize(type_name, serialized, 0)
            assert deserialized == test_data
            assert next_pos == expected_size
    
    def test_enum_type(self):
        """测试枚举类型"""
        test_cases = [
            (0, "0000"),
            (1, "0100"),
            (255, "ff00"),
            (65535, "ffff"),
        ]
        
        for value, expected_hex in test_cases:
            serialized = serialize("enum", value)
            assert serialized.hex().lower() == expected_hex.lower()
            
            data = bytes.fromhex(expected_hex)
            deserialized, next_pos = deserialize("enum", data, 0)
            assert deserialized == value
            assert next_pos == 2


class TestVariableSizeTypes:
    """可变大小类型测试"""
    
    def test_string_type(self):
        """测试字符串类型"""
        test_cases = [
            ("hello", "050068656c6c6f"),  # 来自PREDA规范
            ("", "0000"),                # 空字符串
            ("a", "010061"),             # 单字符
            ("world", "0500776f726c64"), # 另一个单词
        ]
        
        for string_value, expected_hex in test_cases:
            serialized = serialize("string", string_value)
            assert serialized.hex().lower() == expected_hex.lower()
            
            data = bytes.fromhex(expected_hex)
            deserialized, next_pos = deserialize("string", data, 0)
            assert deserialized == string_value
            assert next_pos == len(data)
    
    def test_array_type(self):
        """测试数组类型"""
        test_cases = [
            ("uint32", [1, 2, 3], "03000000010000000200000003000000"),  # 来自PREDA规范
            ("uint32", [], "00000000"),                                   # 空数组
            ("uint32", [42], "0100000042000000"),                        # 单元素
            ("uint8", [255, 0, 128], "03000000ff0080"),                  # 字节数组
        ]
        
        for element_type, array_value, expected_hex in test_cases:
            type_name = f"array<{element_type}>"
            serialized = serialize(type_name, array_value)
            assert serialized.hex().lower() == expected_hex.lower()
            
            data = bytes.fromhex(expected_hex)
            deserialized, next_pos = deserialize(type_name, data, 0)
            assert deserialized == array_value
            assert next_pos == len(data)
    
    def test_map_type(self):
        """测试映射类型"""
        test_cases = [
            ("uint32", "uint32", {0: 1, 100: 2, 400: 5}, 
             "03000000000000006400000090010000010000000200000005000000"),  # 来自PREDA规范
            ("uint32", "uint32", {}, "00000000"),                           # 空映射
        ]
        
        for key_type, value_type, map_value, expected_hex in test_cases:
            type_name = f"map<{key_type},{value_type}>"
            serialized = serialize(type_name, map_value)
            assert serialized.hex().lower() == expected_hex.lower()
            
            data = bytes.fromhex(expected_hex)
            deserialized, next_pos = deserialize(type_name, data, 0)
            assert deserialized == map_value
            assert next_pos == len(data)


class TestErrorHandling:
    """错误处理测试"""
    
    def test_type_validation_errors(self):
        """测试类型验证错误"""
        with pytest.raises(TypeValidationError):
            serialize("uint8", 256)  # 超出范围
        
        with pytest.raises(TypeValidationError):
            serialize("uint8", -1)   # 负数
        
        with pytest.raises(TypeValidationError):
            serialize("int8", 128)   # 超出范围
        
        with pytest.raises(TypeValidationError):
            serialize("hash", b"\x01" * 31)  # 长度错误
    
    def test_unsupported_type_errors(self):
        """测试不支持的类型错误"""
        with pytest.raises(UnsupportedTypeError):
            serialize("uint7", 1)    # 无效位宽
        
        with pytest.raises(UnsupportedTypeError):
            serialize("unknown", 1)  # 未知类型
    
    def test_deserialization_errors(self):
        """测试反序列化错误"""
        with pytest.raises(DeserializationError):
            deserialize("uint32", b"\x01\x02", 0)  # 数据不足
        
        with pytest.raises(DeserializationError):
            deserialize("string", b"\xff\xfe", 0)  # 无效UTF-8


class TestRoundTripConsistency:
    """往返一致性测试"""
    
    def test_integer_round_trip(self):
        """测试整数类型往返一致性"""
        test_cases = [
            ("uint8", [0, 1, 127, 255]),
            ("uint16", [0, 1, 32767, 65535]),
            ("uint32", [0, 1, 2147483647, 4294967295]),
            ("int8", [-128, -1, 0, 1, 127]),
            ("int16", [-32768, -1, 0, 1, 32767]),
            ("int32", [-2147483648, -1024, 0, 1024, 2147483647]),
        ]
        
        for type_name, values in test_cases:
            for value in values:
                serialized = serialize(type_name, value)
                deserialized, _ = deserialize(type_name, serialized, 0)
                assert deserialized == value, f"Round-trip failed for {type_name}({value})"
    
    def test_complex_type_round_trip(self):
        """测试复杂类型往返一致性"""
        test_cases = [
            ("string", ["", "hello", "world", "测试中文"]),
            ("array<uint32>", [[], [1], [1, 2, 3, 4, 5]]),
            ("map<uint32,string>", [{}, {1: "one"}, {1: "one", 2: "two", 3: "three"}]),
            ("bigint", [0, 1, -1, 4, -4, 1234567890, -1234567890]),
            ("token", [{"id": 0, "amount": 0}, {"id": 1, "amount": 4}, {"id": 999, "amount": -100}]),
        ]
        
        for type_name, values in test_cases:
            for value in values:
                serialized = serialize(type_name, value)
                deserialized, _ = deserialize(type_name, serialized, 0)
                assert deserialized == value, f"Round-trip failed for {type_name}({value})"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
