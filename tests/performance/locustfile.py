from locust import HttpUser, task, between
import json
import random
import os

class AIWorkOSUser(HttpUser):
    wait_time = between(1, 3)  # Wait 1-3 seconds between requests
    
    def on_start(self):
        """Called when a user starts"""
        self.api_key = os.getenv("API_KEY", "test-api-key")
        self.headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
        # Sample data for testing
        self.sample_texts = [
            "2025-08-19 Meeting: John needs to complete the database migration by Friday. Blocker: waiting for production access.",
            "Email from client: Sarah to review the UI mockups and provide feedback by Wednesday.",
            "Standup notes: Mike will fix the authentication bug today. Lisa working on the payment integration.",
            "Project update: Need to deploy the new features to staging environment by end of week.",
            "Customer support: Issue with file upload functionality reported by 3 users. High priority fix needed."
        ]
        
        self.sample_questions = [
            "What tasks are assigned to John?",
            "What are the current blockers?",
            "When is the database migration due?",
            "Who is working on the payment integration?",
            "What high priority issues do we have?"
        ]

    @task(3)
    def get_health_check(self):
        """Basic health check - most frequent"""
        self.client.get("/healthz")

    @task(1)
    def get_detailed_health_check(self):
        """Detailed health check"""
        self.client.get("/health/detailed")

    @task(2)
    def get_system_status(self):
        """Get system status"""
        self.client.get("/status")

    @task(5)
    def list_tasks(self):
        """List all tasks"""
        self.client.get("/tasks")

    @task(2)
    def list_tasks_with_filter(self):
        """List tasks with status filter"""
        status = random.choice(["new", "in_progress", "blocked", "done"])
        self.client.get(f"/tasks?status={status}")

    @task(1)
    def ingest_document(self):
        """Ingest a document"""
        text = random.choice(self.sample_texts)
        source = random.choice(["email", "meeting", "note", "other"])
        
        payload = {
            "text": text,
            "source": source
        }
        
        response = self.client.post(
            "/ingest",
            headers=self.headers,
            json=payload
        )
        
        # Store document ID for later use
        if response.status_code == 200:
            data = response.json()
            if hasattr(self, 'document_ids'):
                self.document_ids.append(data.get("document_id"))
            else:
                self.document_ids = [data.get("document_id")]

    @task(2)
    def ask_question(self):
        """Ask a question"""
        question = random.choice(self.sample_questions)
        top_k = random.randint(3, 8)
        
        payload = {
            "question": question,
            "top_k": top_k
        }
        
        self.client.post(
            "/ask",
            headers=self.headers,
            json=payload
        )

    @task(1)
    def update_task(self):
        """Update a task status"""
        # First get tasks to find one to update
        response = self.client.get("/tasks")
        if response.status_code == 200:
            tasks = response.json()
            if tasks:
                task = random.choice(tasks)
                task_id = task["id"]
                
                # Update task status
                new_status = random.choice(["in_progress", "blocked", "done"])
                payload = {
                    "status": new_status,
                    "owner": f"User{random.randint(1, 10)}"
                }
                
                self.client.patch(
                    f"/tasks/{task_id}",
                    headers=self.headers,
                    json=payload
                )

class HighLoadUser(AIWorkOSUser):
    """User class for high load testing"""
    wait_time = between(0.1, 0.5)  # Faster requests
    
    @task(10)
    def rapid_health_checks(self):
        """Rapid health checks to test rate limiting"""
        self.client.get("/healthz")

class APIStressUser(AIWorkOSUser):
    """User class for API stress testing"""
    wait_time = between(0, 0.1)  # Very fast requests
    
    @task(5)
    def stress_ingest(self):
        """Stress test the ingest endpoint"""
        text = "Stress test document " + "x" * random.randint(100, 1000)
        payload = {
            "text": text,
            "source": "other"
        }
        
        self.client.post(
            "/ingest",
            headers=self.headers,
            json=payload
        )

# Custom task classes for specific scenarios
class ReadOnlyUser(HttpUser):
    """User that only performs read operations"""
    wait_time = between(0.5, 2)
    
    @task(5)
    def read_tasks(self):
        self.client.get("/tasks")
    
    @task(3)
    def check_status(self):
        self.client.get("/status")
    
    @task(2)
    def health_check(self):
        self.client.get("/healthz")

class WriteHeavyUser(HttpUser):
    """User that performs many write operations"""
    wait_time = between(2, 5)
    
    def on_start(self):
        self.api_key = os.getenv("API_KEY", "test-api-key")
        self.headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
    
    @task(3)
    def ingest_documents(self):
        text = f"Load test document {random.randint(1, 1000)}: Lorem ipsum dolor sit amet."
        payload = {
            "text": text,
            "source": random.choice(["email", "meeting", "note"])
        }
        
        self.client.post(
            "/ingest",
            headers=self.headers,
            json=payload
        )
    
    @task(2)
    def ask_questions(self):
        question = f"What is the status of task {random.randint(1, 100)}?"
        payload = {
            "question": question,
            "top_k": 5
        }
        
        self.client.post(
            "/ask",
            headers=self.headers,
            json=payload
        )