# Bank of Med 💰 🏦

### Welcome to the Bank of Med, a straightforward banking application 🌇

## Features
💁  Account creation, login, and logout functionalities

📓  Deposit, withdrawal, and transaction logging capabilities
 
💻  An intuitive web UI for data input

## Behind the Scenes
The application utilizes the following packages and tools:
- **FastAPI**: Connects the backend and frontend components
  
- **HTML/CSS**: Constructs the dashboard and website interface
  
- **MySQL**: Stores user data
  
- **Session Cookies**: Remembers users, eliminating the need for constant logins
  
- **Logging**: Tracks user actions

## Getting Started
You can run the application in two ways: by setting it up manually or by using a pre-built Docker image. The latter is recommended for convenience, but both methods are available.

## Method One: Manual Setup

### Prerequisites
**Packages to Install**: FastAPI, datetime, logging, pymysql.cursors, uvicorn

### Setting Up MySQL
When configuring the MySQL database, ensure the settings match your local environment. Here’s an example configuration:

```python
connection = pymysql.connect(
    host='localhost',
    user='aj',
    password='abc',
    database='practice',
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)
```
Replace the host, user, password, and database variables with your own MySQL database configurations. 


### Running the Code
Execute the following command in your terminal to launch the application:

```shell
uvicorn main:app --reload
```

The app should then be accessible in your browser.

## Method Two: Using Docker

Using Docker simplifies the setup process by bundling all required packages and code into a single image, eliminating the need for manual installation and configuration.

### Pull the Docker Image
The Docker image for this application is available on Docker Hub. To download it, run:

```shell
docker pull jam777/bankofmed:latest
```

### Run the Docker Container
After pulling the image, start the application with the following command:

```shell
docker run -d -p 8000:8000 -e HOST=host_name -e USER=username -e PASSWORD=password -e DATABASE=database jam777/bankofmed:latest
```

And that’s all there is to it!
