# ldap2synapse: Matrix Synapse Server and LDAP Users Synchronization Service

## Overview

**ldap2synapse** is a synchronization service designed to integrate user accounts from an LDAP directory into a Matrix Synapse server. This project was created to address the lack of existing solutions for integrating the Matrix protocol into organizations that use Active Directory (AD).

## Important Notice

This code is provided **as-is** and is not optimized for performance. It was not written by a professional programmer but was generated using ChatGPT. While it aims to fulfill its primary function, it may not follow best coding practices and might require adjustments for specific use cases or environments.

## Features

- **Automated Synchronization:** Sync user accounts from your LDAP directory to the Matrix Synapse server.
- **Customizable Mapping:** Basic configuration options to map LDAP attributes to Matrix Synapse user attributes.
- **Batch Sync:** Schedule periodic batch synchronization to ensure consistency without constant monitoring.
- **Logging:** Basic logging and monitoring for synchronization processes to help with troubleshooting.

## Requirements

- **Matrix Synapse Server:** A running instance of the Matrix Synapse server.
- **LDAP Directory:** Access to an LDAP directory with user account information.
- **Docker:** To run the synchronization service in a containerized environment.

## Docker Setup

To run the synchronization service in a Docker container, follow these steps:

1. Create or modify existing `docker-compose.yml` file to define the service:
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

2. Build and run the Docker container using Docker Compose:
    ```sh
    docker-compose up --build
    ```

This will start the synchronization service in a Docker container, exposing it on port 8080.

## Contribution

Contributions are welcome! If you have any ideas, suggestions, or improvements, feel free to open an issue or submit a pull request. Please ensure that your contributions align with the project's coding standards and guidelines.

## License

This project is licensed under the GPL-3.0 License. See the `LICENSE` file for more details.

## Contact

For any questions or support, please open an issue on this repository or contact the maintainer at thunderofsky245@gmail.com.

---

Thank you for using ldap2synapse! I hope this tool helps streamline your user management processes and enhances your overall experience with Matrix Synapse and LDAP.
