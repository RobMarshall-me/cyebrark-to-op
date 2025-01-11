# CyberArk to 1Password Migration Script

This Python script migrates your secrets from a CyberArk Privileged Cloud account to a 1Password account. It leverages the CyberArk API and the 1Password CLI to perform the following actions:

1.  **Authentication:** Authenticates with the CyberArk API using a dedicated application user.
2.  **Safe Discovery:** Retrieves a list of all safes within your CyberArk Privileged Cloud instance.
3.  **Account Discovery:** Retrieves all accounts within each discovered CyberArk safe.
4.  **Vault Creation:** Creates a corresponding vault in your 1Password account for each CyberArk safe, using the same name.
5.  **Item Creation:** Creates new login items within the appropriate 1Password vault for each CyberArk account. Account details like username, password, address, and platformId are transferred.

## Prerequisites

Before running the script, make sure you have the following:

*   **Python 3:** This script is written in Python 3. Make sure you have it installed on your system.
*   **Poetry:** This project uses Poetry for dependency management and packaging. Install it following the instructions on the [official Poetry website](https://python-poetry.org/docs/#installation).
*   **1Password CLI (`op`):** Download and install the 1Password CLI from the official 1Password website. Ensure it's added to your system's `PATH` so you can run `op` commands from the terminal.
*   **CyberArk Privileged Cloud Account:**
    *   **Application User:** Create a dedicated application user in CyberArk with appropriate permissions to access the required safes and accounts.
    *   **Application ID:** Note down the application ID for your application.
    *   **Authentication Safe:** A designated safe to store the application user's credentials.
    *   **User Credentials:** The username and object name of the application user within the authentication safe.
*   **1Password Account:**
    *   **Service Account:** You'll need a 1Password service account token for authentication. You can create one in your 1Password account settings.

## Installation and Configuration with Poetry

1.  **Clone the Repository:**

    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```

2.  **Install Dependencies:**

    ```bash
    poetry install
    ```

3.  **Configuration (using `pyproject.toml` and environment variables):**

    *   **`pyproject.toml`:** This file manages project metadata and dependencies. It also serves as a place to store non-sensitive configuration. The `[tool.ca2op]` section is used for this purpose:
        *   `cyberark_base_url` (e.g., `https://your-cyberark-instance.privilegecloud.cyberark.com`)
        *   `onepassword_cli_path` (Usually just `op`, or the full path to the executable if necessary)
    *   **Environment Variables:** Sensitive information like API keys, and tokens are managed through environment variables.

    **Configure `pyproject.toml`:**

    Open `pyproject.toml` and update the `[tool.ca2op]` section with your CyberArk instance URL and the path to your 1Password CLI:

    ```toml
    [tool.ca2op]
    cyberark_base_url = "[https://your-cyberark-instance.privilegecloud.cyberark.com](https://your-cyberark-instance.privilegecloud.cyberark.com)"
    onepassword_cli_path = "op" # Or the full path if 'op' is not in your PATH
    ```

    **Set Environment Variables:**

    Set the following environment variables in your shell or a `.env` file (if you choose to use one. If you do, you'll need to add `python-dotenv` as a dependency using `poetry add python-dotenv`):

    ```bash
    export CYBERARK_APP_ID="your-app-id"
    export CYBERARK_SAFE="your-authentication-safe"
    export CYBERARK_USER="your-app-user"
    export CYBERARK_USER_OBJECT="your-app-user-object"
    export ONEPASSWORD_SERVICE_ACCOUNT_TOKEN="your-1password-service-account-token"
    ```

    **Important Security Note:** Never commit sensitive credentials like `CYBERARK_APP_ID`, `CYBERARK_USER`, and `ONEPASSWORD_SERVICE_ACCOUNT_TOKEN` to your version control system (e.g., Git). Use environment variables or other secure methods to manage them.

## Usage

1.  Activate the Poetry virtual environment:

    ```bash
    poetry shell
    ```

2.  Run the script from the root of the repository:

    ```bash
    python app/main.py
    ```

The script will output its progress to the console, indicating which safes and accounts are being processed and whether the corresponding vaults and items are created in 1Password.

## Error Handling

The script includes basic error handling to catch issues like network problems, authentication failures, and API errors. If an error occurs, the script will print an error message to the console and attempt to continue with the next safe or account.

## Security Considerations

*   **HTTPS:** The script uses `verify=True` in all `requests` calls to enforce secure HTTPS connections and validate SSL certificates.
*   **Sensitive Data:** Handle your CyberArk credentials and 1Password service account token with extreme care. Use environment variables instead of hardcoding them in the script or `pyproject.toml`.
*   **Least Privilege:** Ensure the CyberArk application user has only the necessary permissions to access the required safes and accounts. Follow the principle of least privilege.
*   **Code Review:** Before running the script in a production environment, thoroughly review the code to ensure its security and correctness.
*   **1Password CLI:** Consider using a dedicated service account to create the vaults and items via the 1Password Connect API instead of the CLI for enhanced security and efficiency.

## Disclaimer

This script is provided as a sample and should be thoroughly tested and adapted to your specific environment and security requirements. The author is not responsible for any issues or damages that may arise from the use of this script. Use it at your own risk.

## Contributing

If you find any bugs or want to improve the script, feel free to submit issues or pull requests on the repository. Your contributions are welcome!