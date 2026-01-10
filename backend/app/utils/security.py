"""
Security utilities for input validation and sanitization.
"""
import ipaddress
from urllib.parse import urlparse
from pathlib import Path
from typing import Optional


def validate_download_url(url: str) -> tuple[bool, Optional[str]]:
    """
    Validate URL to prevent SSRF attacks.

    Args:
        url: The URL to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not url or not isinstance(url, str):
        return False, "Invalid URL format"

    try:
        parsed = urlparse(url)

        # Only allow HTTP/HTTPS
        if parsed.scheme not in ('http', 'https'):
            return False, "Only HTTP/HTTPS protocols are allowed"

        # Ensure hostname is present
        if not parsed.hostname:
            return False, "URL must have a valid hostname"

        # Block common private/internal hostnames
        blocked_hostnames = [
            'localhost',
            '169.254.169.254',  # AWS metadata
            'metadata',
            'metadata.google.internal',  # GCP metadata
            '100.100.100.200',  # Alibaba Cloud metadata
        ]

        hostname_lower = parsed.hostname.lower()
        if hostname_lower in blocked_hostnames:
            return False, "Access to internal services is not allowed"

        # Check if hostname is an IP address and block private ranges
        try:
            ip = ipaddress.ip_address(parsed.hostname)

            if ip.is_private:
                return False, "Access to private IP addresses is not allowed"

            if ip.is_loopback:
                return False, "Access to loopback addresses is not allowed"

            if ip.is_link_local:
                return False, "Access to link-local addresses is not allowed"

            if ip.is_reserved:
                return False, "Access to reserved IP addresses is not allowed"

            if ip.is_multicast:
                return False, "Access to multicast addresses is not allowed"

        except ValueError:
            # Not an IP address, it's a hostname - additional checks
            pass

        return True, None

    except Exception as e:
        return False, f"Invalid URL: {str(e)}"


def validate_safe_path(file_path: Path, base_dir: Path) -> tuple[bool, Optional[str]]:
    """
    Validate that a file path is within the allowed base directory.
    Prevents path traversal attacks and symlink escapes.

    Args:
        file_path: The file path to validate
        base_dir: The base directory that file_path must be within

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        # Resolve both paths to absolute paths
        resolved_path = file_path.resolve()
        resolved_base = base_dir.resolve()

        # Check if the resolved path is within the base directory
        if not resolved_path.is_relative_to(resolved_base):
            return False, "Path is outside allowed directory"

        # Enhanced symlink protection: Check entire path for symlinks
        # Walk from the file up to the base directory
        current = file_path
        checked_paths = set()

        while True:
            # Prevent infinite loops
            current_str = str(current)
            if current_str in checked_paths:
                break
            checked_paths.add(current_str)

            # Check if this component is a symlink
            if current.is_symlink():
                # Get symlink target
                link_target = current.readlink()

                # Reject symlinks entirely for maximum security
                # This prevents any symlink-based escape attempts
                return False, "Symlinks are not allowed"

            # Move to parent directory
            if current == resolved_base or current == current.parent:
                break

            current = current.parent

        return True, None

    except Exception as e:
        return False, f"Path validation error: {str(e)}"


def validate_file_size(file_path: Path, max_size_bytes: int) -> tuple[bool, Optional[str]]:
    """
    Validate that a file does not exceed the maximum size.

    Args:
        file_path: Path to the file
        max_size_bytes: Maximum allowed file size in bytes

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        if not file_path.exists():
            return False, "File does not exist"

        size = file_path.stat().st_size
        if size > max_size_bytes:
            return False, f"File size ({size} bytes) exceeds maximum ({max_size_bytes} bytes)"

        return True, None

    except Exception as e:
        return False, f"File size validation error: {str(e)}"


def validate_password_strength(password: str) -> tuple[bool, Optional[str]]:
    """
    Validate password meets complexity requirements.

    Requirements:
    - Minimum 12 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character

    Args:
        password: Password to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not password:
        return False, "Password is required"

    if len(password) < 12:
        return False, "Password must be at least 12 characters long"

    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"

    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"

    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit"

    # Check for special characters
    special_chars = set('!@#$%^&*()_+-=[]{}|;:,.<>?')
    if not any(c in special_chars for c in password):
        return False, "Password must contain at least one special character (!@#$%^&* etc.)"

    # Check against common passwords
    common_passwords = {
        'password123!', 'Password123!', 'Admin123456!', 'Welcome123!',
        'Changeme123!', 'P@ssword123', 'Password1234!', 'Qwerty123456!'
    }
    if password in common_passwords:
        return False, "Password is too common, please choose a stronger password"

    return True, None
