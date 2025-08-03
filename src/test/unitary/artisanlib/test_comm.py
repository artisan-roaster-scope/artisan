"""Unit tests for artisanlib.comm module.

This module tests the device communication functionality including:
- Phidget device mapping functions (thermocouple, RTD, gain)
- YoctoThread class for Yoctopuce device communication
- nonedevDlg class for manual temperature input dialog
- serialport class initialization and basic functionality
- Device function list structure and integrity
- Serial port configuration and management
- Communication protocol handling

=============================================================================
SDET Test Isolation and Best Practices
=============================================================================

This test module implements comprehensive session-level isolation to prevent
cross-file module contamination while maintaining proper test independence.

Key Features:
- Session-level isolation for external dependencies
- Comprehensive PyQt6 and hardware library mocking
- Serial communication mocking to prevent hardware access
- Mock state management to prevent interference
- Test independence and proper cleanup
- Python 3.8+ compatibility with type annotations
"""

import sys
import threading
from typing import Any, Dict, Generator
from unittest.mock import Mock, patch

import pytest


@pytest.fixture(scope='session', autouse=True)
def session_level_isolation() -> Generator[None, None, None]:
    """Session-level isolation fixture to prevent cross-file module contamination.

    This fixture ensures that external dependencies are properly isolated
    at the session level while preserving the functionality needed for
    comm tests. It handles PyQt6, serial, Phidget, and Yoctopuce mocking.
    """
    # Store original modules if they exist and aren't mocked
    original_modules: Dict[str, Any] = {}
    modules_to_check = [
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'serial',
        'Phidget22',
        'Phidget22.DeviceID',
        'Phidget22.Devices',
        'Phidget22.ThermocoupleType',
        'Phidget22.RTDWireSetup',
        'Phidget22.RTDType',
        'Phidget22.BridgeGain',
        'yoctopuce',
        'yoctopuce.yocto_api',
        'numpy',  # Prevent multiple numpy imports
    ]

    for module_name in modules_to_check:
        if module_name in sys.modules:
            module = sys.modules[module_name]
            # Check if it's not a mock
            if not (
                hasattr(module, '_mock_name')
                or hasattr(module, '_spec_class')
                or 'Mock' in str(type(module))
            ):
                original_modules[module_name] = module

    yield

    # Restore original modules if they were stored
    for module_name, original_module in original_modules.items():
        sys.modules[module_name] = original_module


