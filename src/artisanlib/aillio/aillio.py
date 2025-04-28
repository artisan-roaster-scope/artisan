#!/usr/bin/env python3

#
# ABOUT
# Aillio support for Artisan

# LICENSE
# This program or module is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 2 of the License, or
# version 3 of the License, or (at your option) any later version. It is
# provided for educational purposes and is distributed in the hope that
# it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
# the GNU General Public License for more details.

# AUTHOR
# Rui Paulo, 2023
# mikefsq, r2 2025

import usb.core # type: ignore[import-untyped]
from typing import Optional, Union, List, TypedDict, cast, TYPE_CHECKING
import logging
from platform import system
import importlib.util
import os

if TYPE_CHECKING:
    from artisanlib.aillio.aillio_r1 import AillioR1
    from artisanlib.aillio.aillio_r2 import AillioR2

_log = logging.getLogger(__name__)


class DEVICE_VARIANT(TypedDict):
    vid: int
    pid: int
    protocol: int
    model: str
    module: str
    class_name: str

class AillioBase:
    # Device variants with explicit class names
    DEVICE_VARIANTS:List[DEVICE_VARIANT] = [
        {
            'vid': 0x0483,
            'pid': 0x5741,
            'protocol': 1,
            'model': 'Aillio Bullet R1',
            'module': 'aillio_r1',
            'class_name': 'AillioR1'
        },
        {
            'vid': 0x0483,
            'pid': 0xa27e,
            'protocol': 1,
            'model': 'Aillio Bullet R1 IrBts',
            'module': 'aillio_r1',
            'class_name': 'AillioR1'
        },
        {
            'vid': 0x0483,
            'pid': 0xa4cd,
            'protocol': 2,
            'model': 'Aillio Bullet R2',
            'module': 'aillio_r2',
            'class_name': 'AillioR2'
        }
    ]

    @staticmethod
    def detect_device() -> Optional[DEVICE_VARIANT]:
        """Detect connected Aillio device"""
        if system().startswith('Windows'):
            import libusb_package # pyright:ignore[reportMissingImports] # pylint: disable=import-error
            for variant in AillioBase.DEVICE_VARIANTS:
                device = libusb_package.find(idVendor=variant['vid'], idProduct=variant['pid'])
                if device is not None:
                    return variant
        else:
            for variant in AillioBase.DEVICE_VARIANTS:
                device = usb.core.find(idVendor=variant['vid'], idProduct=variant['pid'])
                if device is not None:
                    return variant
        return None

    @staticmethod
    def create(debug: bool = False) -> 'Optional[Union[AillioR1,AillioR2]]':
        """Factory method to create appropriate Aillio instance"""

        detected_device = AillioBase.detect_device()

        if detected_device is None:
            _log.warning('No Aillio roaster detected')
            return None

        try:
            # Get current directory
            current_dir = os.path.dirname(os.path.abspath(__file__))
            module_path = os.path.join(current_dir, f"{detected_device['module']}.py")

            spec = importlib.util.spec_from_file_location(detected_device['module'], module_path)
            if spec is None or spec.loader is None:
                raise ImportError(f"Could not load spec for {detected_device['module']}")

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Create instance using appropriate class name
            roaster_class = getattr(module, detected_device['class_name'])
            instance = cast('Union[AillioR1,AillioR2]', roaster_class(debug=debug))

            _log.info('Created %s instance using protocol V%s', detected_device['model'], detected_device['protocol'])
            return instance

        except Exception as e:  # pylint: disable=broad-except
            _log.exception('Failed to create roaster instance: %s', e)
            return None

    @staticmethod
    def get_supported_models() -> List[str]:
        """Return list of supported roaster models"""
        return [variant['model'] for variant in AillioBase.DEVICE_VARIANTS]

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    print('Supported models:')
    for model in AillioBase.get_supported_models():
        print(f"- {model}")

    print('\nDetecting roaster...')
    roaster = AillioBase.create(debug=False)
    if roaster:
        try:
            while True:
                bt = roaster.get_bt()
                dt = roaster.get_dt()
                state = roaster.get_state_string()
                print(f"BT: {bt:.1f}°C, DT: {dt:.1f}°C, State: {state}")
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            print('\nExiting...')
        finally:
            # Close connection using the appropriate close method
            roaster._close_port() # pylint: disable=protected-access
    else:
        print('No roaster detected')
