import gspread
from oauth2client.service_account import ServiceAccountCredentials

def init_google_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("qr-absen-432515-2f8433091f26.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open("Data-SidangMD").sheet1 
    return sheet

def save_to_google_sheets(sheet, data):
    for entry in data:
        sheet.append_row(entry)

def get_data_from_google_sheets(sheet):
    data = sheet.get_all_records()
    return data

def all_posisi(sheet):
    data = sheet.get_all_records()
    position_counts = {}
    
    for record in data:
        posisi = record['Posisi']
        if posisi in position_counts:
            position_counts[posisi] += 1
        else:
            position_counts[posisi] = 1
    
    return position_counts
