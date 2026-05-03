from locust import HttpUser, task, between
import uuid

class BookLoadTest(HttpUser):
    # Wait time between tasks
    wait_time = between(1, 3)

    def on_start(self):
        # Create a unique user for each Locust worker/virtual user
        self.username = f"test_{uuid.uuid4().hex[:8]}"
        self.password = "loadtest123"
        
        # Register the user
        self.client.post("/api/auth/register", json={
            "username": self.username,
            "password": self.password
        })
        
        # Login to get the token
        res = self.client.post("/api/auth/login", data={
            "username": self.username,
            "password": self.password
        })
        
        if res.status_code == 200:
            token = res.json().get("access_token")
            # Automatically attach the token to all future requests for this virtual user
            self.client.headers.update({"Authorization": f"Bearer {token}"})
        else:
            print(f"Login failed: {res.text}")

    @task
    def get_all_books(self):
        self.client.get("/api/books")
