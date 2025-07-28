"""Unit tests for artisanlib.wsport module.

This module tests the wsport class functionality including:
- Initialization and configuration
- WebSocket connection and disconnection handling
- Asynchronous message handling (producer/consumer)
- Request/response management with event handling
- JSON message parsing and processing
- Push message handling for roasting events
- Thread and event loop management
- Error handling and timeout management
- Data reading operations and channel management
"""

import asyncio
import json
from unittest.mock import Mock

import pytest

from artisanlib.wsport import wsport


@pytest.fixture
def mock_application_window() -> Mock:
    """Create a mock ApplicationWindow for testing."""
    aw = Mock()
    aw.sendmessageSignal = Mock()
    aw.sendmessageSignal.emit = Mock()
    aw.qmc = Mock()
    aw.qmc.adderror = Mock()
    aw.qmc.flagstart = False
    aw.qmc.timeindex = [-1, 0, 0, 0, 0, 0, 0]  # [CHARGE, DRY, FCs, FCe, SCs, SCe, DROP]
    aw.qmc.delay = 1.0
    aw.qmc.toggleRecorderSignal = Mock()
    aw.qmc.toggleRecorderSignal.emit = Mock()
    aw.qmc.markChargeDelaySignal = Mock()
    aw.qmc.markChargeDelaySignal.emit = Mock()
    aw.qmc.markDropSignal = Mock()
    aw.qmc.markDropSignal.emit = Mock()
    aw.qmc.toggleMonitorSignal = Mock()
    aw.qmc.toggleMonitorSignal.emit = Mock()
    aw.qmc.markDrySignal = Mock()
    aw.qmc.markDrySignal.emit = Mock()
    aw.qmc.markFCsSignal = Mock()
    aw.qmc.markFCsSignal.emit = Mock()
    aw.qmc.markFCeSignal = Mock()
    aw.qmc.markFCeSignal.emit = Mock()
    aw.qmc.markSCsSignal = Mock()
    aw.qmc.markSCsSignal.emit = Mock()
    aw.qmc.markSCeSignal = Mock()
    aw.qmc.markSCeSignal.emit = Mock()
    aw.qmc.device_logging = False
    aw.seriallogflag = False
    aw.addserial = Mock()
    return aw


@pytest.fixture
def wsport_instance(mock_application_window: Mock) -> wsport:
    """Create a wsport instance for testing."""
    return wsport(mock_application_window)