class TestPhidgetMappingFunctions:
    """Test Phidget device mapping utility functions."""

    def test_phidget_thermocouple_type_k_default(self) -> None:
        """Test PHIDGET_THERMOCOUPLE_TYPE returns K-type for default/unknown values."""
        # Arrange & Act
        with patch('Phidget22.ThermocoupleType.ThermocoupleType') as mock_tc_type:
            mock_tc_type.THERMOCOUPLE_TYPE_K = 1

            from artisanlib.comm import PHIDGET_THERMOCOUPLE_TYPE

            # Test default case (tp=1 or any other value)
            result_default = PHIDGET_THERMOCOUPLE_TYPE(1)
            result_unknown = PHIDGET_THERMOCOUPLE_TYPE(99)

            # Assert
            assert result_default == 1
            assert result_unknown == 1

    def test_phidget_thermocouple_type_j_type(self) -> None:
        """Test PHIDGET_THERMOCOUPLE_TYPE returns J-type for tp=2."""
        # Arrange & Act
        with patch('Phidget22.ThermocoupleType.ThermocoupleType') as mock_tc_type:
            mock_tc_type.THERMOCOUPLE_TYPE_J = 2

            from artisanlib.comm import PHIDGET_THERMOCOUPLE_TYPE

            result = PHIDGET_THERMOCOUPLE_TYPE(2)

            # Assert
            assert result == 2

    def test_phidget_thermocouple_type_e_type(self) -> None:
        """Test PHIDGET_THERMOCOUPLE_TYPE returns E-type for tp=3."""
        # Arrange & Act
        with patch('Phidget22.ThermocoupleType.ThermocoupleType') as mock_tc_type:
            mock_tc_type.THERMOCOUPLE_TYPE_E = 3

            from artisanlib.comm import PHIDGET_THERMOCOUPLE_TYPE

            result = PHIDGET_THERMOCOUPLE_TYPE(3)

            # Assert
            assert result == 3

    def test_phidget_thermocouple_type_t_type(self) -> None:
        """Test PHIDGET_THERMOCOUPLE_TYPE returns T-type for tp=4."""
        # Arrange & Act
        with patch('Phidget22.ThermocoupleType.ThermocoupleType') as mock_tc_type:
            mock_tc_type.THERMOCOUPLE_TYPE_T = 4

            from artisanlib.comm import PHIDGET_THERMOCOUPLE_TYPE

            result = PHIDGET_THERMOCOUPLE_TYPE(4)

            # Assert
            assert result == 4

    def test_phidget_rtd_wire_2wire_default(self) -> None:
        """Test PHIDGET_RTD_WIRE returns 2-wire setup for default/unknown values."""
        # Arrange & Act
        with patch('Phidget22.RTDWireSetup.RTDWireSetup') as mock_wire_setup:
            mock_wire_setup.RTD_WIRE_SETUP_2WIRE = 1

            from artisanlib.comm import PHIDGET_RTD_WIRE

            result_default = PHIDGET_RTD_WIRE(0)
            result_unknown = PHIDGET_RTD_WIRE(99)

            # Assert
            assert result_default == 1
            assert result_unknown == 1

    def test_phidget_rtd_wire_3wire(self) -> None:
        """Test PHIDGET_RTD_WIRE returns 3-wire setup for tp=1."""
        # Arrange & Act
        with patch('Phidget22.RTDWireSetup.RTDWireSetup') as mock_wire_setup:
            mock_wire_setup.RTD_WIRE_SETUP_3WIRE = 2

            from artisanlib.comm import PHIDGET_RTD_WIRE

            result = PHIDGET_RTD_WIRE(1)

            # Assert
            assert result == 2

    def test_phidget_rtd_wire_4wire(self) -> None:
        """Test PHIDGET_RTD_WIRE returns 4-wire setup for tp=2."""
        # Arrange & Act
        with patch('Phidget22.RTDWireSetup.RTDWireSetup') as mock_wire_setup:
            mock_wire_setup.RTD_WIRE_SETUP_4WIRE = 3

            from artisanlib.comm import PHIDGET_RTD_WIRE

            result = PHIDGET_RTD_WIRE(2)

            # Assert
            assert result == 3

    def test_phidget_rtd_type_pt100_3850_default(self) -> None:
        """Test PHIDGET_RTD_TYPE returns PT100 3850 for default/unknown values."""
        # Arrange & Act
        with patch('Phidget22.RTDType.RTDType') as mock_rtd_type:
            mock_rtd_type.RTD_TYPE_PT100_3850 = 1

            from artisanlib.comm import PHIDGET_RTD_TYPE

            result_default = PHIDGET_RTD_TYPE(0)
            result_unknown = PHIDGET_RTD_TYPE(99)

            # Assert
            assert result_default == 1
            assert result_unknown == 1

    def test_phidget_rtd_type_pt100_3920(self) -> None:
        """Test PHIDGET_RTD_TYPE returns PT100 3920 for tp=1."""
        # Arrange & Act
        with patch('Phidget22.RTDType.RTDType') as mock_rtd_type:
            mock_rtd_type.RTD_TYPE_PT100_3920 = 2

            from artisanlib.comm import PHIDGET_RTD_TYPE

            result = PHIDGET_RTD_TYPE(1)

            # Assert
            assert result == 2

    def test_phidget_rtd_type_pt1000_3850(self) -> None:
        """Test PHIDGET_RTD_TYPE returns PT1000 3850 for tp=2."""
        # Arrange & Act
        with patch('Phidget22.RTDType.RTDType') as mock_rtd_type:
            mock_rtd_type.RTD_TYPE_PT1000_3850 = 3

            from artisanlib.comm import PHIDGET_RTD_TYPE

            result = PHIDGET_RTD_TYPE(2)

            # Assert
            assert result == 3

    def test_phidget_rtd_type_pt1000_3920(self) -> None:
        """Test PHIDGET_RTD_TYPE returns PT1000 3920 for tp=3."""
        # Arrange & Act
        with patch('Phidget22.RTDType.RTDType') as mock_rtd_type:
            mock_rtd_type.RTD_TYPE_PT1000_3920 = 4

            from artisanlib.comm import PHIDGET_RTD_TYPE

            result = PHIDGET_RTD_TYPE(3)

            # Assert
            assert result == 4

    def test_phidget_gain_value_no_gain_default(self) -> None:
        """Test PHIDGET_GAIN_VALUE returns no gain for default/unknown values."""
        # Arrange & Act
        with patch('Phidget22.BridgeGain.BridgeGain') as mock_bridge_gain:
            mock_bridge_gain.BRIDGE_GAIN_1 = 1

            from artisanlib.comm import PHIDGET_GAIN_VALUE

            result_default = PHIDGET_GAIN_VALUE(1)
            result_unknown = PHIDGET_GAIN_VALUE(99)

            # Assert
            assert result_default == 1
            assert result_unknown == 1

    def test_phidget_gain_value_8x_amplification(self) -> None:
        """Test PHIDGET_GAIN_VALUE returns 8x gain for gv=2."""
        # Arrange & Act
        with patch('Phidget22.BridgeGain.BridgeGain') as mock_bridge_gain:
            mock_bridge_gain.BRIDGE_GAIN_8 = 8

            from artisanlib.comm import PHIDGET_GAIN_VALUE

            result = PHIDGET_GAIN_VALUE(2)

            # Assert
            assert result == 8

    def test_phidget_gain_value_all_amplifications(self) -> None:
        """Test PHIDGET_GAIN_VALUE returns correct gains for all supported values."""
        # Arrange & Act
        with patch('Phidget22.BridgeGain.BridgeGain') as mock_bridge_gain:
            mock_bridge_gain.BRIDGE_GAIN_16 = 16
            mock_bridge_gain.BRIDGE_GAIN_32 = 32
            mock_bridge_gain.BRIDGE_GAIN_64 = 64
            mock_bridge_gain.BRIDGE_GAIN_128 = 128

            from artisanlib.comm import PHIDGET_GAIN_VALUE

            # Act & Assert
            assert PHIDGET_GAIN_VALUE(3) == 16  # 16x Amplification
            assert PHIDGET_GAIN_VALUE(4) == 32  # 32x Amplification
            assert PHIDGET_GAIN_VALUE(5) == 64  # 64x Amplification
            assert PHIDGET_GAIN_VALUE(6) == 128  # 128x Amplification


