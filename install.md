# Biotime Service Installation & Update Guide

This guide describes how to install or update the Biotime Service on your local machine (e.g., iMac) using Docker.

## Prerequisites

- **Docker Desktop** installed and running.
- **Git** installed.
- Access to the GitHub repository: `https://github.com/HappyLife2/Biotime_Service.git`

---

## Option 1: Fresh Installation

If you are setting this up for the first time:

1.  **Clone the Repository**
    Open your terminal and run:
    ```bash
    cd ~/Desktop
    git clone https://github.com/HappyLife2/Biotime_Service.git
    cd Biotime_Service
    ```

2.  **Configure Environment (Optional)**
    The `docker-compose.yml` comes with default environment variables. If you need to change the Biotime server URL or credentials, edit the `docker-compose.yml` file:
    ```bash
    nano docker-compose.yml
    ```

3.  **Start the Service**
    Build and start the container in the background:
    ```bash
    docker compose up -d --build
    ```

4.  **Verify**
    Check if the service is running:
    ```bash
    docker ps
    ```
    Your service should be listed and compliant (healthy).

---

## Option 2: Update Existing Installation

If you already have the service running and want to pull the latest changes (e.g., new reporting scripts):

1.  **Navigate to Project Directory**
    ```bash
    cd /Users/jehad/Desktop/Biotime_Service
    ```

2.  **Pull Latest Changes**
    Download the latest code from GitHub:
    ```bash
    git pull
    ```
    *Note: If you have local conflicts, you can overwrite them with `git reset --hard origin/main`.*

3.  **Rebuild and Restart**
    This step is **crucial**. You must rebuild the container for the new Python code to be copied inside.
    ```bash
    docker compose up -d --build
    ```

4.  **Verify Update**
    Run a test command to ensure the new API features are active:
    ```bash
    curl -s "http://localhost:8000/attendance/report/monthly" | head -c 100
    ```

---

## Troubleshooting

- **Port Conflicts**: If the container fails to start because port `8000` is in use, make sure no invalid python scripts or other services are running on that port.
- **Database Connection**: Ensure your host machine accepts connections from the Docker container if you are pointing `BIOTIME_BASE` to a local IP.
