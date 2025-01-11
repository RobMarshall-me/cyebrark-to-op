import os
import json
import subprocess
import requests

# Configuration - Replace with your actual values
CYBERARK_BASE_URL = "https://your-cyberark-instance.privilegecloud.cyberark.com"
CYBERARK_APP_ID = "your-app-id"
CYBERARK_SAFE = "your-authentication-safe"  # Safe where the app user creds are stored
CYBERARK_USER = "your-app-user"
CYBERARK_USER_OBJECT = "your-app-user-object"

ONEPASSWORD_SERVICE_ACCOUNT_TOKEN = "your-1password-service-account-token"
ONEPASSWORD_CLI_PATH = "op"  # Ensure the 1Password CLI is in your PATH or provide the full path


def get_cyberark_session():
    """Authenticates with CyberArk and returns a session token."""
    url = f"{CYBERARK_BASE_URL}/PasswordVault/API/auth/Cyberark/Logon"
    headers = {"Content-Type": "application/json"}
    payload = {
        "username": CYBERARK_USER,
        "password": get_cyberark_password(),
        "application": CYBERARK_APP_ID
    }
    try:
        response = requests.post(url, headers=headers, json=payload, verify=True) # verify=True is important for security
        response.raise_for_status()
        return response.text  # CyberArk returns the token directly as text
    except requests.exceptions.RequestException as e:
        print(f"Error authenticating with CyberArk: {e}")
        exit(1)
    
def get_cyberark_password():
    """Retrieves the password for the CyberArk user from the specified safe."""
    url = f"{CYBERARK_BASE_URL}/PasswordVault/api/Accounts?AppID={CYBERARK_APP_ID}&Safe={CYBERARK_SAFE}&Object={CYBERARK_USER_OBJECT}"
    headers = {"Content-Type": "application/json"}
    
    try:
        # Logon to get a session token first
        logon_url = f"{CYBERARK_BASE_URL}/PasswordVault/API/auth/Cyberark/Logon"
        logon_payload = {
            "username": CYBERARK_USER,
            "password": "",  # We don't have the password yet, but it's not needed for this specific logon
            "application": CYBERARK_APP_ID
        }
        response = requests.post(logon_url, headers=headers, json=logon_payload, verify=True)
        response.raise_for_status()
        session_token = response.text

        # Use the session token to get the app user password
        headers["Authorization"] = session_token
        response = requests.get(url, headers=headers, verify=True)
        response.raise_for_status()
        password = response.json()['value'][0]['properties']['password']

        # Logoff after retrieving the password
        logoff_url = f"{CYBERARK_BASE_URL}/PasswordVault/API/auth/Cyberark/Logoff"
        requests.post(logoff_url, headers=headers, verify=True)

        return password

    except requests.exceptions.RequestException as e:
        print(f"Error retrieving CyberArk password: {e}")
        exit(1)

def get_cyberark_safes(session):
    """Retrieves a list of safes from CyberArk."""
    url = f"{CYBERARK_BASE_URL}/PasswordVault/WebServices/PIMServices.svc/Safes"
    headers = {
        "Authorization": session,
        "Content-Type": "application/json"
    }
    try:
        response = requests.get(url, headers=headers, verify=True)
        response.raise_for_status()
        safes = response.json()["SafesList"]
        return safes
    except requests.exceptions.RequestException as e:
        print(f"Error retrieving safes from CyberArk: {e}")
        return []


def get_cyberark_accounts(session, safe_name):
    """Retrieves a list of accounts within a given safe."""
    url = f"{CYBERARK_BASE_URL}/PasswordVault/api/Accounts?safe={safe_name}"
    headers = {
        "Authorization": session,
        "Content-Type": "application/json"
    }
    try:
        response = requests.get(url, headers=headers, verify=True)
        response.raise_for_status()
        accounts = response.json()["value"]
        return accounts
    except requests.exceptions.RequestException as e:
        print(f"Error retrieving accounts from safe '{safe_name}': {e}")
        return []