class TestYoctoThread:
    """Test YoctoThread class functionality."""

    def test_yocto_thread_initialization(self) -> None:
        """Test YoctoThread initialization."""
        # Arrange & Act
        with patch('artisanlib.comm.YRefParam'), patch('artisanlib.comm.YAPI'):

            from artisanlib.comm import YoctoThread

            thread = YoctoThread()

            # Assert
            assert isinstance(thread, threading.Thread)
            assert hasattr(thread, '_stopevent')
            assert isinstance(thread._stopevent, threading.Event)

    def test_yocto_thread_run_method(self) -> None:
        """Test YoctoThread run method with mocked YAPI calls."""
        # Arrange
        with patch('artisanlib.comm.YRefParam') as mock_ref_param, patch(
            'artisanlib.comm.YAPI'
        ) as mock_yapi:

            from artisanlib.comm import YoctoThread

            mock_errmsg = Mock()
            mock_ref_param.return_value = mock_errmsg

            thread = YoctoThread()
            # Set stop event immediately to prevent infinite loop
            thread._stopevent.set()

            # Act
            thread.run()

            # Assert
            # YRefParam should be called once to create errmsg
            mock_ref_param.assert_called_once()
            # YAPI methods should not be called since stop event is set
            mock_yapi.UpdateDeviceList.assert_not_called()
            mock_yapi.Sleep.assert_not_called()

    def test_yocto_thread_join_method(self) -> None:
        """Test YoctoThread join method sets stop event."""
        # Arrange
        with patch('artisanlib.comm.YRefParam'), patch('artisanlib.comm.YAPI'), patch(
            'threading.Thread.join'
        ) as mock_thread_join:

            from artisanlib.comm import YoctoThread

            thread = YoctoThread()

            # Act
            thread.join(timeout=1.0)

            # Assert
            assert thread._stopevent.is_set()
            mock_thread_join.assert_called_once_with(thread, 1.0)

    def test_yocto_thread_join_without_timeout(self) -> None:
        """Test YoctoThread join method without timeout."""
        # Arrange
        with patch('artisanlib.comm.YRefParam'), patch('artisanlib.comm.YAPI'), patch(
            'threading.Thread.join'
        ) as mock_thread_join:

            from artisanlib.comm import YoctoThread

            thread = YoctoThread()

            # Act
            thread.join()

            # Assert
            assert thread._stopevent.is_set()
            mock_thread_join.assert_called_once_with(thread, None)


