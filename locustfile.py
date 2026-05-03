from locust import HttpUser, task, between
import uuid

class BookLoadTest(HttpUser):
    # Wait time between tasks
    wait_time = between(1, 3)

    def on_start(self):
        self.username = f"test_{uuid.uuid4().hex[:8]}"
        self.password = "loadtest123"
        
        self.client.post("/api/auth/register", json={
            "username": self.username,
            "password": self.password
        })
        
        res = self.client.post("/api/auth/login", data={
            "username": self.username,
            "password": self.password
        })
        
        if res.status_code == 200:
            data = res.json()
            token = data.get("access_token")
            self.refresh_token = data.get("refresh_token")
            self.client.headers.update({"Authorization": f"Bearer {token}"})
        else:
            print(f"Login failed: {res.text}")

    @task
    def get_all_books(self):
        with self.client.get("/api/books", catch_response=True) as response:
            if response.status_code == 401:
                refresh_res = self.client.post("/api/auth/refresh", json={
                    "refresh_token": self.refresh_token
                })
                if refresh_res.status_code == 200:
                    data = refresh_res.json()
                    new_token = data.get("access_token")
                    self.refresh_token = data.get("refresh_token")
                    self.client.headers.update({"Authorization": f"Bearer {new_token}"})
                    
                    retry_res = self.client.get("/api/books")
                    if retry_res.status_code == 200:
                        response.success()
                    else:
                        response.failure(f"Retry failed with {retry_res.status_code}: {retry_res.text}")
                else:
                    login_res = self.client.post("/api/auth/login", data={
                        "username": self.username,
                        "password": self.password
                    })
                    if login_res.status_code == 200:
                        data = login_res.json()
                        new_token = data.get("access_token")
                        self.refresh_token = data.get("refresh_token")
                        self.client.headers.update({"Authorization": f"Bearer {new_token}"})
                        self.client.get("/api/books")
                        response.success()
                    else:
                        response.failure(f"Refresh and re-login failed: {refresh_res.text}")
