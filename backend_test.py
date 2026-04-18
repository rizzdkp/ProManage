#!/usr/bin/env python3
"""
ProManage Backend API Testing Script
Tests all backend endpoints with realistic Indonesian data
"""

import requests
import json
import sys
from datetime import datetime, timedelta
import uuid

# Configuration
BASE_URL = "https://pm-app-indo.preview.emergentagent.com/api"
TEST_CREDENTIALS = {
    "identifier": "manager@promanage.id",
    "password": "password123"
}

class ProManageAPITester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.test_results = {
            "auth": {},
            "users": {},
            "projects": {},
            "tasks": {},
            "subtasks": {},
            "comments": {},
            "notifications": {},
            "stats": {},
            "whatsapp": {},
            "business_rules": {}
        }
        self.created_ids = {
            "users": [],
            "projects": [],
            "tasks": [],
            "subtasks": [],
            "comments": []
        }

    def log_result(self, category, test_name, success, response_data=None, error=None):
        """Log test results"""
        result = {
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "response_data": response_data,
            "error": str(error) if error else None
        }
        self.test_results[category][test_name] = result
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {category.upper()}: {test_name}")
        if error:
            print(f"   Error: {error}")
        if response_data and not success:
            print(f"   Response: {response_data}")

    def make_request(self, method, endpoint, data=None, params=None, use_auth=True):
        """Make HTTP request with proper headers"""
        url = f"{BASE_URL}{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        if use_auth and self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url, headers=headers, params=params)
            elif method.upper() == "POST":
                response = self.session.post(url, headers=headers, json=data)
            elif method.upper() == "PUT":
                response = self.session.put(url, headers=headers, json=data)
            elif method.upper() == "PATCH":
                response = self.session.patch(url, headers=headers, json=data)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            return response
        except Exception as e:
            print(f"Request failed: {e}")
            return None

    def test_auth_login(self):
        """Test login endpoint"""
        try:
            response = self.make_request("POST", "/auth/login", TEST_CREDENTIALS, use_auth=False)
            
            if response and response.status_code == 200:
                data = response.json()
                if "token" in data and "user" in data:
                    self.token = data["token"]
                    self.log_result("auth", "login", True, data)
                    return True
                else:
                    self.log_result("auth", "login", False, data, "Missing token or user in response")
            else:
                error_msg = response.text if response else "No response"
                self.log_result("auth", "login", False, None, f"Status: {response.status_code if response else 'None'}, {error_msg}")
            
        except Exception as e:
            self.log_result("auth", "login", False, None, e)
        
        return False

    def test_auth_me(self):
        """Test get current user endpoint"""
        try:
            response = self.make_request("GET", "/auth/me")
            
            if response and response.status_code == 200:
                data = response.json()
                if "id" in data and "name" in data:
                    self.log_result("auth", "me", True, data)
                    return True
                else:
                    self.log_result("auth", "me", False, data, "Missing required user fields")
            else:
                error_msg = response.text if response else "No response"
                self.log_result("auth", "me", False, None, f"Status: {response.status_code if response else 'None'}, {error_msg}")
                
        except Exception as e:
            self.log_result("auth", "me", False, None, e)
        
        return False

    def test_auth_register(self):
        """Test user registration"""
        try:
            # Generate unique phone number
            unique_phone = f"6281{uuid.uuid4().hex[:8]}"
            register_data = {
                "name": "Tester Baru",
                "phone": unique_phone,
                "email": f"tester{uuid.uuid4().hex[:6]}@test.id",
                "password": "testpass123"
            }
            
            response = self.make_request("POST", "/auth/register", register_data, use_auth=False)
            
            if response and response.status_code == 200:
                data = response.json()
                if "token" in data and "user" in data:
                    self.created_ids["users"].append(data["user"]["id"])
                    self.log_result("auth", "register", True, data)
                    return True
                else:
                    self.log_result("auth", "register", False, data, "Missing token or user in response")
            else:
                error_msg = response.text if response else "No response"
                self.log_result("auth", "register", False, None, f"Status: {response.status_code if response else 'None'}, {error_msg}")
                
        except Exception as e:
            self.log_result("auth", "register", False, None, e)
        
        return False

    def test_users_get(self):
        """Test get all users"""
        try:
            response = self.make_request("GET", "/users")
            
            if response and response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    self.log_result("users", "get_all", True, f"Found {len(data)} users")
                    return True
                else:
                    self.log_result("users", "get_all", False, data, "No users found or invalid format")
            else:
                error_msg = response.text if response else "No response"
                self.log_result("users", "get_all", False, None, f"Status: {response.status_code if response else 'None'}, {error_msg}")
                
        except Exception as e:
            self.log_result("users", "get_all", False, None, e)
        
        return False

    def test_projects_get(self):
        """Test get all projects"""
        try:
            response = self.make_request("GET", "/projects")
            
            if response and response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_result("projects", "get_all", True, f"Found {len(data)} projects")
                    return data
                else:
                    self.log_result("projects", "get_all", False, data, "Invalid projects format")
            else:
                error_msg = response.text if response else "No response"
                self.log_result("projects", "get_all", False, None, f"Status: {response.status_code if response else 'None'}, {error_msg}")
                
        except Exception as e:
            self.log_result("projects", "get_all", False, None, e)
        
        return []

    def test_project_get_by_id(self, project_id):
        """Test get project by ID"""
        try:
            response = self.make_request("GET", f"/projects/{project_id}")
            
            if response and response.status_code == 200:
                data = response.json()
                if "id" in data and data["id"] == project_id:
                    self.log_result("projects", "get_by_id", True, data)
                    return True
                else:
                    self.log_result("projects", "get_by_id", False, data, "Project ID mismatch")
            else:
                error_msg = response.text if response else "No response"
                self.log_result("projects", "get_by_id", False, None, f"Status: {response.status_code if response else 'None'}, {error_msg}")
                
        except Exception as e:
            self.log_result("projects", "get_by_id", False, None, e)
        
        return False

    def test_project_create(self):
        """Test create new project"""
        try:
            project_data = {
                "name": "Proyek Testing API",
                "description": "Proyek untuk testing API backend ProManage",
                "startDate": "2025-01-20",
                "endDate": "2025-06-30"
            }
            
            response = self.make_request("POST", "/projects", project_data)
            
            if response and response.status_code == 200:
                data = response.json()
                if "id" in data and "name" in data:
                    self.created_ids["projects"].append(data["id"])
                    self.log_result("projects", "create", True, data)
                    return data["id"]
                else:
                    self.log_result("projects", "create", False, data, "Missing required project fields")
            else:
                error_msg = response.text if response else "No response"
                self.log_result("projects", "create", False, None, f"Status: {response.status_code if response else 'None'}, {error_msg}")
                
        except Exception as e:
            self.log_result("projects", "create", False, None, e)
        
        return None

    def test_tasks_get(self, project_id):
        """Test get tasks for a project"""
        try:
            response = self.make_request("GET", "/tasks", params={"projectId": project_id})
            
            if response and response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_result("tasks", "get_by_project", True, f"Found {len(data)} tasks for project")
                    return data
                else:
                    self.log_result("tasks", "get_by_project", False, data, "Invalid tasks format")
            else:
                error_msg = response.text if response else "No response"
                self.log_result("tasks", "get_by_project", False, None, f"Status: {response.status_code if response else 'None'}, {error_msg}")
                
        except Exception as e:
            self.log_result("tasks", "get_by_project", False, None, e)
        
        return []

    def test_task_create(self, project_id):
        """Test create new task"""
        try:
            task_data = {
                "projectId": project_id,
                "name": "Task Testing API",
                "description": "Task untuk testing API backend",
                "dueDate": "2025-03-15",
                "priority": "Tinggi",
                "assignee": None
            }
            
            response = self.make_request("POST", "/tasks", task_data)
            
            if response and response.status_code == 200:
                data = response.json()
                if "id" in data and "name" in data:
                    self.created_ids["tasks"].append(data["id"])
                    self.log_result("tasks", "create", True, data)
                    return data["id"]
                else:
                    self.log_result("tasks", "create", False, data, "Missing required task fields")
            else:
                error_msg = response.text if response else "No response"
                self.log_result("tasks", "create", False, None, f"Status: {response.status_code if response else 'None'}, {error_msg}")
                
        except Exception as e:
            self.log_result("tasks", "create", False, None, e)
        
        return None

    def test_task_update_status(self, task_id, status):
        """Test update task status"""
        try:
            update_data = {"status": status}
            
            response = self.make_request("PATCH", f"/tasks/{task_id}", update_data)
            
            if response and response.status_code == 200:
                data = response.json()
                if "status" in data and data["status"] == status:
                    self.log_result("tasks", f"update_status_to_{status.lower()}", True, data)
                    return True
                else:
                    self.log_result("tasks", f"update_status_to_{status.lower()}", False, data, "Status not updated correctly")
            else:
                error_msg = response.text if response else "No response"
                # For business rule testing, 400 status might be expected
                if status == "Selesai" and response and response.status_code == 400:
                    self.log_result("business_rules", "reject_complete_with_incomplete_subtasks", True, response.text)
                    return True
                else:
                    self.log_result("tasks", f"update_status_to_{status.lower()}", False, None, f"Status: {response.status_code if response else 'None'}, {error_msg}")
                
        except Exception as e:
            self.log_result("tasks", f"update_status_to_{status.lower()}", False, None, e)
        
        return False

    def test_subtasks_get(self, task_id):
        """Test get subtasks for a task"""
        try:
            response = self.make_request("GET", "/subtasks", params={"taskId": task_id})
            
            if response and response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_result("subtasks", "get_by_task", True, f"Found {len(data)} subtasks")
                    return data
                else:
                    self.log_result("subtasks", "get_by_task", False, data, "Invalid subtasks format")
            else:
                error_msg = response.text if response else "No response"
                self.log_result("subtasks", "get_by_task", False, None, f"Status: {response.status_code if response else 'None'}, {error_msg}")
                
        except Exception as e:
            self.log_result("subtasks", "get_by_task", False, None, e)
        
        return []

    def test_subtask_create(self, task_id, project_id):
        """Test create new subtask"""
        try:
            subtask_data = {
                "taskId": task_id,
                "title": "Subtask Testing API",
                "projectId": project_id
            }
            
            response = self.make_request("POST", "/subtasks", subtask_data)
            
            if response and response.status_code == 200:
                data = response.json()
                if "id" in data and "title" in data:
                    self.created_ids["subtasks"].append(data["id"])
                    self.log_result("subtasks", "create", True, data)
                    return data["id"]
                else:
                    self.log_result("subtasks", "create", False, data, "Missing required subtask fields")
            else:
                error_msg = response.text if response else "No response"
                self.log_result("subtasks", "create", False, None, f"Status: {response.status_code if response else 'None'}, {error_msg}")
                
        except Exception as e:
            self.log_result("subtasks", "create", False, None, e)
        
        return None

    def test_subtask_toggle_done(self, subtask_id):
        """Test toggle subtask isDone status"""
        try:
            update_data = {"isDone": True}
            
            response = self.make_request("PUT", f"/subtasks/{subtask_id}", update_data)
            
            if response and response.status_code == 200:
                data = response.json()
                if "isDone" in data:
                    self.log_result("subtasks", "toggle_done", True, data)
                    return True
                else:
                    self.log_result("subtasks", "toggle_done", False, data, "isDone field not found")
            else:
                error_msg = response.text if response else "No response"
                self.log_result("subtasks", "toggle_done", False, None, f"Status: {response.status_code if response else 'None'}, {error_msg}")
                
        except Exception as e:
            self.log_result("subtasks", "toggle_done", False, None, e)
        
        return False

    def test_comments_get(self, task_id):
        """Test get comments for a task"""
        try:
            response = self.make_request("GET", "/comments", params={"taskId": task_id})
            
            if response and response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_result("comments", "get_by_task", True, f"Found {len(data)} comments")
                    return data
                else:
                    self.log_result("comments", "get_by_task", False, data, "Invalid comments format")
            else:
                error_msg = response.text if response else "No response"
                self.log_result("comments", "get_by_task", False, None, f"Status: {response.status_code if response else 'None'}, {error_msg}")
                
        except Exception as e:
            self.log_result("comments", "get_by_task", False, None, e)
        
        return []

    def test_comment_create(self, task_id):
        """Test create new comment"""
        try:
            comment_data = {
                "taskId": task_id,
                "message": "Ini adalah komentar testing dari API test script"
            }
            
            response = self.make_request("POST", "/comments", comment_data)
            
            if response and response.status_code == 200:
                data = response.json()
                if "id" in data and "message" in data:
                    self.created_ids["comments"].append(data["id"])
                    self.log_result("comments", "create", True, data)
                    return data["id"]
                else:
                    self.log_result("comments", "create", False, data, "Missing required comment fields")
            else:
                error_msg = response.text if response else "No response"
                self.log_result("comments", "create", False, None, f"Status: {response.status_code if response else 'None'}, {error_msg}")
                
        except Exception as e:
            self.log_result("comments", "create", False, None, e)
        
        return None

    def test_notifications_get(self):
        """Test get notifications"""
        try:
            response = self.make_request("GET", "/notifications")
            
            if response and response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_result("notifications", "get_all", True, f"Found {len(data)} notifications")
                    return True
                else:
                    self.log_result("notifications", "get_all", False, data, "Invalid notifications format")
            else:
                error_msg = response.text if response else "No response"
                self.log_result("notifications", "get_all", False, None, f"Status: {response.status_code if response else 'None'}, {error_msg}")
                
        except Exception as e:
            self.log_result("notifications", "get_all", False, None, e)
        
        return False

    def test_stats_get(self):
        """Test get stats"""
        try:
            response = self.make_request("GET", "/stats")
            
            if response and response.status_code == 200:
                data = response.json()
                required_fields = ["totalProjects", "totalTasks", "totalMembers"]
                if all(field in data for field in required_fields):
                    self.log_result("stats", "get_all", True, data)
                    return True
                else:
                    self.log_result("stats", "get_all", False, data, "Missing required stats fields")
            else:
                error_msg = response.text if response else "No response"
                self.log_result("stats", "get_all", False, None, f"Status: {response.status_code if response else 'None'}, {error_msg}")
                
        except Exception as e:
            self.log_result("stats", "get_all", False, None, e)
        
        return False

    def test_whatsapp_status(self):
        """Test WhatsApp status"""
        try:
            response = self.make_request("GET", "/whatsapp/status")
            
            if response and response.status_code == 200:
                data = response.json()
                if "enabled" in data and "connected" in data:
                    self.log_result("whatsapp", "status", True, data)
                    return True
                else:
                    self.log_result("whatsapp", "status", False, data, "Missing required WhatsApp status fields")
            else:
                error_msg = response.text if response else "No response"
                self.log_result("whatsapp", "status", False, None, f"Status: {response.status_code if response else 'None'}, {error_msg}")
                
        except Exception as e:
            self.log_result("whatsapp", "status", False, None, e)
        
        return False

    def run_all_tests(self):
        """Run all API tests in sequence"""
        print("🚀 Starting ProManage Backend API Tests")
        print("=" * 50)
        
        # 1. Test Authentication
        print("\n📝 Testing Authentication...")
        if not self.test_auth_login():
            print("❌ Login failed - cannot continue with authenticated tests")
            return False
        
        self.test_auth_me()
        self.test_auth_register()
        
        # 2. Test Users
        print("\n👥 Testing Users...")
        self.test_users_get()
        
        # 3. Test Projects
        print("\n📁 Testing Projects...")
        projects = self.test_projects_get()
        
        # Get first project for testing
        test_project_id = None
        if projects and len(projects) > 0:
            test_project_id = projects[0]["id"]
            self.test_project_get_by_id(test_project_id)
        
        # Create new project
        new_project_id = self.test_project_create()
        if new_project_id:
            test_project_id = new_project_id
        
        # 4. Test Tasks
        print("\n📋 Testing Tasks...")
        if test_project_id:
            existing_tasks = self.test_tasks_get(test_project_id)
            new_task_id = self.test_task_create(test_project_id)
            
            # Use existing task or new task for further testing
            test_task_id = None
            if existing_tasks and len(existing_tasks) > 0:
                test_task_id = existing_tasks[0]["id"]
            elif new_task_id:
                test_task_id = new_task_id
            
            # 5. Test Subtasks
            print("\n📝 Testing Subtasks...")
            if test_task_id:
                existing_subtasks = self.test_subtasks_get(test_task_id)
                new_subtask_id = self.test_subtask_create(test_task_id, test_project_id)
                
                # Test toggle subtask
                if new_subtask_id:
                    self.test_subtask_toggle_done(new_subtask_id)
                
                # 6. Test Business Rule: Try to complete task with incomplete subtasks
                print("\n⚖️ Testing Business Rules...")
                if new_subtask_id:
                    # Create another incomplete subtask
                    incomplete_subtask_data = {
                        "taskId": test_task_id,
                        "title": "Subtask Belum Selesai",
                        "projectId": test_project_id
                    }
                    response = self.make_request("POST", "/subtasks", incomplete_subtask_data)
                    if response and response.status_code == 200:
                        # Now try to complete the task - should fail
                        self.test_task_update_status(test_task_id, "Selesai")
                
                # 7. Test Comments
                print("\n💬 Testing Comments...")
                self.test_comments_get(test_task_id)
                self.test_comment_create(test_task_id)
        
        # 8. Test Notifications
        print("\n🔔 Testing Notifications...")
        self.test_notifications_get()
        
        # 9. Test Stats
        print("\n📊 Testing Stats...")
        self.test_stats_get()
        
        # 10. Test WhatsApp Status
        print("\n📱 Testing WhatsApp Status...")
        self.test_whatsapp_status()
        
        print("\n" + "=" * 50)
        print("🏁 All tests completed!")
        
        return True

    def print_summary(self):
        """Print test results summary"""
        print("\n📊 TEST RESULTS SUMMARY")
        print("=" * 50)
        
        total_tests = 0
        passed_tests = 0
        
        for category, tests in self.test_results.items():
            if tests:
                print(f"\n{category.upper()}:")
                for test_name, result in tests.items():
                    total_tests += 1
                    status = "✅ PASS" if result["success"] else "❌ FAIL"
                    print(f"  {status} {test_name}")
                    if result["success"]:
                        passed_tests += 1
                    elif result["error"]:
                        print(f"    Error: {result['error']}")
        
        print(f"\n📈 OVERALL: {passed_tests}/{total_tests} tests passed ({(passed_tests/total_tests*100):.1f}%)")
        
        if passed_tests == total_tests:
            print("🎉 All tests passed!")
        else:
            print(f"⚠️  {total_tests - passed_tests} tests failed")

def main():
    """Main test execution"""
    tester = ProManageAPITester()
    
    try:
        success = tester.run_all_tests()
        tester.print_summary()
        
        # Save detailed results to file
        with open("/app/test_results_detailed.json", "w") as f:
            json.dump(tester.test_results, f, indent=2)
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())