# Running the React App in Docker

Follow these steps to run this app inside a Docker container:

1. **Build the Docker image**

   Open a terminal in this directory and run:

   ```powershell
   docker build -t my-react-app .
   ```

2. **Run the Docker container**

   ```powershell
   docker run -p 3000:3000 my-react-app
   ```

3. **Access the app**

   Open your browser and go to [http://localhost:3000](http://localhost:3000)

---

If you want to run the app locally without Docker:

1. Install dependencies:
   ```powershell
   npm install
   ```
2. Start the app:
   ```powershell
   npm start
   ```

The app will be available at [http://localhost:3000](http://localhost:3000)
