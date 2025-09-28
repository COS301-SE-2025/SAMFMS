<!-- Project logo -->
<p align="center">
  <img src="docs/Demo4/images/logo_horisontal_light.svg" alt="Firewall Five — SAMFMS" height="84">
</p>

<p align="center">
  <img src="docs/Demo4/images/DNS.png" alt="Sponsor: DNS" height="64" style="margin: 0 14px;">
  <img src="docs/Demo4/images/LOGO_BLACK_FULLTRANSP.png" alt="Sponsor" height="64" style="margin: 0 14px;">
</p>

<!-- Optional project title under the logo -->
<h1 align="center">Firewall Five — SAMFMS</h1>
<p align="center">Modular Fleet Management System</p>

## 📚 Documentation

## 📚 Documentation

| Resource | Link |
|---|---|
| SRS & Architecture | [Requirements](docs/Demo3/Software%20Requirement%20Specification.pdf) |
| Project Board | [GitHub Projects](https://github.com/orgs/COS301-SE-2025/projects/208/views/2) |
| Coding Standards | [Guide](docs/Demo3/Coding_Standards.pdf) |
| Technical Installation | [Install Guide](docs/Demo3/Technical_Installation_Guide.pdf) |
| User Manual | [Manual](docs/Demo3/SAMFMS%20User%20Manual.pdf) |
| Deployment Strategy | [Deployment Model](docs/Demo3/Deployment%20Strategy.pdf) |
| Service Contracts | [Contracts](docs/Demo3/Service%20Contracts-1.pdf) |
| Branching Strategy | [Strategy](docs/Demo3/Branching_Strategy.pdf) |
| Updated Domain Model | [Domain Model](docs/Demo3/images/DomainModel.png) |
|---|---|
| SRS & Architecture | [Requirements](docs/Demo3/Software%20Requirement%20Specification.pdf) |
| Project Board | [GitHub Projects](https://github.com/orgs/COS301-SE-2025/projects/208/views/2) |
| Coding Standards | [Guide](docs/Demo3/Coding_Standards.pdf) |
| Technical Installation | [Install Guide](docs/Demo3/Technical_Installation_Guide.pdf) |
| User Manual | [Manual](docs/Demo3/SAMFMS%20User%20Manual.pdf) |
| Deployment Strategy | [Deployment Model](docs/Demo3/Deployment%20Strategy.pdf) |
| Service Contracts | [Contracts](docs/Demo3/Service%20Contracts-1.pdf) |
| Branching Strategy | [Strategy](docs/Demo3/Branching_Strategy.pdf) |
| Updated Domain Model | [Domain Model](docs/Demo3/images/DomainModel.png) |

Older docs:
- Demo 1 SRS: [Google Doc](https://docs.google.com/document/d/1En1Mck7JwaSdKjgyvRhmX5pXqHhVSUlhZhp7XU-f_K4/edit?tab=t.0)
- Demo 2 SRS: [Google Doc](https://docs.google.com/document/d/1G0PdNyn39kSutfvn8tCN5x-yCHrte0QFu_v2-gYdXPU/edit?tab=t.0)
- Demo 2 Slides: [Canva Presentation](https://www.canva.com/design/DAGrW5d1HYA/LC1cf0PKTY7MIsAVtObYPA/edit)
Older docs:
- Demo 1 SRS: [Google Doc](https://docs.google.com/document/d/1En1Mck7JwaSdKjgyvRhmX5pXqHhVSUlhZhp7XU-f_K4/edit?tab=t.0)
- Demo 2 SRS: [Google Doc](https://docs.google.com/document/d/1G0PdNyn39kSutfvn8tCN5x-yCHrte0QFu_v2-gYdXPU/edit?tab=t.0)
- Demo 2 Slides: [Canva Presentation](https://www.canva.com/design/DAGrW5d1HYA/LC1cf0PKTY7MIsAVtObYPA/edit)

---

## 👥 Team

| Profile | Name (Student No.) | GitHub | LinkedIn | Focus |
|---|---|---|---|---|
| <img src="docs/Demo3/images/stefan.jpg" width="56" /> | Mr. Stefan Jansen van Rensburg (u22550055) | [StefanJvRCodes](https://github.com/StefanJvRCodes) | [Stefan Jansen van Rensburg](https://linkedin.com/in/stefan-JvR) | Team lead, CI/CD, daemon & backend services (storage, CRUD, file I/O, server & user mgmt) |
| <img src="docs/Demo3/images/johan.jpeg" width="56" /> | Mr. Johan Jansen van Rensburg (u22590732) | [22590732](https://github.com/22590732) | [Johan Jansen van Rensburg](https://www.linkedin.com/in/nicolaas-jansen-van-rensburg-202629363/) | UI engineering & design, frontend architecture, service integration |
| <img src="docs/Demo3/images/laird.png" width="56" /> | Mr. Laird Glanville (u22541332) | [Laird-G](https://github.com/Laird-G) | [Laird Glanville](https://www.linkedin.com/in/laird-glanville-046270326/) | Backend engineering, MCore development, modular SBlocks |
| <img src="docs/Demo3/images/morne.jpeg" width="56" /> | Mr. Morné van Heerden (u21482153) | [Mornevanheerden](https://github.com/Mornevanheerden) | [Morné van Heerden](https://www.linkedin.com/in/morne-van-heerden-a0b173355/) | DevOps & systems, repo maintenance, services engineering |
| <img src="docs/Demo3/images/herrie.jpg" width="56" /> | Mr. Herman Engelbrecht (u22512374) | [herrie732](https://github.com/herrie732) | [Herman Engelbrecht](https://www.linkedin.com/in/herman-johan-engelbrecht-a6b6a8327/) | Services engineering, loosely coupled SBlocks, frontend & DB management |

---

## 🧭 Overview

SAMFMS is a modular fleet platform that avoids “buy-everything” bloat. Start with a lightweight core (MCore) and install only the features you need as plug-in modules (SBlocks): location tracking, trip planning, maintenance, and driver/vehicle management. Start lean. Scale smoothly.

- Install only what you need  
- Clear separation of core, services, and UI  
- Event-driven and scalable  
- Developer-friendly monorepo with shared contracts

---

## 🧱 Architecture 

### MCore
- Auth hooks, configuration, service discovery, and shared contracts
- API routing and standards across services
- Event catalog & schemas for cross-module messaging

### SBlocks (Modules)
- Independently deployable feature services that register with MCore
- Stable FastAPI interfaces & clear boundaries  
- Examples: Location, Trips, Maintenance, Driver/Vehicle

### Communication & Data
- FastAPI for REST + service-to-service calls  
- RabbitMQ for async pub/sub between modules  
- MongoDB for operational & historical data

### Frontend
- React + Tailwind for a crisp, responsive UI  
- Leaflet for live maps, positions, and routes

### Deployment
- Dockerized services and Compose for local  
- Environment-driven configuration & secrets  
- Modules deploy independently in production

---

Notes:
- Issues in [GitHub Issues](https://github.com/COS301-SE-2025/SAMFMS/issues)
- Branching model: [Strategy](docs/Demo3/Branching_Strategy.pdf)

---

## 🧰 Technology

![Leaflet](https://img.shields.io/badge/Leaflet-199900?style=for-the-badge&logo=leaflet&logoColor=white)
![RabbitMQ](https://img.shields.io/badge/RabbitMQ-FF6600?style=for-the-badge&logo=rabbitmq&logoColor=white)
![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-4DB33D?style=for-the-badge&logo=mongodb&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)

