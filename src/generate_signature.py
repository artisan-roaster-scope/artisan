# ABOUT
# Appends a signature based on the version and revision to __init.py__
# Runs on Appveyor or locally

# LICENSE
# This program or module is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 2 of the License, or
# version 3 of the License, or (at your option) any later version. It is
# provided for educational purposes and is distributed in the hope that
# it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
# the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# AUTHOR
# Dave Baxter, Marko Luther 2026

import os
import sys
import re
import base64
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization


def read_init_file(filepath: str) -> str:
    try:
        with open(filepath, encoding='utf-8') as f:
            content: str = f.read()
    except FileNotFoundError:
        print(f'ERROR: File not found: {filepath}')
        print(f'CWD: {os.getcwd()}')
        sys.exit(1)
    except OSError as e:
        print(f'ERROR: Failed to read file {filepath}: {e}')
        sys.exit(1)

    return content

def extract_field(content: str, field_name: str) -> str | None:
    # Extract a field value from the __init__.py content
    pattern: str = rf'^__{field_name}__\s*=\s*[\'"]([^\'"]*)[\'"]'
    match = re.search(pattern, content, re.MULTILINE)
    if match:
        return match.group(1)
    return None

def load_private_key(build_service: str) -> ed25519.Ed25519PrivateKey | None:

    if build_service == 'LOCAL':
        path_abs = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'artisan-utils', 'crypto', 'artisan_private_key.pem'))
        try:
            with open(path_abs, encoding='utf-8') as f:
                lines = f.readlines()
        except FileNotFoundError:
            print('INFO: No key found')
            return None

        key_env = lines[1].strip()

    # ARTISAN_KEY environment variable is set in the CI environment
    elif build_service in {'APPVEYOR','GITHUB_ACTIONS'}:
        key_env = os.environ.get('ARTISAN_KEY', 'False')
        if not key_env:
            print('ERROR: ARTISAN_KEY environment variable not set.')
            sys.exit(1)
    else:
        print(f'ERROR: Unexpected build_service {build_service}')
        sys.exit(1)

    try:
        # Decode base64 to get DER bytes
        key_bytes: bytes = base64.b64decode(key_env)

        # Load DER-formatted key
        private_key = serialization.load_der_private_key(key_bytes, password=None )

        # Verify it's an Ed25519 key
        if not isinstance(private_key, ed25519.Ed25519PrivateKey):
            print('ERROR: Private key is not an Ed25519 key.')
            sys.exit(1)

        return private_key
    except ValueError as e:
        print(f'ERROR: Failed to load private key: {e}')
        sys.exit(1)
    except OSError as e:
        print(f'ERROR: Failed to load private key: {e}')
        sys.exit(1)

def generate_signature(
        private_key: ed25519.Ed25519PrivateKey,
        revision: str,
        version: str,
        artisan_os: str) -> str:
    # Generate the ed25519 signature
    message: bytes = bytes(f'{version}{revision}{artisan_os}', encoding='ascii')
    signature_bytes: bytes = private_key.sign(message)
    # Convert to hex string
    signature_hex: str = signature_bytes.hex()
    return signature_hex

def remove_existing_signature(content: str) -> str:
    # Remove an existing __signature__ line from content if it exists
    content = re.sub(
        r'^__signature__\s*=\s*[\'"]([^\'"]*)[\'"]\n',
        '',
        content,
        flags=re.MULTILINE
    )
    return content

def write_signature_to_file(filepath: str, signature_hex: str) -> None:
    try:
        with open(filepath, encoding='utf-8') as f:
            content: str = f.read()

        # Remove existing __signature__ line if it exists
        content = remove_existing_signature(content)

        # Append the new signature
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
            f.write(f'__signature__ = \'{signature_hex}\'\n')
    except OSError as e:
        print(f'ERROR: Failed to write signature to file: {e}')
        sys.exit(1)

def get_artisan_os(content: str) -> str:
    # Is this script running on Appveyor?
    is_appveyor = os.getenv('APPVEYOR', 'False').lower() == 'true'

    if is_appveyor:
        # This script is running on Appveyor
        job_name = os.environ.get('APPVEYOR_JOB_NAME', 'False')

        if not job_name:
            print('ERROR: APPVEYOR_JOB_NAME environment variable not found')
            sys.exit(1)

        # Map values returned by platform.system(), RPi not on Appveyor
        mapping: dict[str, str] = {
            'windows': 'Windows',
            'macos': 'macOS',
            'linux': 'Linux'
        }

        if job_name in mapping:
            return mapping[job_name]

        print(f'Warning: Unknown APPVEYOR_JOB_NAME value: {job_name}')
        return job_name

    # This script is not running on Appveyor, get artisan_os from __init__.py
    artisan_os: str | None = extract_field(content, 'artisan_os')

    if artisan_os is None:
        print('ERROR: artisan_os not found in file content')
        sys.exit(1)

    return artisan_os

def get_build_environment() -> tuple[str,str]:
    # CI Service names found as environment variables
    env_vars = ['APPVEYOR', 'GITHUB_ACTIONS']

    # Platforms this script can run on
    platforms = {
        'darwin': 'MACOS',
        'win32': 'WINDOWS',
        'linux': 'LINUX'
    }

    build_service = 'LOCAL'
    for var_name in env_vars:
        if os.environ.get(var_name, 'False').lower() == 'true':
            build_service = var_name
            break

    build_platform = 'UNKNOWN'
    for platform_name, platform_label in platforms.items():
        if sys.platform == platform_name:
            build_platform = platform_label
            break

    if build_platform == 'UNKNOWN':
        print(f'ERROR: Cannot determine the platform on {build_service}')
        sys.exit(1)

    print(f'INFO: Environment is {build_platform} on {build_service}')
    return build_service, build_platform


def main() -> None:
    # Announce who is running
    print('Now running: src/generate_signature.py')
    # Set the file path
    init_filepath: str = os.path.join('artisanlib', '__init__.py')

    # Find out where we are running
    build_service, _ = get_build_environment()

    # Is this a PR?
    if (build_service == 'APPVEYOR' and os.environ.get('APPVEYOR_PULL_REQUEST_NUMBER')) or \
        (build_service == 'GITHUB_ACTIONS' and os.environ.get('GITHUB_EVENT_NAME') == 'pull_request'):
        print('INFO: Pull Request - signature set to the empty string')
        write_signature_to_file(init_filepath, '')
        return

    # Read the file
    content = read_init_file(init_filepath)

    # Extract version and revision
    version: str | None = extract_field(content, 'version')
    revision: str | None = extract_field(content, 'revision')
    artisan_os: str = get_artisan_os(content)
    print(f'INFO: {version=}, {revision=}, {artisan_os=}')

    # Warn if fields are missing but continue
    if not version:
        print('WARNING: __version__ value not found in __init__.py')
    if not revision:
        print('WARNING: __revision__ value not found in __init__.py')

    # Load the private key
    private_key: ed25519.Ed25519PrivateKey | None = load_private_key(build_service)

    #Do nothing if there is not a key
    if not private_key:
        return

    # Generate the signature
    signature_hex: str = generate_signature(private_key, revision or '', version or '', artisan_os or '')

    # Write the signature to the file (replaces if it exists)
    write_signature_to_file(init_filepath, signature_hex)

    print('INFO: Signature written successfully.')
    print(f'INFO: Signature: {signature_hex}')

if __name__ == '__main__':
    main()