def create_onepassword_vault(safe_name):
    """Creates a 1Password vault using the 1Password CLI."""
    try:
        # Sign in using service account token
        subprocess.run([ONEPASSWORD_CLI_PATH, "signin", "--account", "my", "--raw"], input=ONEPASSWORD_SERVICE_ACCOUNT_TOKEN.encode(), check=True)
        # Create the vault
        command = [
            ONEPASSWORD_CLI_PATH,
            "vault",
            "create",
            safe_name,
            "--format",
            "json",
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        vault_data = json.loads(result.stdout)
        return vault_data.get("id")
    except subprocess.CalledProcessError as e:
        print(f"Error creating 1Password vault '{safe_name}': {e.stderr}")
        return None
    except Exception as e:
        print(f"Error creating 1Password vault '{safe_name}': {e}")
        return None

def create_onepassword_item(vault_id, account, cyberark_session):
    """Creates a 1Password item based on a CyberArk account using the 1Password CLI via a service user."""

    try:
        # Sign in using service account token
        subprocess.run([ONEPASSWORD_CLI_PATH, "signin", "--account", "my", "--raw"], input=ONEPASSWORD_SERVICE_ACCOUNT_TOKEN.encode(), check=True)

        # Retrieve the password for the account using requests
        account_url = f"{CYBERARK_BASE_URL}/PasswordVault/api/Accounts/{account['id']}"
        headers = {
            "Authorization": cyberark_session,
            "Content-Type": "application/json"
        }
        response = requests.get(account_url, headers=headers, verify=True)
        response.raise_for_status()
        cyberark_password = response.json()['properties']['password']

        # Create a basic item
        item_data = {
            "title": account["name"],
            "category": "Login",
            "fields": [
                {
                    "id": "username",
                    "type": "STRING",
                    "purpose": "USERNAME",
                    "label": "username",
                    "value": account.get("userName", ""),
                },
                {
                    "id": "password",
                    "type": "CONCEALED",
                    "purpose": "PASSWORD",
                    "label": "password",
                    "value": cyberark_password,
                },
                {
                    "id": "address",
                    "type": "STRING",
                    "purpose": "NOTES",
                    "label": "address",
                    "value": account.get("address", ""),
                },
                {
                    "id": "platformId",
                    "type": "STRING",
                    "purpose": "NOTES",
                    "label": "platformId",
                    "value": account.get("platformId", ""),
                }
            ],
        }

        # Create the item using the op cli
        command = [
            ONEPASSWORD_CLI_PATH,
            "item",
            "create",
            "--vault",
            vault_id,
            json.dumps(item_data),
            "--format",
            "json"
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        print(f"Created 1Password item '{account['name']}' in vault '{vault_id}'")

    except subprocess.CalledProcessError as e:
        print(f"Error creating 1Password item for account '{account['name']}' in vault '{vault_id}': {e.stderr}")
    except requests.exceptions.RequestException as e:
        print(f"Error retrieving password for CyberArk account '{account['name']}': {e}")
    except Exception as e:
        print(f"Error creating 1Password item for account '{account['name']}' in vault '{vault_id}': {e}")

if __name__ == "__main__":
    cyberark_session = get_cyberark_session()
    cyberark_safes = get_cyberark_safes(cyberark_session)

    if cyberark_safes:
        print("Processing CyberArk safes and accounts...")
        for safe in cyberark_safes:
            safe_name = safe["safeName"]
            print(f"\nProcessing safe: {safe_name}")

            # Create 1Password vault
            vault_id = create_onepassword_vault(safe_name)

            if vault_id:
                print(f"Created 1Password vault: {safe_name} (ID: {vault_id})")

                # Get accounts from CyberArk safe
                cyberark_accounts = get_cyberark_accounts(cyberark_session, safe_name)
                
                if cyberark_accounts:
                    print(f"Found {len(cyberark_accounts)} accounts in safe '{safe_name}'.")
                    for account in cyberark_accounts:
                        create_onepassword_item(vault_id, account, cyberark_session)

                else:
                    print(f"No accounts found in safe '{safe_name}'.")
            else:
                print(f"Skipping safe '{safe_name}' due to vault creation error.")
    else:
        print("No safes found in CyberArk.")

    print("\nProcess completed.")