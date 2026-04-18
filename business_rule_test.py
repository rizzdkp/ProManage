#!/usr/bin/env python3
"""
Test the business rule: Task cannot be completed if subtasks are incomplete
"""

import requests
import json

BASE_URL = "https://pm-app-indo.preview.emergentagent.com/api"
TEST_CREDENTIALS = {
    "identifier": "manager@promanage.id",
    "password": "password123"
}

def test_business_rule():
    """Test the business rule for task completion"""
    session = requests.Session()
    
    # 1. Login to get token
    print("🔐 Logging in...")
    response = session.post(f"{BASE_URL}/auth/login", json=TEST_CREDENTIALS)
    if response.status_code != 200:
        print(f"❌ Login failed: {response.text}")
        return False
    
    token = response.json()["token"]
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # 2. Create a test project
    print("📁 Creating test project...")
    project_data = {
        "name": "Business Rule Test Project",
        "description": "Testing business rules",
        "startDate": "2025-01-20",
        "endDate": "2025-06-30"
    }
    response = session.post(f"{BASE_URL}/projects", json=project_data, headers=headers)
    if response.status_code != 200:
        print(f"❌ Project creation failed: {response.text}")
        return False
    
    project_id = response.json()["id"]
    print(f"✅ Project created: {project_id}")
    
    # 3. Create a test task
    print("📋 Creating test task...")
    task_data = {
        "projectId": project_id,
        "name": "Business Rule Test Task",
        "description": "Task for testing business rules",
        "dueDate": "2025-03-15",
        "priority": "Tinggi"
    }
    response = session.post(f"{BASE_URL}/tasks", json=task_data, headers=headers)
    if response.status_code != 200:
        print(f"❌ Task creation failed: {response.text}")
        return False
    
    task_id = response.json()["id"]
    print(f"✅ Task created: {task_id}")
    
    # 4. Create subtasks (some complete, some incomplete)
    print("📝 Creating subtasks...")
    
    # Complete subtask
    subtask1_data = {
        "taskId": task_id,
        "title": "Completed Subtask",
        "projectId": project_id
    }
    response = session.post(f"{BASE_URL}/subtasks", json=subtask1_data, headers=headers)
    if response.status_code != 200:
        print(f"❌ Subtask 1 creation failed: {response.text}")
        return False
    
    subtask1_id = response.json()["id"]
    
    # Mark first subtask as done
    response = session.put(f"{BASE_URL}/subtasks/{subtask1_id}", json={"isDone": True}, headers=headers)
    if response.status_code != 200:
        print(f"❌ Subtask 1 completion failed: {response.text}")
        return False
    
    print("✅ Subtask 1 created and marked as done")
    
    # Incomplete subtask
    subtask2_data = {
        "taskId": task_id,
        "title": "Incomplete Subtask",
        "projectId": project_id
    }
    response = session.post(f"{BASE_URL}/subtasks", json=subtask2_data, headers=headers)
    if response.status_code != 200:
        print(f"❌ Subtask 2 creation failed: {response.text}")
        return False
    
    subtask2_id = response.json()["id"]
    print("✅ Subtask 2 created (left incomplete)")
    
    # 5. Try to complete the task - should fail
    print("⚖️ Testing business rule: Trying to complete task with incomplete subtasks...")
    update_data = {"status": "Selesai"}
    response = session.patch(f"{BASE_URL}/tasks/{task_id}", json=update_data, headers=headers)
    
    if response.status_code == 400:
        error_message = response.text
        print(f"✅ Business rule working correctly! Task completion rejected: {error_message}")
        
        # Verify the error message mentions incomplete subtasks
        if "subtask" in error_message.lower() or "belum selesai" in error_message.lower():
            print("✅ Error message correctly mentions incomplete subtasks")
            return True
        else:
            print(f"⚠️ Error message doesn't mention subtasks: {error_message}")
            return True  # Still correct behavior, just different message
    else:
        print(f"❌ Business rule failed! Task completion should have been rejected but got status {response.status_code}: {response.text}")
        return False

def main():
    print("🧪 Testing ProManage Business Rule: Task Completion with Incomplete Subtasks")
    print("=" * 80)
    
    success = test_business_rule()
    
    print("\n" + "=" * 80)
    if success:
        print("🎉 Business rule test PASSED!")
    else:
        print("❌ Business rule test FAILED!")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())