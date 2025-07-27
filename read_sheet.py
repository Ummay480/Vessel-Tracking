import gspread
from google.oauth2.service_account import Credentials

# Path to your JSON key file
SERVICE_ACCOUNT_FILE = "credentials.json"

# Scope
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Authenticate
creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
client = gspread.authorize(creds)

# Open your spreadsheet by name
sheet = client.open("VesselSchedule").sheet1

# Read all records
records = sheet.get_all_records()

# Print data
for row in records:
    print(row)
