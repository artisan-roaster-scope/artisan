"""
Unit tests for artisanlib.async_comm module.

This module tests the async communication classes including:
- AsyncLoopThread: Thread management for asyncio loops
- AsyncIterable: Async iterator wrapper for queues
- IteratorReader: Stream reader for async iterators
- AsyncComm: Main async communication class
"""

import asyncio
import time
from unittest.mock import AsyncMock, Mock, patch
from typing import AsyncGenerator, TYPE_CHECKING

if TYPE_CHECKING:
    from artisanlib.atypes import SerialSettings # pylint: disable=unused-import

import pytest

from artisanlib.async_comm import (
    AsyncComm,
    AsyncIterable,
    AsyncLoopThread,
    IteratorReader,
)


class TestAsyncLoopThread:
    """Test AsyncLoopThread class for managing asyncio loops in threads."""

    def test_init_creates_loop_and_thread(self) -> None:
        """Test that AsyncLoopThread creates a loop and starts a thread."""
        thread = AsyncLoopThread()

        # Should have a loop property
        assert thread.loop is not None
        assert isinstance(thread.loop, asyncio.AbstractEventLoop)

        # Thread should be running
        assert hasattr(thread, '_AsyncLoopThread__thread')
        assert thread._AsyncLoopThread__thread.is_alive() ## type: ignore[reportAttributeAccessIssue]

        # Clean up
        thread.__del__()
        time.sleep(0.1)  # Give time for cleanup

    def test_loop_property_returns_event_loop(self) -> None:
        """Test that loop property returns the event loop."""
        thread = AsyncLoopThread()
        loop = thread.loop

        assert isinstance(loop, asyncio.AbstractEventLoop)

        # Clean up
        thread.__del__()
        time.sleep(0.1)

    def test_del_stops_loop(self) -> None:
        """Test that __del__ stops the event loop."""
        thread = AsyncLoopThread()
        loop = thread.loop

        # Mock call_soon_threadsafe to verify it's called
        with patch.object(loop, 'call_soon_threadsafe') as mock_call:
            thread.__del__()
            mock_call.assert_called_once_with(loop.stop)


class TestAsyncIterable:
    """Test AsyncIterable class for wrapping queues as async iterators."""

    @pytest.mark.asyncio
    async def test_init_stores_queue(self) -> None:
        """Test that AsyncIterable stores the provided queue."""
        queue: asyncio.Queue[bytes] = asyncio.Queue()
        iterable = AsyncIterable(queue)

        assert iterable._queue is queue

    @pytest.mark.asyncio
    async def test_aiter_returns_self(self) -> None:
        """Test that __aiter__ returns self."""
        queue: asyncio.Queue[bytes] = asyncio.Queue()
        iterable = AsyncIterable(queue)

        assert iterable.__aiter__() is iterable

    @pytest.mark.asyncio
    async def test_anext_returns_queue_item(self) -> None:
        """Test that __anext__ returns items from the queue."""
        queue: asyncio.Queue[bytes] = asyncio.Queue()
        iterable = AsyncIterable(queue)

        test_data = b'test_data'
        await queue.put(test_data)

        result = await iterable.__anext__()
        assert result == test_data

    @pytest.mark.asyncio
    async def test_async_iteration(self) -> None:
        """Test that AsyncIterable can be used in async for loops."""
        queue: asyncio.Queue[bytes] = asyncio.Queue()
        iterable = AsyncIterable(queue)

        # Put some test data
        test_items = [b'item1', b'item2', b'item3']
        for item in test_items:
            await queue.put(item)

        # Collect items using async iteration
        collected = []
        async for item in iterable:
            collected.append(item)
            if len(collected) == len(test_items):
                break

        assert collected == test_items


