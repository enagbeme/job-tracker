# Job Application Tracker — Docker + ECS Fargate + CI/CD

A production-grade job application tracking web app built with Python FastAPI. Originally deployed on EC2 + RDS, then containerized with Docker and migrated to ECS Fargate with a fully automated GitHub Actions CI/CD pipeline.

## Live Demo

**http://3.144.48.59:8000**

## Architecture

### Current: Containerized on ECS Fargate with CI/CD

```
┌──────────────┐       ┌──────────────────┐       ┌──────────────┐
│   Developer  │       │  GitHub Actions   │       │  Amazon ECR  │
│   git push   │──────▶│  (CI/CD Pipeline) │──────▶│  (Registry)  │
└──────────────┘       └────────┬─────────┘       └──────┬───────┘
                                │                        │
                                │  Deploy                │  Pull image
                                ▼                        ▼
                       ┌─────────────────────────────────────────┐
                       │           Amazon ECS Fargate            │
                       │  ┌───────────────────────────────────┐  │
                       │  │  job-tracker container            │  │
                       │  │  Python 3.11 + FastAPI + Uvicorn  │  │
                       │  │  Port 8000                        │  │
                       │  └───────────────────────────────────┘  │
                       └─────────────────────────────────────────┘
```

### Previous: EC2 + RDS (manual deployment)

```
                                     Private VPC
                              ┌─────────────────────────┐
┌──────────┐   Port 8000      │  ┌──────────────────┐   │   Port 5432    ┌──────────────────┐
│  Browser │ ────────────────▶│  │   EC2 Instance   │───│──────────────▶│  RDS PostgreSQL  │
│  (User)  │                  │  │   t2.micro        │   │               │  db.t4g.micro    │
│          │◀────────────────│  │   FastAPI+Uvicorn │◀──│───────────────│  jobtracker db   │
└──────────┘                  │  │   systemd service │   │               └──────────────────┘
                              │  └──────────────────┘   │
                              └─────────────────────────┘
```

## AWS Services Used

| Service | Purpose |
|---------|---------|
| **Amazon ECS (Fargate)** | Serverless container orchestration — runs the Docker container without managing servers |
| **Amazon ECR** | Private Docker registry to store container images |
| **Amazon EC2** | Original deployment target (t2.micro, Amazon Linux 2023) |
| **Amazon RDS** | Managed PostgreSQL database (db.t4g.micro) with automated backups |
| **VPC** | Private network for secure EC2 ↔ RDS communication |
| **Security Groups** | Firewall rules controlling access to ECS, EC2, and RDS |
| **CloudWatch** | Container logs and monitoring for ECS tasks |
| **IAM** | Task execution role with least-privilege permissions for ECS |

## Key Concepts Demonstrated

### Docker Containerization
- Created a multi-layer `Dockerfile` with dependency caching — `requirements.txt` is copied and installed before app code, so rebuilds only reinstall packages when dependencies change
- Used `python:3.11-slim` base image to minimize container size
- Added `.dockerignore` to exclude unnecessary files (`.git`, `*.db`, `.env`) from the image
- Built and tested the container locally before pushing to AWS

### ECS Fargate (Serverless Containers)
- Created an ECS cluster and Fargate service — no EC2 instances to manage
- Defined a task definition specifying container image, CPU (0.25 vCPU), memory (512MB), and port mappings
- Configured the service to maintain exactly 1 running task with automatic restarts on failure
- Assigned a public IP for direct access without a load balancer

### CI/CD with GitHub Actions
- Built a fully automated deployment pipeline triggered on every push to `main`
- Pipeline steps: checkout code → authenticate with AWS → login to ECR → build Docker image → push to ECR → update ECS task definition → deploy to ECS → wait for service stability
- Used official AWS GitHub Actions (`configure-aws-credentials`, `amazon-ecr-login`, `amazon-ecs-render-task-definition`, `amazon-ecs-deploy-task-definition`)
- Stored AWS credentials as GitHub repository secrets — never hardcoded

### ECR (Elastic Container Registry)
- Created a private repository to store Docker images
- Images are tagged with both `latest` and the git commit SHA for traceability
- ECR is in the same region as ECS for fast image pulls

### EC2 + RDS (Original Deployment)
- Launched an Amazon Linux 2023 instance with SSH key pair access
- Set up the app as a **systemd service** for persistent execution — auto-restarts on failure and survives reboots
- Created a PostgreSQL database on RDS with **no public access** — only reachable from within the VPC
- Configured security groups so RDS only accepts traffic from the EC2 security group (least privilege)

### Deployment Evolution
```
Manual:     Code → git push → SSH into EC2 → git pull → restart systemd
Automated:  Code → git push → GitHub Actions → Docker build → ECR → ECS (zero touch)
```

## Application Features

### Dashboard
- **Stats cards** — Total applied, interviewing, offers received, response rate
- **Donut chart** — Visual breakdown of application statuses
- **Upcoming interviews** — Calendar-style list with dates and companies
- **Weekly activity** — Bar chart showing application activity over time

### Application Management
- **Table view** — Sortable table with inline status updates via dropdown
- **Kanban board** — Drag-style columns organized by status (Saved, Applied, Phone Screen, Technical Interview, etc.)
- **Search** — Filter by company, role, or location
- **Filter pills** — Quick filter by status category
- **CSV export** — Download all applications as a spreadsheet

