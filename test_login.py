#!/usr/bin/env python3
"""Test student login credentials."""

from backend.auth import login_user

def test_all_logins():
    test_creds = [
        ("kaustav", "mypass1"),
        ("debnil", "mypass2"),
        ("jyotirmoy", "mypass3"),
        ("soumita", "mypass4"),
    ]
    
    print("\n" + "=" * 70)
    print("  TESTING STUDENT LOGIN CREDENTIALS")
    print("=" * 70 + "\n")
    
    passed = 0
    failed = 0
    
    for username, password in test_creds:
        result = login_user(username, password)
        
        if result:
            status = "✓ PASS"
            passed += 1
            print(f"  {status}  |  {username:15} / {password:10} | User ID: {result.get('user_id')} | Role: {result.get('role')}")
        else:
            status = "✗ FAIL"
            failed += 1
            print(f"  {status}  |  {username:15} / {password:10}")
    
    print("\n" + "=" * 70)
    print(f"  Results: {passed} passed, {failed} failed")
    print("=" * 70 + "\n")
    
    if failed == 0:
        print("  ✓ All login tests passed! Frontend login should work.")
    else:
        print("  ✗ Some login tests failed. Check database.")
    
    return failed == 0

if __name__ == "__main__":
    success = test_all_logins()
    exit(0 if success else 1)
