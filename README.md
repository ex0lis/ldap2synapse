# ldap2synapse
Matrix Synapse server and LDAP users synchronization service.

## Overview

Welcome to **ldap2synapse**, a synchronization service designed to integrate user accounts from an LDAP directory into a Matrix Synapse server. This project was created to address the lack of existing solutions for integrating the Matrix protocol into organizations that use Active Directory (AD).

## Important Notice

This code is provided **as-is** and is not optimized for performance. It was not written by a professional programmer but was generated using ChatGPT. While it aims to fulfill its primary function, it may not follow best coding practices and might require adjustments for specific use cases or environments.

## Features

- **Automated Synchronization:** Sync user accounts from your LDAP directory to the Matrix Synapse server.
- **Customizable Mapping:** Basic configuration options to map LDAP attributes to Matrix Synapse user attributes.
- **Batch Sync:** Schedule periodic batch synchronization to ensure consistency without constant monitoring.
- **Detailed Logging:** Basic logging and monitoring for synchronization processes to help with troubleshooting.
- **Secure Communication:** Secure data transfer using encrypted protocols to protect sensitive user information.

## Requirements

- **Matrix Synapse Server:** A running instance of the Matrix Synapse server.
- **LDAP Directory:** Access to an LDAP directory with user account information.
- **Docker:** To run the synchronization service in a containerized environment.
- **Python 3.x:** The synchronization service is implemented in Python and requires Python 3.x to run.
- **Dependencies:** Additional Python libraries specified in the `requirements.txt` file.

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/your-username/ldap2synapse.git
    cd ldap2synapse
    ```

2. Install dependencies:
    ```sh
    pip install -r requirements.txt
    ```

3. Configure the synchronization service by editing the `config.yaml` file to include your LDAP and Matrix Synapse server details.

## Docker Setup

To run the synchronization service in a Docker container, follow these steps:

1. Create a `Dockerfile` in the root directory of your project:
    ```dockerfile
    # Use an official Python runtime as a parent image
    FROM python:3.9-slim

    # Set the working directory in the container
    WORKDIR /usr/src/app

    # Copy the current directory contents into the container at /usr/src/app
    COPY . .

    # Install any needed packages specified in requirements.txt
    RUN pip install --no-cache-dir -r requirements.txt

    # Make port 80 available to the world outside this container
    EXPOSE 80

    # Define environment variable
    ENV NAME ldap2synapse

    # Run sync_service.py when the container launches
    CMD ["python", "sync_service.py"]
    ```

2. Create a `docker-compose.yml` file to define the services:
    ```yaml
    version: '3.8'

    services:
      ldap2synapse:
        build: .
        container_name: ldap2synapse
        volumes:
          - .:/usr/src/app
        environment:
          - PYTHONUNBUFFERED=1
        ports:
          - "8080:80"
    ```

3. Build and run the Docker container using Docker Compose:
    ```sh
    docker-compose up --build
    ```

This will start the synchronization service in a Docker container, exposing it on port 8080.

## Contribution

Contributions are welcome! If you have any ideas, suggestions, or improvements, feel free to open an issue or submit a pull request. Please ensure that your contributions align with the project's coding standards and guidelines.

## License

This project is licensed under the GPL-3.0 License. See the `LICENSE` file for more details.

## Contact

For any questions or support, please open an issue on this repository or contact the maintainer at [your-email@example.com](mailto:your-email@example.com).

---

Thank you for using ldap2synapse! We hope this tool helps streamline your user management processes and enhances your overall experience with Matrix Synapse and LDAP.
