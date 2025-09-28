<div align="center">

# Firewall Five — SAMFMS  
Modular Fleet Management System for growing fleets 🚚✨

</div>

---

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

Older docs:
- Demo 1 SRS: [Google Doc](https://docs.google.com/document/d/1En1Mck7JwaSdKjgyvRhmX5pXqHhVSUlhZhp7XU-f_K4/edit?tab=t.0)
- Demo 2 SRS: [Google Doc](https://docs.google.com/document/d/1G0PdNyn39kSutfvn8tCN5x-yCHrte0QFu_v2-gYdXPU/edit?tab=t.0)
- Demo 2 Slides: [Canva Presentation](https://www.canva.com/design/DAGrW5d1HYA/LC1cf0PKTY7MIsAVtObYPA/edit)

---

## 👥 Team

| Profile | Name (Student No.) | GitHub | LinkedIn | Focus |
|---|---|---|---|---|
| <img src="docs/Demo3/images/stefan.jpg" width="56" /> | Mr. Stefan Jansen van Rensburg (u22550055) | [StefanJvRCodes](https://github.com/StefanJvRCodes) | [Stefan Jansen van Rensburg](https://linkedin.com/in/stefan-JvR) | Team lead, CI/CD, daemon and backend services (storage, CRUD, file I/O, server and user management) |
| <img src="docs/Demo3/images/johan.jpeg" width="56" /> | Mr. Johan Jansen van Rensburg (u22590732) | [22590732](https://github.com/22590732) | [Johan Jansen van Rensburg](https://www.linkedin.com/in/nicolaas-jansen-van-rensburg-202629363/) | UI engineering and design, frontend architecture, service integration |
| <img src="docs/Demo3/images/laird.png" width="56" /> | Mr. Laird Glanville (u22541332) | [Laird-G](https://github.com/Laird-G) | [Laird Glanville](https://www.linkedin.com/in/laird-glanville-046270326/) | Backend engineering, MCore development, modular SBlocks |
| <img src="docs/Demo3/images/morne.jpeg" width="56" /> | Mr. Morné van Heerden (u21482153) | [Mornevanheerden](https://github.com/Mornevanheerden) | [Morné van Heerden](https://www.linkedin.com/in/morne-van-heerden-a0b173355/) | DevOps and systems, repository maintenance, services engineering |
| <img src="docs/Demo3/images/herrie.jpg" width="56" /> | Mr. Herman Engelbrecht (u22512374) | [herrie732](https://github.com/herrie732) | [Herman Engelbrecht](https://www.linkedin.com/in/herman-johan-engelbrecht-a6b6a8327/) | Services engineering, loosely coupled SBlocks, frontend and database management |

---

## 🧭 Overview

SAMFMS is a modular fleet platform built to avoid “buy-everything” bloat. Start with a lightweight core (MCore), then add only the modules you need (SBlocks): location tracking, trip planning, maintenance, and driver/vehicle management. Simple to start. Easy to extend. Cost-aware for smaller teams.

### Why SAMFMS?  
- ✅ Install only what you need  
- ✅ Clean separation between core, services, and UI  
- ✅ Event-driven and scalable from day one  
- ✅ Friendly developer experience (monorepo, shared contracts, strong docs)

---

## 🧱 Architecture

```mermaid
flowchart LR
  subgraph UI[React + Tailwind]
    A[Web App]
  end

  subgraph CORE[MCore]
    G[Auth & Config]
    H[Service Registry]
    I[Contracts & Schemas]
  end

  subgraph BUS[RabbitMQ]
    Q[[Events]]
  end

  subgraph MODS[SBlocks]
    M1[Location Tracking]
    M2[Trip Planning]
    M3[Maintenance]
    M4[Driver/Vehicle]
  end

  subgraph DATA[MongoDB]
    D[(Operational Data)]
  end

  A <-- REST/WebSocket --> CORE
  A <-- REST --> MODS
  CORE <-- REST --> MODS
  MODS <-- pub/sub --> BUS
  MODS <-- CRUD --> DATA
  CORE <-- CRUD --> DATA
```

### MCore
- Authentication hooks, configuration, service discovery, and shared contracts.
- Central API routing and standards enforcement.
- Event catalog and schema definitions for cross-module messaging.

### SBlocks (Modules)
- Independently deployable feature services that register with MCore.
- Stable FastAPI interfaces and clear boundaries.
- Examples: location, trips, maintenance, driver/vehicle.

### Communication & Data
- FastAPI for APIs and service-to-service calls.  
- RabbitMQ for async, decoupled events between modules.  
- MongoDB for operational data and histories.

### Frontend
- React + Tailwind for a crisp, responsive UI.  
- Leaflet for live maps, positions, and routes.

### Deployment
- Dockerized services with Compose for local orchestration.  
- Environment-driven configuration and secrets.  
- Production can deploy modules independently.

---

## Notes:
- Issues are tracked in [GitHub Issues](https://github.com/COS301-SE-2025/SAMFMS/issues).
- Use the [Branching Strategy](docs/Demo3/Branching_Strategy.pdf) for PR flow and releases.

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
