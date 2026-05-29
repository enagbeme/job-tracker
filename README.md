# Job Application Tracker - Full-Stack App on EC2 + RDS

A production-grade job application tracking web app built with Python FastAPI, deployed on an AWS EC2 instance with a managed RDS PostgreSQL database. Features a modern dark-themed dashboard with analytics charts, kanban board, table view, search, filtering, and CSV export.

## Live Demo

**http://3.16.124.86:8000**

## Architecture

```
                                     Private VPC
                              ┌─────────────────────────┐
                              │                         │
┌──────────┐   Port 8000      │  ┌──────────────────┐   │   Port 5432    ┌──────────────────┐
│  Browser │ ────────────────▶│  │   EC2 Instance   │───│──────────────▶│  RDS PostgreSQL  │
│  (User)  │                  │  │   t2.micro        │   │               │  db.t4g.micro    │
│          │◀────────────────│  │   Amazon Linux    │◀──│───────────────│  jobtracker db   │
└──────────┘                  │  │   FastAPI+Uvicorn │   │               └──────────────────┘
                              │  │   systemd service │   │                  No public access
                              │  └──────────────────┘   │
                              │                         │
                              └─────────────────────────┘
```

## AWS Services Used

| Service | Purpose |
|---------|---------|
| **Amazon EC2** | Virtual Linux server (t2.micro) running the FastAPI application |
| **Amazon RDS** | Managed PostgreSQL database (db.t4g.micro) with automated backups |
| **VPC** | Private network containing both EC2 and RDS for secure communication |
| **Security Groups** | Firewall rules controlling access to EC2 (ports 22, 8000) and RDS (port 5432) |

## Key Concepts Demonstrated

### EC2 Instance Management
- Launched an Amazon Linux 2023 instance with a `.pem` key pair for SSH access
- Installed Python, cloned the application from GitHub, configured environment variables
- Set up the app as a **systemd service** for persistent execution — auto-restarts on failure and survives reboots
- Configured security group to allow SSH (port 22) from my IP only, and HTTP (port 8000) from anywhere

### RDS Managed Database
- Created a PostgreSQL database on the free tier (db.t4g.micro)
- RDS handles backups, patching, and availability automatically
- Set **Public Access to No** — the database is only reachable from within the VPC
- Created an initial database (`jobtracker`) during setup
- Connected from EC2 using the RDS endpoint with SSL (`sslmode=require`)

### Security Groups as Firewalls
- **EC2 Security Group** (`job-tracker-sg`):
  - Inbound: Port 22 (SSH) from my IP, Port 8000 (HTTP) from 0.0.0.0/0
- **RDS Security Group** (`default`):
  - Inbound: Port 5432 (PostgreSQL) from `job-tracker-sg` only
- This ensures the database is **never exposed to the internet** — only the EC2 instance can connect

### Deployment Pipeline
```
Local development → Git push → SSH into EC2 → Git clone → Install deps → Configure env → systemd start
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
| **Server** | Uvicorn ASGI server, systemd service manager |

## Project Structure

```
job-tracker/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI routes and application logic
│   ├── models.py            # SQLAlchemy models (JobApplication)
│   ├── database.py          # Database connection and session management
│   ├── job_fetcher.py       # Auto-fetch jobs from free APIs
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css    # Dark theme with glassmorphism, charts, kanban
│   │   └── js/
│   │       └── main.js      # Animated counters, chart animations, keyboard shortcuts
│   └── templates/
│       ├── base.html         # Base layout with sidebar navigation
│       ├── dashboard.html    # Dashboard with stats, charts, table/kanban views
│       ├── add.html          # Add new application form
│       └── edit.html         # Edit existing application form
├── requirements.txt          # Python dependencies
├── run.py                    # Local development server launcher
├── fetch_daily.py            # Standalone script for daily job fetching (cron)
└── README.md
```

## Local Development

```bash
# Clone the repo
git clone https://github.com/enagbeme/job-tracker.git
cd job-tracker

# Install dependencies
pip install -r requirements.txt

# Run locally (uses SQLite)
python run.py

# Open http://localhost:8000
```

## AWS Deployment

### 1. Create RDS PostgreSQL
- Engine: PostgreSQL (free tier, db.t4g.micro)
- Initial database name: `jobtracker`
- Public access: No

### 2. Launch EC2 Instance
- AMI: Amazon Linux 2023
- Instance type: t2.micro (free tier)
- Security group: SSH (port 22, my IP) + HTTP (port 8000, anywhere)

### 3. Allow EC2 → RDS Connection
- Add inbound rule to RDS security group: PostgreSQL (5432) from EC2 security group

### 4. Deploy the App
```bash
# SSH into EC2
ssh -i "key.pem" ec2-user@<EC2-PUBLIC-IP>

# Install dependencies
sudo dnf install python3.11 python3.11-pip -y
git clone https://github.com/enagbeme/job-tracker.git
cd job-tracker
pip3.11 install -r requirements.txt
pip3.11 install psycopg2-binary

# Set database connection
export DATABASE_URL="postgresql://postgres:<PASSWORD>@<RDS-ENDPOINT>:5432/jobtracker?sslmode=require"

# Test
python3.11 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 5. Set Up systemd Service
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
| POST | `/fetch-jobs` | Fetch jobs from free APIs |
| GET | `/api/applications` | JSON API: list applications |
| GET | `/api/stats` | JSON API: dashboard statistics |
| GET | `/api/fetch-jobs` | JSON API: fetch jobs (for cron) |

## Keyboard Shortcuts
- `/` — Focus search bar
- `n` — Navigate to Add Application

## What I Learned
- EC2 instance setup, SSH access, and application deployment
- RDS managed database creation and private VPC connectivity
- Security group configuration for least-privilege network access
- systemd service management for persistent application hosting
- Full deployment pipeline from local development to production
- Database abstraction with SQLAlchemy (SQLite locally, PostgreSQL in production)

## Built With
- Python 3.11, FastAPI, SQLAlchemy, Jinja2
- PostgreSQL (AWS RDS), SQLite (local)
- AWS EC2, RDS, VPC, Security Groups
