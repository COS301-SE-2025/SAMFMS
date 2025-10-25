<!-- Project logo -->
<p align="center">
  <img
    src="https://raw.githubusercontent.com/COS301-SE-2025/SAMFMS/main/docs/Demo4/images/logo_horisontal_light.svg?sanitize=true"
    alt="Firewall Five — SAMFMS"
    width="640"
  >
</p>

<p align="center">
  <img src="docs/Demo4/images/DNS.png" alt="Sponsor: DNS" height="100" style="margin: 0 14px;">
  <img src="docs/Demo4/images/LOGO_BLACK_FULLTRANSP.png" alt="Sponsor" height="100" style="margin: 0 14px;">
</p>

<!-- Optional project title under the logo -->
<h1 align="center">Firewall Five — SAMFMS</h1>
<h2 align="center">Winners of the Entelect Software Engineering Excellence Award 2025</h2>
<p align="center">Modular Fleet Management System</p>

## 📚 Documentation

Note: Table of contents for SRS is broken, everything is there.

| Demo 1 | Demo 2 | Demo 3  | Demo 4 |
|---|---|---|---|
|[SRS & Architecture](docs/Demo1/Software%20Requirement%20Specification.pdf)|[SRS & Architecture](docs/Demo2/Software%20Requirement%20Specification.pdf)| [SRS & Architecture](docs/Demo3/Software%20Requirement%20Specification.pdf) | [SRS & Architecture](docs/Demo4/Software%20Requirement%20Specification.pdf) |
||| [Project Board](https://github.com/orgs/COS301-SE-2025/projects/208/views/2) | [Project Board](https://github.com/orgs/COS301-SE-2025/projects/208/views/2) |
||| [Coding Standards](docs/Demo3/Coding_Standards.pdf) | [Coding Standards](docs/Demo4/SAMFMS%20Coding%20Standards%20Document.pdf) |
||| [Technical Installation](docs/Demo3/Technical_Installation_Guide.pdf) | [Technical Installation](docs/Demo4/SAMFMS%20Technical%20Installation%20Guide.pdf) |
||| [User Manual](docs/Demo3/SAMFMS%20User%20Manual.pdf) | [User Manual](docs/Demo4/SAMFMS%20User%20Manual%20Final.pdf) |
||| [Deployment Strategy](docs/Demo3/Deployment%20Strategy.pdf) | [Deployment Strategy](docs/Demo4/Deployment%20Strategy.pdf) |
||| [Service Contracts](docs/Demo3/Service%20Contracts-1.pdf) | [Service Contracts](docs/Demo4/Service%20Contracts.pdf) |
|[Branching Strategy](docs/Demo1/Branching_Strategy.pdf)|[Branching Strategy](docs/Demo2/Branching_Strategy.pdf)| [Branching Strategy](docs/Demo3/Branching_Strategy.pdf) | [Branching Strategy](docs/Demo4/Branching_Strategy.pdf) |
||| [Updated Domain Model](docs/Demo3/images/DomainModel.png) | [Domain Model](docs/Demo4/images/domainModel.png) |
||||[Testing Policy](docs/Demo4/Testing%20Policy.docx-3.pdf)|



Older docs:
- Demo 2 Slides: [Canva Presentation](https://www.canva.com/design/DAGrW5d1HYA/LC1cf0PKTY7MIsAVtObYPA/edit)

## Demo Video
[![Firewall Five — SAMFMS demo](https://img.youtube.com/vi/JEtQA2nmG4o/hqdefault.jpg)](https://www.youtube.com/watch?v=JEtQA2nmG4o)


## 👥 Team

| Profile | Name (Student No.) | GitHub | LinkedIn | Focus |
|---|---|---|---|---|
| <img src="docs/Demo3/images/stefan.jpg" width="56" /> | Mr. Stefan Jansen van Rensburg (u22550055) | [StefanJvRCodes](https://github.com/StefanJvRCodes) | [Stefan Jansen van Rensburg](https://linkedin.com/in/stefan-JvR) | Team lead, CI/CD, daemon & backend services (storage, CRUD, file I/O, server & user mgmt) |
| <img src="docs/Demo3/images/johan.jpeg" width="56" /> | Mr. Johan Jansen van Rensburg (u22590732) | [22590732](https://github.com/22590732) | [Johan Jansen van Rensburg](https://www.linkedin.com/in/nicolaas-jansen-van-rensburg-202629363/) | UI engineering & design, frontend architecture, service integration |
| <img src="docs/Demo3/images/laird.png" width="56" /> | Mr. Laird Glanville (u22541332) | [Laird-G](https://github.com/Laird-G) | [Laird Glanville](https://www.linkedin.com/in/laird-glanville-046270326/) | Backend engineering, MCore development, modular SBlocks |
| <img src="docs/Demo3/images/morne.jpeg" width="56" /> | Mr. Morné van Heerden (u21482153) | [Mornevanheerden](https://github.com/Mornevanheerden) | [Morné van Heerden](https://www.linkedin.com/in/morne-van-heerden-a0b173355/) | CO-Leader, DevOps & System Architect. Responsible for maintaining code standards, Docker containerization and deployment|
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

