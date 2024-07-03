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

The provided script is a synchronization service for LDAP and Matrix Synapse. Here's a high-level description of how the code functions:

### 1. **Configuration Loading**
- The script starts by importing necessary libraries.
- It then loads sensitive data (like LDAP and Matrix server details) from a `config.ini` file using the `ConfigParser` library.

### 2. **Logging Setup**
- Logging is configured to write logs to a file (`ldap2synapse.log`) with daily rotation and to the console.
- Two handlers are set up: one for writing to the log file and another for printing to stdout.

### 3. **Helper Functions**

#### `display_synapse_err(response)`
- Logs errors returned by the Synapse server.

#### `fetch_ldap_data()`
- Connects to the LDAP server and retrieves user data based on a specified filter.
- Extracts relevant user attributes and stores them in a dictionary.
```sh
The following attributes are fetched:
- "sAMAccountName" the base of login of a matrix user;
- "displayName" first name and surname of the user defined in AD;
- "userAccountControl" value defines if the user account is disabled or not;
- "memberOf" checks if the created Synapse user should be an administrator or not: if the user
in AD is a member of  "Domain Admins" AND "Administrators" groups it will
be an administrator on Synapse server as well.
```
#### `fetch_access_token()`
- Retrieves an access token for the Matrix Synapse server.
- Registers the core administrator account if it is not already registered.
- Refetches the token if it has expired.

#### `register_user(id, displayname, password, admin)`
- Registers a user on the Matrix Synapse server using a HMAC-based authentication mechanism.

#### `generate_mac(nonce, user, password, admin)`
- Generates a HMAC signature for user registration.

#### `fetch_registered_users(access_token)`
- Retrieves a list of users registered on the Matrix Synapse server.

#### `delete_user(user_id, access_token)`
- Deletes user data and deactivates the user on the Matrix Synapse server.

#### `update_user_data(user_id, update_payload, access_token)`
- Updates user attributes on the Matrix Synapse server.

#### `load_deleted_users(deleted_users_list)`
- Loads a list of deleted users from a file.

#### `save_deleted_users(deleted_users_list, deleted_users)`
- Saves the list of deleted users to a file.

#### `compare_and_update(ldap_users_data, registered_users, access_token)`
- Compares LDAP users with registered Matrix users.
- Updates user attributes or deletes users as necessary.

#### `register_unregistered(ldap_users_data, registered_users)`
- Registers users that exist in LDAP but not on the Matrix server.

### 4. **Main Function**

#### `main()`
- Orchestrates the synchronization process:
  1. Retrieves an access token.
  2. Fetches registered users from the Matrix server.
  3. Fetches user data from LDAP.
  4. Registers any unregistered users.
  5. Compares and updates user data.

### 5. **Continuous Synchronization**

- The script runs in an infinite loop, invoking the `main()` function and then sleeping for a specified period before the next synchronization cycle.

This setup ensures that the Matrix Synapse server is kept in sync with the LDAP directory, reflecting changes in user accounts, whether they are additions, updates, or deletions. The logging mechanism provides detailed insights into the synchronization process and helps in troubleshooting any issues that arise.

## Docker Setup

To run the synchronization service in a Docker container, follow these steps:

1. Modify the `config.ini` to match your enviroment.
2. Create or modify existing `docker-compose.yml` file to define the service:
    ```yaml
    version: '3'

    services:
        ldap2synapse:
          container_name: ldap2synapse
          hostname: ldap2synapse
          restart: unless-stopped
          image: ex0lis/ldap2synapse
          volumes:
            - ./ldap2synapse/config.ini:/ldap2synapse/config.ini
            - ./ldap2synapse/logs:/ldap2synapse/logs
           # Remove comment if you wish to view deleted users list
           #- ./ldap2synapse/deleted_users_list:/ldap2synapse/deleted_users_list
            - /etc/localtime:/etc/localtime
         # Recommended to set the dependency on the health status of Synapse instance
         # (also should be configured in the Synapse service itself) 
         # depends_on:
         #   synapse:
         #     condition: service_healthy
    ```

3. Run the Docker container using Docker Compose:
    ```
    docker compose up -d
    ```

This will start the synchronization service in a Docker container.
To stop the service use the following command:
    ```
    docker compose down
    ```
## Contribution

Contributions are welcome! If you have any ideas, suggestions, or improvements, feel free to open an issue or submit a pull request. Please ensure that your contributions align with the project's coding standards and guidelines.

## License

This project is licensed under the GPL-3.0 License. See the `LICENSE` file for more details.

## Contact

For any questions or support, please open an issue on this repository or contact the maintainer at thunderofsky245@gmail.com.

---

Thank you for using ldap2synapse! I hope this tool helps streamline your user management processes and enhances your overall experience with Matrix Synapse and LDAP.
