from locust import HttpUser, task, between


class AttackUser(HttpUser):
    wait_time = between(0.1, 0.5)

    @task
    def hit_ping(self):
        self.client.get("/ping")