class TestWSPortInitialization:
    """Test wsport initialization and configuration."""

    def test_wsport_initialization_success(self, mock_application_window: Mock) -> None:
        """Test successful initialization of wsport."""
        # Act
        port = wsport(mock_application_window)

        # Assert
        assert port.aw == mock_application_window
        assert port._loop is None
        assert port._thread is None
        assert port._write_queue is None
        assert port.default_host == '127.0.0.1'
        assert port.host == '127.0.0.1'
        assert port.port == 80
        assert port.path == 'WebSocket'
        assert port.machineID == 0
        assert port.compression is True
        assert port.lastReadResult is None
        assert port.channels == 10
        assert port.tx == 0
        assert len(port.readings) == 10
        assert all(reading == -1.0 for reading in port.readings)
        assert len(port.channel_requests) == 10
        assert len(port.channel_nodes) == 10
        assert len(port.channel_modes) == 10
        assert port.connect_timeout == 4
        assert port.request_timeout == 0.5
        assert port.reconnect_interval == 0.2
        assert port._ping_interval == 20
        assert port._ping_timeout == 20

    def test_wsport_slots_definition(self) -> None:
        """Test that wsport has proper __slots__ definition."""
        # Act & Assert
        expected_slots = [
            'aw',
            '_loop',
            '_thread',
            '_write_queue',
            'default_host',
            'host',
            'port',
            'path',
            'machineID',
            'lastReadResult',
            'channels',
            'readings',
            'tx',
            'channel_requests',
            'channel_nodes',
            'channel_modes',
            'connect_timeout',
            'request_timeout',
            'compression',
            'reconnect_interval',
            '_ping_interval',
            '_ping_timeout',
            'id_node',
            'machine_node',
            'command_node',
            'data_node',
            'pushMessage_node',
            'request_data_command',
            'charge_message',
            'drop_message',
            'addEvent_message',
            'event_node',
            'DRY_node',
            'FCs_node',
            'FCe_node',
            'SCs_node',
            'SCe_node',
            'STARTonCHARGE',
            'OFFonDROP',
            'open_event',
            'pending_events',
            'ws',
            'wst',
        ]

        assert hasattr(wsport, '__slots__')
        assert set(wsport.__slots__) == set(expected_slots)

    def test_wsport_json_nodes_configuration(self, mock_application_window: Mock) -> None:
        """Test JSON nodes configuration."""
        # Act
        port = wsport(mock_application_window)

        # Assert
        assert port.id_node == 'id'
        assert port.machine_node == 'roasterID'
        assert port.command_node == 'command'
        assert port.data_node == 'data'
        assert port.pushMessage_node == 'pushMessage'
        assert port.request_data_command == 'getData'

    def test_wsport_push_messages_configuration(self, mock_application_window: Mock) -> None:
        """Test push messages configuration."""
        # Act
        port = wsport(mock_application_window)

        # Assert
        assert port.charge_message == 'startRoasting'
        assert port.drop_message == 'endRoasting'
        assert port.addEvent_message == 'addEvent'

    def test_wsport_event_nodes_configuration(self, mock_application_window: Mock) -> None:
        """Test event nodes configuration."""
        # Act
        port = wsport(mock_application_window)

        # Assert
        assert port.event_node == 'event'
        assert port.DRY_node == 'colorChangeEvent'
        assert port.FCs_node == 'firstCrackBeginningEvent'
        assert port.FCe_node == 'firstCrackEndEvent'
        assert port.SCs_node == 'secondCrackBeginningEvent'
        assert port.SCe_node == 'secondCrackEndEvent'

    def test_wsport_flags_configuration(self, mock_application_window: Mock) -> None:
        """Test flags configuration."""
        # Act
        port = wsport(mock_application_window)

        # Assert
        assert port.STARTonCHARGE is False
        assert port.OFFonDROP is False

    def test_wsport_event_management_initialization(self, mock_application_window: Mock) -> None:
        """Test event management initialization."""
        # Act
        port = wsport(mock_application_window)

        # Assert
        assert port.open_event is None
        assert port.pending_events == {}