### Forms
- **Add application** — Company, role, status, priority, job type, location, salary range, interview date, contact info, notes
- **Edit application** — Update any field with pre-filled values
- **Quick status update** — Change status directly from the table via dropdown

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.11, FastAPI, SQLAlchemy ORM |
| **Frontend** | Jinja2 templates, vanilla CSS (glassmorphism design), vanilla JS |
| **Database** | PostgreSQL (RDS) / SQLite (local development) |
| **Container** | Docker, Amazon ECR |
| **Orchestration** | Amazon ECS Fargate |
| **CI/CD** | GitHub Actions |
| **Server** | Uvicorn ASGI server |

## Project Structure

```
job-tracker/
├── .github/
│   └── workflows/
│       └── deploy.yml           # GitHub Actions CI/CD pipeline
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI routes and application logic
│   ├── models.py                # SQLAlchemy models (JobApplication)
│   ├── database.py              # Database connection and session management
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css        # Dark theme with glassmorphism, charts, kanban
│   │   └── js/
│   │       └── main.js          # Animated counters, chart animations, keyboard shortcuts
│   └── templates/
│       ├── base.html            # Base layout with sidebar navigation
│       ├── dashboard.html       # Dashboard with stats, charts, table/kanban views
│       ├── add.html             # Add new application form
│       └── edit.html            # Edit existing application form
├── Dockerfile                   # Container build instructions
├── .dockerignore                # Files excluded from Docker image
├── task-definition.json         # ECS Fargate task configuration
├── requirements.txt             # Python dependencies
├── run.py                       # Local development server launcher
└── README.md
```

## Local Development

```bash
# Clone the repo
git clone https://github.com/enagbeme/job-tracker.git
cd job-tracker

# Run with Docker
docker build -t job-tracker .
docker run -p 8000:8000 job-tracker

# Or run without Docker
pip install -r requirements.txt
python run.py

# Open http://localhost:8000
```

## AWS Deployment (ECS Fargate)

### 1. Create ECR Repository
```bash
aws ecr create-repository --repository-name job-tracker --region us-east-2
```

### 2. Build and Push Docker Image
```bash
# Login to ECR
aws ecr get-login-password --region us-east-2 | docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.us-east-2.amazonaws.com

# Build, tag, and push
docker build -t job-tracker .
docker tag job-tracker:latest <ACCOUNT_ID>.dkr.ecr.us-east-2.amazonaws.com/job-tracker:latest
docker push <ACCOUNT_ID>.dkr.ecr.us-east-2.amazonaws.com/job-tracker:latest
```

### 3. Create ECS Cluster
```bash
aws ecs create-cluster --cluster-name job-tracker-cluster --region us-east-2
```

### 4. Set Up ECS (AWS Console)
- Create IAM role `ecsTaskExecutionRole` with `AmazonECSTaskExecutionRolePolicy`
- Create CloudWatch log group `/ecs/job-tracker`
- Create task definition: Fargate, 0.25 vCPU, 512MB, container port 8000
- Create service: 1 desired task, public subnet, auto-assign public IP, security group allowing port 8000

### 5. Set Up CI/CD
- Add `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` as GitHub repository secrets
- Push code to `main` branch — GitHub Actions handles the rest

## Previous Deployment (EC2 + RDS)

### EC2 Setup
```bash
ssh -i "key.pem" ec2-user@<EC2-PUBLIC-IP>
sudo dnf install python3.11 python3.11-pip -y
git clone https://github.com/enagbeme/job-tracker.git
cd job-tracker
pip3.11 install -r requirements.txt
pip3.11 install psycopg2-binary
export DATABASE_URL="postgresql://postgres:<PASSWORD>@<RDS-ENDPOINT>:5432/jobtracker?sslmode=require"
python3.11 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### systemd Service
```bash
sudo tee /etc/systemd/system/jobtracker.service << 'EOF'
[Unit]
Description=Job Tracker FastAPI App
After=network.target

[Service]
User=ec2-user
WorkingDirectory=/home/ec2-user/job-tracker
Environment=DATABASE_URL=postgresql://postgres:<PASSWORD>@<RDS-ENDPOINT>:5432/jobtracker?sslmode=require
ExecStart=/home/ec2-user/.local/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable jobtracker
sudo systemctl start jobtracker
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Dashboard (table or kanban view) |
| GET | `/add` | Add application form |
| POST | `/add` | Submit new application |
| GET | `/edit/{id}` | Edit application form |
| POST | `/edit/{id}` | Update application |
| POST | `/delete/{id}` | Delete application |
| POST | `/update-status/{id}` | Quick status update |
| GET | `/export` | Download CSV export |
| GET | `/api/applications` | JSON API: list applications |
| GET | `/api/stats` | JSON API: dashboard statistics |

## Keyboard Shortcuts
- `/` — Focus search bar
- `n` — Navigate to Add Application

## What I Learned
- Docker containerization with multi-layer caching for fast rebuilds
- Amazon ECR as a private container registry
- ECS Fargate for serverless container orchestration
- GitHub Actions CI/CD pipeline with AWS integration
- Task definitions, service configuration, and IAM roles for ECS
- Evolution from manual EC2 deployment to fully automated container deployment
- EC2 instance setup, SSH access, and systemd service management
- RDS managed database with private VPC connectivity
- Security group configuration for least-privilege network access

## Built With
- Python 3.11, FastAPI, SQLAlchemy, Jinja2
- Docker, Amazon ECR, Amazon ECS Fargate
- GitHub Actions (CI/CD)
- PostgreSQL (AWS RDS), SQLite (local)
- AWS EC2, RDS, VPC, Security Groups, CloudWatch, IAM
