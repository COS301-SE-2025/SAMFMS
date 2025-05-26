# 🚀 Firewall Five

## Project Information
**Firewall Five - SAMFMS - Modular Fleet Management System**  

---

## 📚 Documentation  
| Resource | Link |
|----------|------|
| 📄 SRS Document | [Requirements](srs-link) |
| 📊 Project Board | [Project Board](link-to-project-board)

---

## 👥 Meet the Team 
Here’s our awesome team behind **Firewall Five**:

<table>
  <thead>
    <tr>
      <th style="font-size: 20px; font-family: 'Verdana', sans-serif;">📸 Profile</th>
      <th style="font-size: 20px; font-family: 'Verdana', sans-serif;">👾 GitHub</th>
      <th style="font-size: 20px; font-family: 'Verdana', sans-serif;">🧑 Name</th>
      <th style="font-size: 20px; font-family: 'Verdana', sans-serif;">🎓 Student Number</th>
        <th style="font-size: 20px; font-family: 'Verdana', sans-serif;">🧑‍💻LinkedIn</th>
      <th style="font-size: 20px; font-family: 'Verdana', sans-serif;">📄Description</th>

  </tr>
  </thead>
  <tbody>
    <tr>
      <td><img src="https://github.com/StefanJvRCodes.png" width="80"></td>
      <td><a href="https://github.com/StefanJvRCodes" style="font-size: 18px;">@StefanJvRCodes</a></td>
      <td style="font-size: 18px;">Mr. Stefan Jansen van Rensburg</td>
      <td style="font-size: 18px;">u22550055</td>
      <td><a href="https://linkedin.com/in/stefan-JvR" style="font-size: 18px;">@Stefan Jansen van Rensburg</a></td>
      <td style="font-size: 18px;"><strong>Team lead/ Project manager.</strong>, management of <strong>CI\CD</strong> , Worked on <strong>Daemon.</strong> // Features: storage, CRUD operations, reading and writing files, server creation and user management</td>
    </tr>
  </tbody>
</table>

---

## Repository Information
### Git Structure
- **Mono Repo**: Our code for all of our projects or features is kept within a single repository. This keeps all our features centralised and improves the ability for integration amoungst the subsystems.  
- **Branching Strategy**: [Branching strategy](https://github.com/COS301-SE-2025/SAMFMS/blob/docs/docs/Branching_Strategy.pdf)

### Git Management
- **Linting** : Usage of linting to complete our CI/CD pipeline and maintain the quality of our code. This reduced the number of bugs and kept our coding standards up to date. Can be seen in the following file: [Linting](linting link)

### Issue Tracking
- Managed via [GitHub Issues](https://github.com/COS301-SE-2025/SAMFMS/issues).

---
## 🛠️ Project Features
### 💻 **Technologies Used**:
[![Leaflet](https://img.shields.io/badge/Leaflet-199900?style=for-the-badge&logo=leaflet&logoColor=white)](https://leafletjs.com/)
[![RabbitMQ](https://img.shields.io/badge/RabbitMQ-FF6600?style=for-the-badge&logo=rabbitmq&logoColor=white)](https://www.rabbitmq.com/)
[![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)](https://reactjs.org/)
[![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-4DB33D?style=for-the-badge&logo=mongodb&logoColor=white)](https://www.mongodb.com/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)



**Key Components**:  

  1. **🔧 MCORE**  
   - Manages NoSQL database operations, storage, and real-time events  
   - Implements all CRUD operations  
   - Directly interacts with the storage system (reading/writing files)

2. **🌐 SBlocks**  
   - Exposes endpoints for CRUD operations, authentication, and event subscriptions

3. **🖼️ UI**  
   - Web-based interface for visual database management