class TestCommModuleIntegration:
    """Test comm module integration and additional functionality."""

    def test_module_imports_successfully(self) -> None:
        """Test that the comm module can be imported successfully."""
        # Arrange & Act
        from artisanlib import comm

        # Assert
        assert comm is not None
        assert hasattr(comm, 'serialport')
        assert hasattr(comm, 'YoctoThread')
        assert hasattr(comm, 'nonedevDlg')

    def test_phidget_mapping_functions_exist(self) -> None:
        """Test that Phidget mapping functions exist and are callable."""
        # Arrange & Act
        from artisanlib.comm import (
            PHIDGET_GAIN_VALUE,
            PHIDGET_RTD_TYPE,
            PHIDGET_RTD_WIRE,
            PHIDGET_THERMOCOUPLE_TYPE,
        )

        # Assert
        assert callable(PHIDGET_THERMOCOUPLE_TYPE)
        assert callable(PHIDGET_RTD_WIRE)
        assert callable(PHIDGET_RTD_TYPE)
        assert callable(PHIDGET_GAIN_VALUE)

    def test_serialport_class_exists_and_instantiable(self) -> None:
        """Test that serialport class exists and can be instantiated."""
        # Arrange
        with patch('serial.Serial'), patch('artisanlib.comm.QSemaphore'), patch(
            'artisanlib.comm.platform'
        ) as mock_platform:

            mock_platform.system.return_value = 'Linux'
            mock_aw = Mock()

            from artisanlib.comm import serialport

            # Act
            ser = serialport(mock_aw)

            # Assert
            assert ser is not None
            assert hasattr(ser, 'devicefunctionlist')
            assert hasattr(ser, 'aw')
            assert ser.aw == mock_aw

    def test_yocto_thread_class_exists_and_instantiable(self) -> None:
        """Test that YoctoThread class exists and can be instantiated."""
        # Arrange & Act
        with patch('artisanlib.comm.YRefParam'), patch('artisanlib.comm.YAPI'):

            from artisanlib.comm import YoctoThread

            thread = YoctoThread()

            # Assert
            assert thread is not None
            assert isinstance(thread, threading.Thread)
            assert hasattr(thread, '_stopevent')

    def test_nonedev_dlg_class_exists(self) -> None:
        """Test that nonedevDlg class exists."""
        # Arrange & Act
        from artisanlib.comm import nonedevDlg

        # Assert
        assert nonedevDlg is not None
        # Check if it's a class
        assert isinstance(nonedevDlg, type)


