# FocusBoard Capacity Planning & Growth Modeling

## 1. Workload Modeling Assumptions
- Average active user generates 25 API requests per day.
- Read-to-write ratio: **80% reads / 20% writes**.
- Average database storage per user: **5 MB / year** (tasks, comments, activity logs).

---

## 2. Capacity Growth Tiers

| User Tier | Concurrent Users | Peak Req/Sec | Database Storage | Recommended Infrastructure Tier |
|---|---|---|---|---|
| **100 Users** | 5 – 10 | 1 – 3 | < 1 GB | 1 Container (0.5 vCPU, 512MB RAM), Free Tier Managed DB |
| **1,000 Users** | 50 – 100 | 15 – 30 | ~5 GB | 2 Containers (1 vCPU, 1GB RAM), Basic Managed DB (Neon/RDS) |
| **10,000 Users** | 500 – 1,000 | 150 – 300 | ~50 GB | 4 Containers (2 vCPU, 2GB RAM), 1 Read Replica, Redis Cache |
| **50,000 Users** | 2,500 – 5,000 | 750 – 1,500 | ~250 GB | Auto-scaled Container Cluster (4–8 nodes), 2 Read Replicas |
| **100,000 Users**| 5,000 – 10,000| 1,500 – 3,000| ~500 GB | Multi-AZ Container Cluster, Table Partitioning, Dedicated Workers |
