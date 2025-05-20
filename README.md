# 🚀 Firewall Five

## Project Information
**Firewall Five - SAMFMS - Modular Fleet Management System**  

---

## 📚 Documentation  
| Resource | Link |
|----------|------|
| 📹 Demo Video | [Databox-Demo1](https://drive.google.com/file/d/1uH5wLZUVsM41YY3ZPp_KuF7n9DoipgCw/view?usp=sharing) |
| 📄 SRS Document | [Requirements](https://github.com/COS301-SE-2025/MP1/blob/dev/Documentation/Requirements/Requirements.md) |
| 🎨 Design Specs | [Design Specs](https://github.com/COS301-SE-2025/MP1/blob/dev/Documentation/Requirements/Design_Specifications.md) |
| 📊 Project Board | [CLI](https://github.com/orgs/COS301-SE-2025/projects/25/views/2)

---

## 👥 Meet the Team 
Here’s our awesome team behind **Databox**:

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
- **Branching Strategy**: Feature Branch Workflow. Using a dev branch in which all our subsytems lie and are ready to be merged into main. The dev branch then consists of 5 feature branches : The Daemon, CLI, UI, API and JS Client libray. Off of each of these branches are another set of features branches that relate to their 5 main feature branches. These new features branches are where mirco features are built and merged back into their main feature branch.

### Git Management
- **Linting** : Usage of linting to complete our CI/CD pipeline and maintain the quality of our code. This reduced the number of bugs and kept our coding standards up to date. Can be seen in the following file: [Linting](https://github.com/COS301-SE-2025/MP1/blob/main/.github/workflows/super-linter.yml)

### Issue Tracking
- Managed via [GitHub Issues](https://github.com/COS301-SE-2025/SAMFMS/issues).

---
## 🛠️ Project Features
### 💻 **Technologies Used**:
![NodeJS](https://img.shields.io/badge/node.js-6DA55F?style=for-the-badge&logo=node.js&logoColor=white)
![HTML5](https://img.shields.io/badge/html5-%23E34F26.svg?style=for-the-badge&logo=html5&logoColor=white)
![Java](https://img.shields.io/badge/java-%23ED8B00.svg?style=for-the-badge&logo=openjdk&logoColor=white)
![JavaScript](https://img.shields.io/badge/javascript-%23323330.svg?style=for-the-badge&logo=javascript&logoColor=%23F7DF1E)
![Swagger](https://img.shields.io/badge/Swagger-0C4B8E?style=for-the-badge&logo=swagger&logoColor=white)
![React](https://img.shields.io/badge/react-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![Express.js](https://img.shields.io/badge/express.js-%23404d59.svg?style=for-the-badge&logo=express&logoColor=%2361DAFB)
![CSS3](https://img.shields.io/badge/css3-%231572B6.svg?style=for-the-badge&logo=css3&logoColor=white)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)
![YAML](https://img.shields.io/badge/yaml-%23ffffff.svg?style=for-the-badge&logo=yaml&logoColor=151515)

**Key Components**:  

  1. **🔧 MCORE**  
   - Manages NoSQL database operations, storage, and real-time events  
   - Implements all CRUD operations  
   - Directly interacts with the storage system (reading/writing files)

2. **🌐 SBlocks**  
   - Exposes endpoints for CRUD operations, authentication, and event subscriptions

3. **🖼️ UI**  
   - Web-based interface for visual database management
