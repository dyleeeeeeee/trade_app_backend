#!/usr/bin/env python3
"""
Comprehensive test script to verify JWT authentication is working correctly
"""
import asyncio
import aiohttp
import json
import os

async def test_jwt_comprehensive():
    base_url = "http://localhost:5000"

    # Test user credentials
    test_user = {
        "email": "test@example.com",
        "password": "password123"
    }

    async with aiohttp.ClientSession() as session:
        print("🔍 Testing Cookie Cash JWT Authentication System")
        print("=" * 50)

        # Test 1: Login and get JWT tokens
        print("\n1️⃣ Testing Login...")
        try:
            async with session.post(f"{base_url}/api/login", json=test_user) as response:
                if response.status == 200:
                    data = await response.json()
                    access_token = data.get('access_token')
                    refresh_token = data.get('refresh_token')
                    user_data = data.get('user')

                    print("✅ Login successful")
                    print(f"   Access Token: {access_token[:30]}...")
                    print(f"   Refresh Token: {refresh_token[:30]}...")
                    print(f"   User: {user_data}")

                    headers = {"Authorization": f"Bearer {access_token}"}

                    # Test 2: Get current user
                    print("\n2️⃣ Testing Get Current User...")
                    async with session.get(f"{base_url}/api/user", headers=headers) as response:
                        if response.status == 200:
                            user_data = await response.json()
                            print("✅ Get current user successful")
                            print(f"   User data: {user_data}")
                        else:
                            print(f"❌ Get current user failed: {response.status}")

                    # Test 3: Get wallet balance
                    print("\n3️⃣ Testing Wallet Balance...")
                    async with session.get(f"{base_url}/api/wallet", headers=headers) as response:
                        if response.status == 200:
                            balance_data = await response.json()
                            print("✅ Wallet balance successful")
                            print(f"   Balance: {balance_data}")
                        else:
                            print(f"❌ Wallet balance failed: {response.status}")

                    # Test 4: Get strategies (public endpoint)
                    print("\n4️⃣ Testing Get Strategies...")
                    async with session.get(f"{base_url}/api/strategies") as response:
                        if response.status == 200:
                            strategies_data = await response.json()
                            print("✅ Get strategies successful")
                            print(f"   Found {len(strategies_data.get('strategies', []))} strategies")
                        else:
                            print(f"❌ Get strategies failed: {response.status}")

                    # Test 5: Get my strategies (protected)
                    print("\n5️⃣ Testing Get My Strategies...")
                    async with session.get(f"{base_url}/api/strategies/my-strategies", headers=headers) as response:
                        if response.status == 200:
                            my_strategies = await response.json()
                            print("✅ Get my strategies successful")
                            print(f"   My strategies: {len(my_strategies.get('strategies', []))} subscriptions")
                        else:
                            print(f"❌ Get my strategies failed: {response.status}")

                    # Test 6: Test token refresh
                    print("\n6️⃣ Testing Token Refresh...")
                    refresh_data = {"refresh_token": refresh_token}
                    async with session.post(f"{base_url}/api/refresh", json=refresh_data) as response:
                        if response.status == 200:
                            refresh_data = await response.json()
                            new_access_token = refresh_data.get('access_token')
                            print("✅ Token refresh successful")
                            print(f"   New access token: {new_access_token[:30]}...")

                            # Test with new token
                            new_headers = {"Authorization": f"Bearer {new_access_token}"}
                            async with session.get(f"{base_url}/api/user", headers=new_headers) as response:
                                if response.status == 200:
                                    print("✅ New token works correctly")
                                else:
                                    print(f"❌ New token failed: {response.status}")

                        else:
                            print(f"❌ Token refresh failed: {response.status}")

                    # Test 7: Test admin endpoint (should fail for regular user)
                    print("\n7️⃣ Testing Admin Endpoint (should fail)...")
                    async with session.get(f"{base_url}/api/admin/users", headers=headers) as response:
                        if response.status == 403:
                            print("✅ Admin access correctly denied")
                        else:
                            print(f"❌ Admin access unexpectedly allowed: {response.status}")

                    # Test 8: Test logout
                    print("\n8️⃣ Testing Logout...")
                    async with session.post(f"{base_url}/api/logout") as response:
                        if response.status == 200:
                            print("✅ Logout successful")
                        else:
                            print(f"❌ Logout failed: {response.status}")

                else:
                    print(f"❌ Login failed: {response.status}")
                    error = await response.text()
                    print(f"   Error: {error}")

        except Exception as e:
            print(f"❌ Test failed with exception: {e}")

        print("\n" + "=" * 50)
        print("🏁 JWT Authentication Test Complete")

if __name__ == "__main__":
    asyncio.run(test_jwt_comprehensive())
