import ldap3
import requests
import hmac
import hashlib
import time
import sys
from datetime import date
import logging
from logging.handlers import TimedRotatingFileHandler
from configparser import ConfigParser

# Load sensitive data from config.ini
config = ConfigParser()
config.read('./config.ini')

# Get values from the config file
ldap_server = config.get('LDAP', 'ldap_server')
ldap_base_dn = config.get('LDAP', 'ldap_base_dn')
ldap_user = config.get('LDAP', 'ldap_user')
ldap_filter = config.get('LDAP', 'ldap_filter')
ldap_password = config.get('LDAP', 'ldap_password')

matrix_shared_secret = config.get('Matrix', 'matrix_shared_secret')
matrix_core_admin = config.get('Matrix', 'matrix_core_admin')
matrix_server = config.get('Matrix', 'matrix_server')
matrix_domain = config.get('Matrix', 'matrix_domain')

sync_period = int(config.get('Main', 'sync_period'))

# Local variables list
deleted_users_list = "deleted_users_list"  # Deleted users list file location; defaults to directory from where the script was launched
token_needs_refresh = True  # Flag to track if access token should be refreshed or not
core_admin_registered = False  # Flag to track if core administrator account was registered or not
access_token = None  # Initiate access token variable
hour_word = "hour." if sync_period == 1 else "hours."

# Define log file name pattern
log_file = './logs/ldap2synapse.log'

# Define a log file writing via TimedRotatingFileHandler with daily rotation
logfile_handler = TimedRotatingFileHandler(log_file, when="midnight", interval=1, backupCount=20)  # Rotate logs daily, keep 20 days worth of logs
logfile_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%d-%m-%Y %H:%M:%S'))  # Set time format for the events

# Define a StreamHandler for stdout
stream_handler = logging.StreamHandler(sys.stdout)  # Define StreamHandler for stdout log output
stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%d-%m-%Y %H:%M:%S'))  # Set time format for the events

# Create a logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(logfile_handler)
logger.addHandler(stream_handler)

def display_synapse_err(response):
    try:
        logger.error(f"Error from Synapse server: {response.json().get('error')}")
        return response.json().get('error')
    except Exception as e:
        logger.error(f"Failed to display Synapse server error: {str(e)}")

def fetch_ldap_data():
    try:
        server = ldap3.Server(ldap_server)
        with ldap3.Connection(server, user=ldap_user, password=ldap_password, auto_bind=True) as conn:
            if not conn:
                raise Exception("Unable to establish connection with LDAP server.")
            # Filter for selecting users
            filter_str = ldap_filter
            attributes = ["sAMAccountName", "displayName", "userAccountControl", "memberOf"]

            conn.search(search_base=ldap_base_dn, search_filter=filter_str, search_scope=ldap3.SUBTREE, attributes=attributes)

            users_data = {}

            for entry in conn.entries:
                sAMAccountName = entry.sAMAccountName.value.lower()
                displayName = entry.displayName.value
                userAccountControl = entry.userAccountControl.value
                memberOf = entry.memberOf.values

                admin = True if f'CN=Domain Admins,CN=Users,{ldap_base_dn}' in memberOf and f'CN=Administrators,CN=Builtin,{ldap_base_dn}' in memberOf else False
                deactivated = True if userAccountControl & 2 == 2 else False

                users_data[sAMAccountName] = {'displayname': displayName, 'admin': admin, 'deactivated': deactivated}

        logging.info("LDAP user data has been successfully retrieved.")
        return users_data
    except Exception as e:
        logging.error(f"Failed to retrieve user data from LDAP: {str(e)}")
        return {}

def fetch_access_token():
    try:
        global core_admin_registered, access_token, token_needs_refresh
        if access_token and token_needs_refresh == False:
            logging.info("A previously retrieved valid access token is being reused.")
            return access_token
        elif token_needs_refresh is True:
            logging.info("Access token has expired; attempting to refetch access token.")
        if core_admin_registered is False:
            logging.info("Attempting to register the core administrator.")
            counter = 0
            while counter < 10:
                result = register_user(matrix_core_admin, matrix_core_admin, '', True)
                if result == 200:
                    core_admin_registered = True
                    break
                elif result == "M_USER_IN_USE":
                    core_admin_registered = True
                    break
                else:
                    logging.error("Failed to register core administrator account; retrying.")
                    counter += 1
                    time.sleep(6)  # Sleep for 6 seconds before retrying.
            if counter == 10:
                raise Exception("Unable to register core administrator account; aborting execution.")
        access_token = None
        while not access_token:
            response = requests.post(f"{matrix_server}/_matrix/client/v3/login",
                json={
                    "identifier": {
                        "type": "m.id.user",
                        "user": matrix_core_admin
                    },
                    "initial_device_display_name": "Synapse Server Internal",
                    "password": ldap_password,
                    "type": "m.login.password"
                    })
            response_json = response.json()
            if "access_token" in response_json:
                access_token = response_json["access_token"]
                token_needs_refresh = False
                logging.info("The access token has been successfully retrieved.")
                return access_token
            else:
                logging.error("The attempt to retrieve the access token has failed. Retrying...")
                display_synapse_err(response)
                time.sleep(10)
    except Exception as e:
        logging.error(f"The attempt to fetch the access token has failed: {str(e)}")
        return None