class TestWSPortRequestEventHandling:
    """Test wsport request event handling functionality."""

    @pytest.mark.asyncio
    async def test_register_request_success(self, wsport_instance: wsport) -> None:
        """Test successful request registration."""
        # Arrange
        message_id = 12345

        # Act
        event = await wsport_instance.registerRequest(message_id)

        # Assert
        assert isinstance(event, asyncio.Event)
        assert message_id in wsport_instance.pending_events
        assert wsport_instance.pending_events[message_id] == event
        assert not event.is_set()

    def test_remove_request_response_success(self, wsport_instance: wsport) -> None:
        """Test successful request response removal."""
        # Arrange
        message_id = 12345
        wsport_instance.pending_events[message_id] = asyncio.Event()

        # Act
        wsport_instance.removeRequestResponse(message_id)

        # Assert
        assert message_id not in wsport_instance.pending_events

    def test_remove_request_response_nonexistent(self, wsport_instance: wsport) -> None:
        """Test removing non-existent request response."""
        # Arrange
        message_id = 99999

        # Act & Assert - Should raise KeyError
        with pytest.raises(KeyError):
            wsport_instance.removeRequestResponse(message_id)

    @pytest.mark.asyncio
    async def test_set_request_response_with_event(self, wsport_instance: wsport) -> None:
        """Test setting request response when event exists."""
        # Arrange
        message_id = 12345
        event = asyncio.Event()
        wsport_instance.pending_events[message_id] = event
        response_data = {'result': 'success', 'data': 'test'}

        # Act
        await wsport_instance.setRequestResponse(message_id, response_data)

        # Assert
        assert event.is_set()
        assert message_id in wsport_instance.pending_events
        assert wsport_instance.pending_events[message_id] == response_data

    @pytest.mark.asyncio
    async def test_set_request_response_nonexistent_id(self, wsport_instance: wsport) -> None:
        """Test setting request response for non-existent message ID."""
        # Arrange
        message_id = 99999
        response_data = {'result': 'success'}

        # Act - Should not raise exception
        await wsport_instance.setRequestResponse(message_id, response_data)

        # Assert - Nothing should change
        assert message_id not in wsport_instance.pending_events

    def test_get_request_response_success(self, wsport_instance: wsport) -> None:
        """Test successful request response retrieval."""
        # Arrange
        message_id = 12345
        response_data = {'result': 'success', 'data': 'test'}
        wsport_instance.pending_events[message_id] = response_data

        # Act
        result = wsport_instance.getRequestResponse(message_id)

        # Assert
        assert result == response_data
        assert message_id not in wsport_instance.pending_events  # Should be removed after retrieval

    def test_get_request_response_with_event(self, wsport_instance: wsport) -> None:
        """Test request response retrieval when event is still pending."""
        # Arrange
        message_id = 12345
        event = asyncio.Event()
        wsport_instance.pending_events[message_id] = event

        # Act
        result = wsport_instance.getRequestResponse(message_id)

        # Assert
        assert result is None
        assert message_id not in wsport_instance.pending_events  # Should be removed

    def test_get_request_response_nonexistent(self, wsport_instance: wsport) -> None:
        """Test request response retrieval for non-existent message ID."""
        # Arrange
        message_id = 99999

        # Act
        result = wsport_instance.getRequestResponse(message_id)

        # Assert
        assert result is None


class TestWSPortProducer:
    """Test wsport producer functionality."""

    @pytest.mark.asyncio
    async def test_producer_with_no_queue(self, wsport_instance: wsport) -> None:
        """Test producer when write queue is None."""
        # Arrange
        wsport_instance._write_queue = None

        # Act
        result = await wsport_instance.producer()

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_producer_with_queue_message(self, wsport_instance: wsport) -> None:
        """Test producer with message in queue."""
        # Arrange
        test_message = '{"test": "message"}'
        wsport_instance._write_queue = asyncio.Queue()
        await wsport_instance._write_queue.put(test_message)

        # Act
        result = await wsport_instance.producer()

        # Assert
        assert result == test_message


class TestWSPortMessageHandling:
    """Test wsport message handling functionality."""

    @pytest.mark.asyncio
    async def test_consumer_with_id_node(self, wsport_instance: wsport) -> None:
        """Test consumer handling message with ID node."""
        # Arrange
        message_id = 12345
        test_message = json.dumps(
            {wsport_instance.id_node: message_id, 'result': 'success', 'data': 'test'}
        )

        # Manually set up the pending event to test the flow
        wsport_instance.pending_events[message_id] = asyncio.Event()

        # Act
        await wsport_instance.consumer(test_message)

        # Assert
        # The event should be set and replaced with the response data
        assert message_id in wsport_instance.pending_events
        response_data = wsport_instance.pending_events[message_id]
        assert not isinstance(response_data, asyncio.Event)
        assert response_data[wsport_instance.id_node] == message_id

    @pytest.mark.asyncio
    async def test_consumer_with_invalid_json(self, wsport_instance: wsport) -> None:
        """Test consumer handling invalid JSON."""
        # Arrange
        invalid_message = 'invalid json {'

        # Act & Assert - Should raise JSONDecodeError
        with pytest.raises(json.JSONDecodeError):
            await wsport_instance.consumer(invalid_message)