class TestIteratorReader:
    """Test IteratorReader class for reading from async iterators."""

    @pytest.mark.asyncio
    async def test_init_stores_chunks_and_initializes_backlog(self) -> None:
        """Test that IteratorReader initializes correctly."""

        async def mock_chunks() -> AsyncGenerator[bytes, None]:
            yield b'test'

        reader = IteratorReader(mock_chunks())
        assert reader._backlog == b''

    @pytest.mark.asyncio
    async def test_read_until_end_returns_all_content(self) -> None:
        """Test _read_until_end returns all available content."""

        async def mock_chunks() -> AsyncGenerator[bytes, None]:
            yield b'chunk1'
            yield b'chunk2'
            yield b'chunk3'

        reader = IteratorReader(mock_chunks())
        result = await reader._read_until_end()

        assert result == b'chunk1chunk2chunk3'
        assert reader._backlog == b''

    @pytest.mark.asyncio
    async def test_read_until_end_includes_backlog(self) -> None:
        """Test _read_until_end includes existing backlog."""

        async def mock_chunks() -> AsyncGenerator[bytes, None]:
            yield b'new_chunk'

        reader = IteratorReader(mock_chunks())
        reader._backlog = b'existing_'

        result = await reader._read_until_end()
        assert result == b'existing_new_chunk'

    @pytest.mark.asyncio
    async def test_read_chunk_returns_exact_size(self) -> None:
        """Test _read_chunk returns exactly the requested size."""

        async def mock_chunks() -> AsyncGenerator[bytes, None]:
            yield b'1234567890'

        reader = IteratorReader(mock_chunks())
        result = await reader._read_chunk(5)

        assert result == b'12345'
        assert reader._backlog == b'67890'

    @pytest.mark.asyncio
    async def test_read_chunk_handles_multiple_chunks(self) -> None:
        """Test _read_chunk can read across multiple chunks."""

        async def mock_chunks() -> AsyncGenerator[bytes, None]:
            yield b'123'
            yield b'456'
            yield b'789'

        reader = IteratorReader(mock_chunks())
        result = await reader._read_chunk(7)

        assert result == b'1234567'
        assert reader._backlog == b'89'

    @pytest.mark.asyncio
    async def test_readexactly_with_positive_size(self) -> None:
        """Test readexactly with positive size calls _read_chunk."""

        async def mock_chunks() -> AsyncGenerator[bytes, None]:
            yield b'test_data'

        reader = IteratorReader(mock_chunks())
        result = await reader.readexactly(4)

        assert result == b'test'

    @pytest.mark.asyncio
    async def test_readexactly_with_minus_one_reads_all(self) -> None:
        """Test readexactly with -1 reads all content."""

        async def mock_chunks() -> AsyncGenerator[bytes, None]:
            yield b'all_content'

        reader = IteratorReader(mock_chunks())
        result = await reader.readexactly(-1)

        assert result == b'all_content'

    @pytest.mark.asyncio
    async def test_readexactly_with_zero_returns_empty(self) -> None:
        """Test readexactly with 0 returns empty bytes."""

        async def mock_chunks() -> AsyncGenerator[bytes, None]:
            yield b'ignored'

        reader = IteratorReader(mock_chunks())
        result = await reader.readexactly(0)

        assert result == b''

    @pytest.mark.asyncio
    async def test_readuntil_finds_separator(self) -> None:
        """Test readuntil finds and returns the separator."""

        async def mock_chunks() -> AsyncGenerator[bytes, None]:
            yield b'a'
            yield b'b'
            yield b'\n'
            yield b'c'

        reader = IteratorReader(mock_chunks())
        result = await reader.readuntil(b'\n')

        assert result == b'\n'

    @pytest.mark.asyncio
    async def test_readuntil_with_empty_separator_returns_immediately(self) -> None:
        """Test readuntil with empty separator returns immediately."""

        async def mock_chunks() -> AsyncGenerator[bytes, None]:
            yield b'test'

        reader = IteratorReader(mock_chunks())
        result = await reader.readuntil(b'')

        assert result == b''


