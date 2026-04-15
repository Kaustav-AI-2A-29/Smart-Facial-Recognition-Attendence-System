#!/usr/bin/env python3
"""Test faculty login."""

from backend.auth import login_user

result = login_user('admin123', 'admin100')

if result:
    print('\n✓ Faculty Login Test PASSED\n')
    print(f'  Username: admin123')
    print(f'  Role: {result.get("role")}')
    print(f'  User ID: {result.get("user_id")}')
    print(f'  Name: {result.get("name")}')
    print()
else:
    print('\n✗ Faculty Login Test FAILED\n')