def register_user(id, displayname, password, admin):
    try:
        response = requests.get(f"{matrix_server}/_synapse/admin/v1/register")
        response_json = response.json()
        nonce = response_json.get("nonce")
        if nonce:
            mac = generate_mac(nonce, id, password, admin)
            register_data = {
                "nonce": nonce,
                "username": id,
                "displayname": displayname,
                "password": password,
                "admin": admin,
                "mac": mac
            }
            response = requests.post(f"{matrix_server}/_synapse/admin/v1/register", json=register_data)
            if response.status_code == 200:
                logging.info(f"User '{id}' was registered successfully.")
                return response.status_code
            else:
                logging.error(f"Failed to register user '{id}'.")
                error_message = (response.json()).get("errcode")
                if error_message == "M_USER_IN_USE" and id == matrix_core_admin:
                    logging.warning("Core administrator account is registered already.")
                    return error_message
                else:
                    return error_message
        else:
            logging.error("Failed to retrieve a nonce for registration.")
    except Exception as e:
        logging.error(f"Failed to register user '{id}': {str(e)}")

def generate_mac(nonce, user, password, admin):
    try:
        mac = hmac.new(
        key=matrix_shared_secret.encode('utf8'),
        digestmod=hashlib.sha1,
        )
        mac.update(nonce.encode('utf8'))
        mac.update(b"\x00")
        mac.update(user.encode('utf-8'))
        mac.update(b"\x00")
        mac.update(password.encode('utf-8'))
        mac.update(b"\x00")
        mac.update(b"admin" if admin else b"notadmin")

        if mac:
            return mac.hexdigest()
    except Exception as e:
        logging.error(f"Failed to generate user HMAC: {str(e)}")

def fetch_registered_users(access_token):
    try:
        registered_users = {}
        next_token = None
        while True:
            params = {"from": next_token, "limit": 100, "guests": "false", "deactivated": "true"}
            response = requests.get(f"{matrix_server}/_synapse/admin/v2/users", headers={"Authorization": f"Bearer {access_token}"}, params=params)
            response_json = response.json()
            if response_json.get("error") == "Access token has expired":
                global token_needs_refresh
                token_needs_refresh = True
                access_token = fetch_access_token()
                if not access_token:
                    logging.error("Failed to refetch the access token. Ending sync process.")
                    return None
                logging.info("Access token successfully refetched. Retrying fetch_registered_users.")
                continue
            elif "errcode" in response_json:
                logging.error(f"The attempt to retrieve registered users has failed.")
                display_synapse_err(response)
                break
            else:
                for user in response_json.get("users", []):
                    user_id = user["name"]
                    displayname = user.get("displayname", "")
                    admin = user.get("admin", False)
                    deactivated = user.get("deactivated", False)
                    registered_users[user_id] = {"displayname": displayname, "admin": admin, "deactivated": deactivated}
                next_token = response_json.get("next_token")
                if not next_token:
                    logging.info("All data for registered users has been successfully retrieved.")
                    return registered_users
    except Exception as e:
        logging.error(f"The attempt to retrieve registered users has failed: {str(e)}")

def delete_user(user_id, access_token):
    try:
        response = requests.delete(f"{matrix_server}/_synapse/admin/v1/users/{user_id}/media",
                                   headers={"Authorization": f"Bearer {access_token}"})
        if response.status_code == 200:
            logging.info(f"Media has been successfully deleted for the user: '{user_id}'")
        else:
            logging.error(f"The deletion of media for the user has failed: '{user_id}'")

        response = requests.post(f"{matrix_server}/_synapse/admin/v1/deactivate/{user_id}",
                                headers={"Authorization": f"Bearer {access_token}"},
                                json={"erase": True})
        if response.status_code == 200:
            logging.info(f"User '{user_id}' erased successfully.")
        else:
            logging.error(f"Failed to erase user '{user_id}'")
            display_synapse_err(response)
            
    except Exception as e:
        logging.error(f"Failed to delete user {user_id}: {str(e)}")

