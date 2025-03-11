import os
import pandas as pd
from qrcode import constants, QRCode

def cm_to_pixels(cm, dpi=300):
    return int((cm / 2.54) * dpi)

def create_qr_code(data, filename, output_dir, target_size_cm=2.61):
    qr = QRCode(
        version=1,
        error_correction=constants.ERROR_CORRECT_L,
        box_size=10,  
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill='black', back_color='white')
    
    filepath = os.path.join(output_dir, filename)
    img.save(filepath)
    print(f"QR Code saved as {filepath}")

output_dir = 'qr_codes'
os.makedirs(output_dir, exist_ok=True)

# enter your company's employee data (Name and Job)
df = pd.read_excel('data.xlsx')

for index, row in df.iterrows():
    # Edit your name row
    name = row['Nama']
    position = row['Posisi']
    data = f"{name}; {position}"
    filename = f"{name.replace(' ', '_')}.png"
    create_qr_code(data, filename, output_dir)

print("All QR Codes have been created.")