class TestAsyncComm:
    """Test AsyncComm class for async communication management."""

    def test_init_with_defaults(self) -> None:
        """Test AsyncComm initialization with default parameters."""
        comm = AsyncComm()

        assert comm._host == '127.0.0.1'
        assert comm._port == 8080
        assert comm._serial is None
        assert comm._connected_handler is None
        assert comm._disconnected_handler is None
        assert comm._verify_crc is True
        assert comm._logging is False
        assert comm._running is False
        assert comm._asyncLoopThread is None
        assert comm._write_queue is None

    def test_init_with_custom_parameters(self) -> None:
        """Test AsyncComm initialization with custom parameters."""

        def mock_connected() -> None:
            pass

        def mock_disconnected() -> None:
            pass

        serial_settings:SerialSettings = {
            'port': '/dev/ttyUSB0',
            'baudrate': 9600,
            'bytesize': 8,
            'stopbits': 1,
            'parity': 'N',
            'timeout': 1.0,
        }

        comm = AsyncComm(
            host='192.168.1.100',
            port=9000,
            serial=serial_settings,
            connected_handler=mock_connected,
            disconnected_handler=mock_disconnected,
        )

        assert comm._host == '192.168.1.100'
        assert comm._port == 9000
        assert comm._serial == serial_settings
        assert comm._connected_handler == mock_connected
        assert comm._disconnected_handler == mock_disconnected

    def test_setVerifyCRC(self) -> None:
        """Test setVerifyCRC method."""
        comm = AsyncComm()

        comm.setVerifyCRC(False)
        assert comm._verify_crc is False

        comm.setVerifyCRC(True)
        assert comm._verify_crc is True

    def test_setLogging(self) -> None:
        """Test setLogging method."""
        comm = AsyncComm()

        comm.setLogging(True)
        assert comm._logging is True

        comm.setLogging(False)
        assert comm._logging is False

    def test_async_loop_thread_property(self) -> None:
        """Test async_loop_thread property."""
        comm = AsyncComm()

        assert comm.async_loop_thread is None

        # Mock an AsyncLoopThread
        mock_thread = Mock()
        comm._asyncLoopThread = mock_thread

        assert comm.async_loop_thread is mock_thread

    def test_reset_readings_default_implementation(self) -> None:
        """Test reset_readings default implementation does nothing."""
        comm = AsyncComm()

        # Should not raise any exception
        comm.reset_readings()

    @pytest.mark.asyncio
    async def test_read_msg_default_implementation(self) -> None:
        """Test read_msg default implementation does nothing."""
        comm = AsyncComm()
        mock_stream = Mock()

        # Should not raise any exception
        await comm.read_msg(mock_stream)

    @pytest.mark.asyncio
    async def test_open_serial_connection_with_defaults(self) -> None:
        """Test open_serial_connection with default parameters."""
        with patch('artisanlib.async_comm.create_serial_connection') as mock_create:
            mock_transport = Mock()
            mock_protocol = Mock()
            mock_create.return_value = (mock_transport, mock_protocol)

            with patch('asyncio.StreamReader') as mock_reader_class, \
                    patch('asyncio.StreamReaderProtocol') as mock_protocol_class, \
                    patch('asyncio.StreamWriter') as mock_writer_class:
                mock_reader = Mock()
                mock_protocol_instance = Mock()
                mock_writer = Mock()

                mock_reader_class.return_value = mock_reader
                mock_protocol_class.return_value = mock_protocol_instance
                mock_writer_class.return_value = mock_writer

                reader, writer = await AsyncComm.open_serial_connection('/dev/ttyUSB0')

                assert reader == mock_reader
                assert writer == mock_writer
                mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_writes_handles_exceptions(self) -> None:
        """Test handle_writes handles exceptions gracefully."""
        comm = AsyncComm()
        mock_writer = AsyncMock()
        queue: asyncio.Queue[bytes] = asyncio.Queue()

        # Mock queue.get to raise an exception
        with patch.object(queue, 'get', side_effect=Exception('Queue error')), \
                patch('artisanlib.async_comm._log') as mock_log:
            await comm.handle_writes(mock_writer, queue)
            mock_log.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_writes_drains_writer_in_finally(self) -> None:
        """Test handle_writes drains writer in finally block."""
        comm = AsyncComm()
        mock_writer = AsyncMock()
        queue: asyncio.Queue[bytes] = asyncio.Queue()

        # Put empty message to stop immediately
        await queue.put(b'')

        await comm.handle_writes(mock_writer, queue)

        # Should drain the writer
        mock_writer.drain.assert_called()

    def test_send_with_active_thread_and_queue(self) -> None:
        """Test send method with active thread and queue."""
        comm = AsyncComm()

        # Mock the async loop thread and write queue
        mock_thread = Mock()
        mock_loop = Mock()
        mock_thread.loop = mock_loop
        comm._asyncLoopThread = mock_thread
        comm._write_queue = Mock()

        test_message = b'test_message'

        with patch('asyncio.run_coroutine_threadsafe') as mock_run:
            comm.send(test_message)
            mock_run.assert_called_once()

    def test_send_with_no_thread_does_nothing(self) -> None:
        """Test send method does nothing when no thread is active."""
        comm = AsyncComm()

        # No thread or queue set
        test_message = b'test_message'

        with patch('asyncio.run_coroutine_threadsafe') as mock_run:
            comm.send(test_message)
            mock_run.assert_not_called()

    def test_send_with_no_queue_does_nothing(self) -> None:
        """Test send method does nothing when no queue is set."""
        comm = AsyncComm()

        # Set thread but no queue
        mock_thread = Mock()
        comm._asyncLoopThread = mock_thread
        comm._write_queue = None

        test_message = b'test_message'

        with patch('asyncio.run_coroutine_threadsafe') as mock_run:
            comm.send(test_message)
            mock_run.assert_not_called()

    def test_start_does_nothing_if_thread_already_exists(self) -> None:
        """Test start method does nothing if thread already exists."""
        comm = AsyncComm()

        # Set existing thread
        existing_thread = Mock()
        comm._asyncLoopThread = existing_thread

        with patch('artisanlib.async_comm.AsyncLoopThread') as mock_thread_class:
            comm.start()

            # Should not create new thread
            mock_thread_class.assert_not_called()
            assert comm._asyncLoopThread == existing_thread

    def test_start_handles_exceptions(self) -> None:
        """Test start method handles exceptions gracefully."""
        comm = AsyncComm()

        with patch('artisanlib.async_comm.AsyncLoopThread', side_effect=Exception('Thread error')), \
                patch('artisanlib.async_comm._log') as mock_log:
            comm.start()
            mock_log.exception.assert_called_once()

class TestAsyncCommEdgeCases:
    """Test edge cases and error conditions for AsyncComm."""

    def test_init_with_invalid_serial_settings(self) -> None:
        """Test AsyncComm handles invalid serial settings gracefully."""
        # This should not raise an exception during init
        invalid_serial:SerialSettings = {
            'port': '',
            'baudrate': -1,
            'bytesize': 0,
            'stopbits': 0,
            'parity': 'INVALID',
            'timeout': -1.0,
        }

        comm = AsyncComm(serial=invalid_serial)
        assert comm._serial == invalid_serial

    @pytest.mark.asyncio
    async def test_iterator_reader_with_empty_chunks(self) -> None:
        """Test IteratorReader handles empty chunks gracefully."""

        async def mock_chunks() -> AsyncGenerator[bytes, None]:
            yield b''
            yield b'data'
            yield b''

        reader = IteratorReader(mock_chunks())
        result = await reader.readexactly(4)

        assert result == b'data'