def update_user_data(user_id, update_payload, access_token):
    try:
        response = requests.put(f"{matrix_server}/_synapse/admin/v2/users/{user_id}",
                                headers={"Authorization": f"Bearer {access_token}"},
                                json=update_payload)
        if response.status_code == 200:
            logging.info(f"User data updated successfully for '{user_id}'.")
        else:
            logging.error(f"Failed to update data for user '{user_id}'.")
            display_synapse_err(response)
    except Exception as e:
        logging.error(f"Failed to update user data for '{user_id}': {str(e)}")

def load_deleted_users(deleted_users_list):
    try:
        with open(deleted_users_list, 'r') as file:
            deleted_users = set(line.strip() for line in file)
        return deleted_users
    except FileNotFoundError:
        return set()

def save_deleted_users(deleted_users_list, deleted_users):
    try:
        with open(deleted_users_list, 'w') as file:
            file.write('\n'.join(deleted_users))
    except FileNotFoundError:
        return set()
    finally:
        logging.info("Deleted users list was updated successfully.")

def compare_and_update(ldap_users_data, registered_users, access_token):
    try:
        attributes_updated = False  # Flag to indicate if there were any updates committed
        changes_made = False  # Flag to track changes made to deleted users list
        deleted_users = load_deleted_users(deleted_users_list)  # Loads the deleted users list
        for matrix_user_id, registered_user_data in registered_users.items():
            # Extract user_id from matrix_user_id
            user_id = matrix_user_id.split('@')[1].split(':')[0]
            if user_id in ldap_users_data:
                if matrix_user_id in deleted_users:
                    response = requests.post(f"{matrix_server}/_synapse/admin/v1/deactivate/{matrix_user_id}",
                                headers={"Authorization": f"Bearer {access_token}"},
                                json={})
                    if response.status_code == 200:
                        logging.info(f"User '{user_id}' account has been reactivated.")
                        deleted_users.remove(matrix_user_id)
                        changes_made = True
                    else:
                        logging.error(f"Failed to reactivate user '{user_id}' account.")
                        display_synapse_err(response)
                ldap_user_data = ldap_users_data[user_id]
                # Determine which attributes do not match
                mismatched_attributes = {key: ldap_user_data[key] for key in ldap_user_data.keys() if key in registered_user_data and ldap_user_data[key] != registered_user_data[key]}
                if mismatched_attributes:
                    # Update only mismatched attributes
                    update_user_data(matrix_user_id, mismatched_attributes, access_token)
                    attributes_updated = True
            elif matrix_user_id not in deleted_users:
                # Delete the user since it doesn't exist in LDAP data
                delete_user(matrix_user_id, access_token)
                deleted_users.add(matrix_user_id)
                changes_made = True
    except Exception as e:
        logging.error(f"An error occurred while comparing users and updating: {str(e)}")
    finally:
        # Save the deleted users list if changes were made
        if changes_made:
            save_deleted_users(deleted_users_list, deleted_users)
        if attributes_updated == False:
            logging.info("No changes to attributes; no updates required.")

def register_unregistered(ldap_users_data, registered_users):
    try:
        registered_ids = []
        for user_id, data in ldap_users_data.items():
            if f"@{user_id}:{matrix_domain}" not in registered_users:
                register_user(user_id, data["displayname"], '', data["admin"])
                registered_ids.append(user_id)
        return registered_ids
    except Exception as e:
        logging.error(f"An error occurred during registration of new users: {str(e)}")

def main():
    try:
        # Declaration of sync start
        logging.info("The synchronization process between LDAP and Synapse has been initiated.")

        # Step 1: Fetch admin access token
        access_token = fetch_access_token()
        if not access_token:
            raise Exception("No access token was retrieved; unable to proceed.")
        
        # Step 2: Fetch registered users
        registered_users = fetch_registered_users(access_token)
        if not registered_users:
            logging.info("No registered users were fetched.")

        # Step 3: Fetch LDAP users data
        ldap_users_data = fetch_ldap_data()
        if not ldap_users_data:
            raise Exception("Cannot retrieve LDAP users data; unable to proceed.")

        # Step 4: Register unregistered users
        if register_unregistered(ldap_users_data, registered_users):
            registered_users = fetch_registered_users(access_token)
        
        # Step 5: Compare and update user data
        compare_and_update(ldap_users_data, registered_users, access_token)
        
        # Declaration of sync end
        logging.info(f"The synchronization process between LDAP and Synapse has been finished; awaiting to resync in {sync_period} {hour_word}\n")
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        logging.warning(f"Waiting for the next synchronization process in {sync_period} {hour_word} to retry.\n")

if __name__ == "__main__":
    while True:
        main()  # Declaration of the script body
        time.sleep(sync_period * 3600)  # Wait until next sync is needed
