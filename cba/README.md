Clamping Business Administration by One Media Asia Co, Ltd

This is a Flask application designed for managing a clamping business. It provides a user-friendly interface for inputting and managing clamping data, including customer information and clamp details.

## Project Structure

```
clamping-business-admin
├── app.py                # Main entry point of the Flask application
├── config.py             # Configuration settings for the application
├── requirements.txt      # List of dependencies required for the project
├── static
│   ├── css
│   │   └── style.css     # CSS styles for the application
│   └── images
│       └── background.jpg # Background image for the web pages
├── templates
│   ├── base.html         # Base HTML template for the application
│   ├── dashboard.html    # Dashboard displaying business operations
│   ├── clamp_form.html   # Form for inputting clamping business data
│   └── clamp_list.html   # List of all clamping entries
└── README.md             # Documentation for the project
```

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd clamping-business-admin
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Configure the application settings in `config.py` as needed.

## Usage

1. Run the application:
   ```
   python app.py
   ```

2. Open your web browser and navigate to `http://127.0.0.1:5000` to access the application.

## Features

- Input form for clamping business data
- Dashboard for an overview of business operations
- List view for managing clamping entries

## Contributing

Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## SECRET_KEY and rotating secrets

The application uses Flask sessions which require a `SECRET_KEY`. By default `app.py` will read the `SECRET_KEY` environment variable. If it is not set, the application will generate a secure runtime-only fallback key. That fallback is convenient for local development but will change on every restart and should NOT be used in production.

To set a persistent secret (recommended):

1. Generate a secure secret locally. Example using Python:

```bash
python - <<'PY'
import secrets
print(secrets.token_urlsafe(48))
PY
```

2. Export the secret as an environment variable before starting the app:

```bash
export SECRET_KEY="<paste-generated-secret-here>"
python app.py
```

3. To rotate the secret safely (invalidate all existing sessions):

- Stop the app.
- Generate a new secret using the command above.
- Update the `SECRET_KEY` env var and start the app.
- Inform users that they will need to log in again, since session cookies signed with the old key will no longer be valid.

Keep the secret value private and avoid committing it to source control.