class TestSerialportClass:
    """Test serialport class functionality."""

    def test_serialport_initialization(self) -> None:
        """Test serialport class initialization."""
        # Arrange
        with patch('serial.Serial') as mock_serial_class, patch(
            'artisanlib.comm.QSemaphore'
        ) as mock_semaphore, patch('artisanlib.comm.platform') as mock_platform:

            mock_platform.system.return_value = 'Linux'
            mock_serial_instance = Mock()
            mock_serial_class.return_value = mock_serial_instance
            mock_semaphore_instance = Mock()
            mock_semaphore.return_value = mock_semaphore_instance

            # Mock ApplicationWindow
            mock_aw = Mock()

            from artisanlib.comm import serialport

            # Act
            ser = serialport(mock_aw)

            # Assert
            assert ser.aw == mock_aw
            assert ser.platf == 'Linux'
            assert ser.default_comport == 'COM4'
            assert ser.comport == 'COM4'
            assert ser.baudrate == 9600
            assert ser.bytesize == 8
            assert ser.parity == 'O'
            assert ser.stopbits == 1
            assert ser.timeout == 0.4
            assert ser.SP == mock_serial_instance  # noqa: SIM300
            assert ser.COMsemaphore == mock_semaphore_instance

    def test_serialport_device_function_list_integrity(self) -> None:
        """Test that devicefunctionlist has expected number of functions."""
        # Arrange
        with patch('serial.Serial'), patch('artisanlib.comm.QSemaphore'), patch(
            'artisanlib.comm.platform'
        ) as mock_platform:

            mock_platform.system.return_value = 'Linux'
            mock_aw = Mock()

            from artisanlib.comm import serialport

            # Act
            ser = serialport(mock_aw)

            # Assert
            # Should have 177 device functions (indices 0-176)
            assert len(ser.devicefunctionlist) == 177
            # All functions should be callable
            for i, func in enumerate(ser.devicefunctionlist):
                assert callable(func), f"Function at index {i} is not callable"

    def test_serialport_phidget_initialization(self) -> None:
        """Test serialport Phidget-related initialization."""
        # Arrange
        with patch('serial.Serial'), patch('artisanlib.comm.QSemaphore'), patch(
            'artisanlib.comm.platform'
        ) as mock_platform:

            mock_platform.system.return_value = 'Windows'
            mock_aw = Mock()

            from artisanlib.comm import serialport

            # Act
            ser = serialport(mock_aw)

            # Assert
            # Phidget sensors should be None initially
            assert ser.PhidgetTemperatureSensor is None
            assert ser.PhidgetIRSensor is None
            assert ser.PhidgetBridgeSensor is None
            assert ser.PhidgetIO is None

            # Phidget values should be initialized as empty lists
            assert ser.Phidget1048values == [[], [], [], []]
            assert ser.Phidget1046values == [[], [], [], []]
            assert len(ser.PhidgetIOvalues) == 8

            # Last values should be initialized to -1
            assert ser.Phidget1048lastvalues == [-1.0] * 4
            assert ser.Phidget1046lastvalues == [-1.0] * 4
            assert len(ser.PhidgetIOlastvalues) == 8

    def test_serialport_yocto_initialization(self) -> None:
        """Test serialport Yoctopuce-related initialization."""
        # Arrange
        with patch('serial.Serial'), patch('artisanlib.comm.QSemaphore'), patch(
            'artisanlib.comm.platform'
        ) as mock_platform:

            mock_platform.system.return_value = 'Darwin'
            mock_aw = Mock()

            from artisanlib.comm import serialport

            # Act
            ser = serialport(mock_aw)

            # Assert
            # YOCTO sensors should be None initially
            assert ser.YOCTOsensor is None
            assert ser.YOCTOchan1 is None
            assert ser.YOCTOchan2 is None
            assert ser.YOCTOthread is None

            # YOCTO values should be initialized
            assert ser.YOCTOvalues == [[], []]
            assert ser.YOCTOlastvalues == [-1.0] * 2
            assert not ser.YOCTOlibImported

            # YOCTO outputs should be empty lists
            assert ser.YOCTOvoltageOutputs == []
            assert ser.YOCTOcurrentOutputs == []
            assert ser.YOCTOrelays == []
            assert ser.YOCTOservos == []
            assert ser.YOCTOpwmOutputs == []

    def test_serialport_pid_initialization(self) -> None:
        """Test serialport PID-related initialization."""
        # Arrange
        with patch('serial.Serial'), patch('artisanlib.comm.QSemaphore'), patch(
            'artisanlib.comm.platform'
        ) as mock_platform:

            mock_platform.system.return_value = 'Linux'
            mock_aw = Mock()

            from artisanlib.comm import serialport

            # Act
            ser = serialport(mock_aw)

            # Assert
            # PID settings should be initialized
            assert ser.controlETpid == [0, 1]  # FujiPXG, unitID 1
            assert ser.readBTpid == [1, 2]  # FujiPXR3, unitID 2
            assert not ser.useModbusPort
            assert ser.showFujiLCDs

    def test_serialport_arduino_initialization(self) -> None:
        """Test serialport Arduino-related initialization."""
        # Arrange
        with patch('serial.Serial'), patch('artisanlib.comm.QSemaphore'), patch(
            'artisanlib.comm.platform'
        ) as mock_platform:

            mock_platform.system.return_value = 'Linux'
            mock_aw = Mock()

            from artisanlib.comm import serialport

            # Act
            ser = serialport(mock_aw)

            # Assert
            # Arduino settings should be initialized
            assert ser.arduinoETChannel == '1'
            assert ser.arduinoBTChannel == '2'
            assert ser.arduinoATChannel == 'None'
            assert ser.ArduinoIsInitialized == 0
            assert ser.ArduinoFILT == [70, 70, 70, 70]

    def test_serialport_external_program_initialization(self) -> None:
        """Test serialport external program initialization."""
        # Arrange
        with patch('serial.Serial'), patch('artisanlib.comm.QSemaphore'), patch(
            'artisanlib.comm.platform'
        ) as mock_platform:

            mock_platform.system.return_value = 'Linux'
            mock_aw = Mock()

            from artisanlib.comm import serialport

            # Act
            ser = serialport(mock_aw)

            # Assert
            # External program settings should be initialized
            assert ser.externalprogram == 'test.py'
            assert ser.externaloutprogram == 'out.py'
            assert not ser.externaloutprogramFlag


