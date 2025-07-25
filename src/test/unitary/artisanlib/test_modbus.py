import pytest


from artisanlib.main import ApplicationWindow
from artisanlib.modbusport import modbusport

@pytest.fixture
def aw() -> ApplicationWindow:
    parent = None
    locale:str = 'en'
    web_engine_support:bool = False
    artisan_viewer_first_start:bool = False
    return ApplicationWindow(parent, locale, web_engine_support, artisan_viewer_first_start) # type: ignore[misc]

@pytest.fixture
def client() -> modbusport:
    return modbusport(aw) # type: ignore[arg-type]

def test_word_order_default(client:modbusport) -> None:
    assert client.word_order() == 'little'

def test_convert_float_to_registers(client:modbusport) -> None:
    client.wordorderLittle = True
    assert client.convert_float_to_registers(12.2) == [13107, 16707]
    client.wordorderLittle = False
    assert client.convert_float_to_registers(12.2) == [16707, 13107]

def test_convert_16bit_uint_to_registers(client:modbusport) -> None:
    client.wordorderLittle = True
    assert client.convert_16bit_uint_to_registers(3451) == [3451]
    client.wordorderLittle = False
    assert client.convert_16bit_uint_to_registers(3451) == [3451]

def test_convert_32bit_int_to_registers(client:modbusport) -> None:
    client.wordorderLittle = True
    assert client.convert_32bit_int_to_registers(74510) == [8974, 1]
    assert client.convert_32bit_int_to_registers(-3451) == [62085, 65535]
    client.wordorderLittle = False
    assert client.convert_32bit_int_to_registers(74510) == [1, 8974]
    assert client.convert_32bit_int_to_registers(-3451) == [65535, 62085]

def test_convert_float_from_registers(client:modbusport) -> None:
    client.wordorderLittle = True
    assert pytest.approx(client.convert_float_from_registers([13107, 16707]), 0.01)  == 12.2
    client.wordorderLittle = False
    assert pytest.approx(client.convert_float_from_registers([16707, 13107]), 0.01) == 12.2

def test_convert_16bit_uint_from_registers(client:modbusport) -> None:
    client.wordorderLittle = True
    assert client.convert_16bit_uint_from_registers([13107]) == 13107
    client.wordorderLittle = False
    assert client.convert_16bit_uint_from_registers([13107]) == 13107

def test_convert_32bit_uint_from_registers(client:modbusport) -> None:
    client.wordorderLittle = True
    assert client.convert_32bit_uint_from_registers([321,12100]) == 792985921
    client.wordorderLittle = False
    assert client.convert_32bit_uint_from_registers([12100,321]) == 792985921

def test_convert_32bit_int_from_registers(client:modbusport) -> None:
    client.wordorderLittle = True
    assert client.convert_32bit_int_from_registers([13107, 12]) == 799539
    assert client.convert_32bit_int_from_registers([62085, 65535]) == -3451
    client.wordorderLittle = False
    assert client.convert_32bit_int_from_registers([12, 13107]) == 799539
    assert client.convert_32bit_int_from_registers([65535, 62085]) == -3451

def test_max_blocks(client:modbusport) -> None:
    assert client.max_blocks([0, 10]) == [(0, 10)]
    assert client.max_blocks([0, 99]) == [(0, 99)]
    assert client.max_blocks([0, 100]) == [(0,0), (100, 100)]
    assert client.max_blocks([1, 5, 112, 120]) == [(1, 5), (112, 120)]
    assert client.max_blocks([0, 2, 20, 1040, 1105, 1215]) == [(0, 20), (1040, 1105), (1215, 1215)]
    assert client.max_blocks([0, 99, 100, 199, 200, 299, 300, 320, 350]) == [(0, 99), (100, 199), (200, 299), (300, 350)]