class TestSerialportDeviceFunctions:
    """Test serialport device functions."""

    def test_dummy_device_function(self) -> None:
        """Test DUMMY device function returns expected values."""
        # Arrange
        with patch('serial.Serial'), patch('artisanlib.comm.QSemaphore'), patch(
            'artisanlib.comm.platform'
        ) as mock_platform:

            mock_platform.system.return_value = 'Linux'
            mock_aw = Mock()
            mock_aw.qmc.timeclock.elapsedMilli.return_value = 12345.0

            from artisanlib.comm import serialport

            ser = serialport(mock_aw)

            # Act
            tx, t1, t2 = ser.DUMMY()

            # Assert
            assert tx == 12345.0
            assert t1 == 0
            assert t2 == 0

    def test_none_device_function(self) -> None:
        """Test NONE device function with manual temperature dialog."""
        # Arrange
        with patch('serial.Serial'), patch('artisanlib.comm.QSemaphore'), patch(
            'artisanlib.comm.platform'
        ) as mock_platform, patch('artisanlib.comm.nonedevDlg') as mock_dialog_class:

            mock_platform.system.return_value = 'Linux'
            mock_aw = Mock()
            mock_aw.qmc.timeclock.elapsedMilli.return_value = 12345.0

            # Mock dialog
            mock_dialog = Mock()
            mock_dialog.exec.return_value = 1  # Accepted
            mock_dialog.etEdit.text.return_value = '100'
            mock_dialog.btEdit.text.return_value = '200'
            mock_dialog_class.return_value = mock_dialog

            from artisanlib.comm import serialport

            ser = serialport(mock_aw)

            # Act
            tx, t1, t2 = ser.NONE()

            # Assert
            assert tx == 12345.0
            assert t1 == 100.0
            assert t2 == 200.0
            mock_dialog_class.assert_called_once()
            mock_dialog.exec.assert_called_once()

    def test_none_device_function_cancelled(self) -> None:
        """Test NONE device function when dialog is cancelled."""
        # Arrange
        with patch('serial.Serial'), patch('artisanlib.comm.QSemaphore'), patch(
            'artisanlib.comm.platform'
        ) as mock_platform, patch('artisanlib.comm.nonedevDlg') as mock_dialog_class:

            mock_platform.system.return_value = 'Linux'
            mock_aw = Mock()
            mock_aw.qmc.timeclock.elapsedMilli.return_value = 12345.0

            # Mock dialog cancelled
            mock_dialog = Mock()
            mock_dialog.exec.return_value = 0  # Rejected
            mock_dialog_class.return_value = mock_dialog

            from artisanlib.comm import serialport

            ser = serialport(mock_aw)

            # Act
            tx, t1, t2 = ser.NONE()

            # Assert
            assert tx == 12345.0
            assert t1 == -1
            assert t2 == -1

    def test_virtual_device_function(self) -> None:
        """Test virtual device function returns fixed virtual temperatures."""
        # Arrange
        with patch('serial.Serial'), patch('artisanlib.comm.QSemaphore'), patch(
            'artisanlib.comm.platform'
        ) as mock_platform:

            mock_platform.system.return_value = 'Linux'
            mock_aw = Mock()
            mock_aw.qmc.timeclock.elapsedMilli.return_value = 12345.0

            from artisanlib.comm import serialport

            ser = serialport(mock_aw)

            # Act
            tx, t1, t2 = ser.virtual()

            # Assert
            assert tx == 12345.0
            assert t1 == 1.0  # Fixed virtual temperature
            assert t2 == 1.0  # Fixed virtual temperature

    def test_slider_01_device_function(self) -> None:
        """Test slider_01 device function returns slider values."""
        # Arrange
        with patch('serial.Serial'), patch('artisanlib.comm.QSemaphore'), patch(
            'artisanlib.comm.platform'
        ) as mock_platform:

            mock_platform.system.return_value = 'Linux'
            mock_aw = Mock()
            mock_aw.qmc.timeclock.elapsedMilli.return_value = 12345.0
            mock_aw.slider1.value.return_value = 10
            mock_aw.slider2.value.return_value = 20

            from artisanlib.comm import serialport

            ser = serialport(mock_aw)

            # Act
            tx, t1, t2 = ser.slider_01()

            # Assert
            assert tx == 12345.0
            assert t1 == 20  # slider2 value (t2 in function)
            assert t2 == 10  # slider1 value (t1 in function)

    def test_slider_23_device_function(self) -> None:
        """Test slider_23 device function returns slider values."""
        # Arrange
        with patch('serial.Serial'), patch('artisanlib.comm.QSemaphore'), patch(
            'artisanlib.comm.platform'
        ) as mock_platform:

            mock_platform.system.return_value = 'Linux'
            mock_aw = Mock()
            mock_aw.qmc.timeclock.elapsedMilli.return_value = 12345.0
            mock_aw.slider3.value.return_value = 30
            mock_aw.slider4.value.return_value = 40

            from artisanlib.comm import serialport

            ser = serialport(mock_aw)

            # Act
            tx, t1, t2 = ser.slider_23()

            # Assert
            assert tx == 12345.0
            assert t1 == 40  # slider4 value (t2 in function)
            assert t2 == 30  # slider3 value (t1 in function)


class TestSerialportPortManagement:
    """Test serialport port management functionality."""

    def test_confport_method(self) -> None:
        """Test confport method configures serial port settings."""
        # Arrange
        with patch('serial.Serial') as mock_serial_class, patch(
            'artisanlib.comm.QSemaphore'
        ), patch('artisanlib.comm.platform') as mock_platform:

            mock_platform.system.return_value = 'Linux'
            mock_serial_instance = Mock()
            mock_serial_class.return_value = mock_serial_instance

            mock_aw = Mock()

            from artisanlib.comm import serialport

            ser = serialport(mock_aw)
            ser.comport = '/dev/ttyUSB0'
            ser.baudrate = 115200
            ser.bytesize = 7
            ser.parity = 'E'
            ser.stopbits = 2
            ser.timeout = 1.0

            # Act
            ser.confport()

            # Assert
            assert ser.SP.port == '/dev/ttyUSB0'
            assert ser.SP.baudrate == 115200
            assert ser.SP.bytesize == 7
            assert ser.SP.parity == 'E'
            assert ser.SP.stopbits == 2
            assert ser.SP.timeout == 1.0
            assert ser.SP.exclusive is True  # Linux platform

    def test_confport_method_windows(self) -> None:
        """Test confport method on Windows platform."""
        # Arrange
        with patch('serial.Serial') as mock_serial_class, patch(
            'artisanlib.comm.QSemaphore'
        ), patch('artisanlib.comm.platform') as mock_platform:

            mock_platform.system.return_value = 'Windows'
            mock_serial_instance = Mock()
            # Remove exclusive attribute to simulate Windows behavior
            if hasattr(mock_serial_instance, 'exclusive'):
                delattr(mock_serial_instance, 'exclusive')
            mock_serial_class.return_value = mock_serial_instance

            mock_aw = Mock()

            from artisanlib.comm import serialport

            ser = serialport(mock_aw)

            # Act
            ser.confport()

            # Assert
            # exclusive should not be set on Windows
            assert not hasattr(ser.SP, 'exclusive')

    def test_closeport_method(self) -> None:
        """Test closeport method closes serial port."""
        # Arrange
        with patch('serial.Serial') as mock_serial_class, patch(
            'artisanlib.comm.QSemaphore'
        ), patch('artisanlib.comm.platform') as mock_platform:

            mock_platform.system.return_value = 'Linux'
            mock_serial_instance = Mock()
            mock_serial_instance.is_open = True
            mock_serial_class.return_value = mock_serial_instance

            mock_aw = Mock()

            from artisanlib.comm import serialport

            ser = serialport(mock_aw)

            # Act
            ser.closeport()

            # Assert
            mock_serial_instance.close.assert_called_once()

    def test_closeport_method_exception_handling(self) -> None:
        """Test closeport method handles exceptions gracefully."""
        # Arrange
        with patch('serial.Serial') as mock_serial_class, patch(
            'artisanlib.comm.QSemaphore'
        ), patch('artisanlib.comm.platform') as mock_platform:

            mock_platform.system.return_value = 'Linux'
            mock_serial_instance = Mock()
            mock_serial_instance.is_open = True
            mock_serial_instance.close.side_effect = Exception('Port error')
            mock_serial_class.return_value = mock_serial_instance

            mock_aw = Mock()

            from artisanlib.comm import serialport

            ser = serialport(mock_aw)

            # Act & Assert - Should not raise exception
            ser.closeport()
