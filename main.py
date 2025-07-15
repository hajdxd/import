import os
import zipfile
import shutil
from ftplib import FTP
from datetime import datetime
import time
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

MONTHS_POLISH = {
    "January": "Styczen",
    "February": "Luty",
    "March": "Marzec",
    "April": "Kwiecien",
    "May": "Maj",
    "June": "Czerwiec",
    "July": "Lipiec",
    "August": "Sierpien",
    "September": "Wrzesien",
    "October": "Pazdziernik",
    "November": "Listopad",
    "December": "Grudzien"
}

start_time = time.time()
readable_start_time = datetime.fromtimestamp(start_time).strftime('%H:%M:%S')
today = datetime.today().strftime('%b %d %Y')
now = datetime.now()
counter = 0

def create_new_log():
    log_filename = now.strftime("import_%Y-%m-%d_%H.%M.log")
    logs_dir = r"C:\import\logi"
    logs_daily_dir = r"C:\import"
    full_log_path = os.path.join(logs_daily_dir, log_filename)

    for handler in logging.root.handlers[:]:
        handler.close()
        logging.root.removeHandler(handler)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        filename=full_log_path,
        filemode="w",
    )
    logger = logging.getLogger()

    return logger, full_log_path, logs_dir, log_filename

def move_log_to_monthly_folder(logs_dir, log_filename, full_log_path):
    now = datetime.now()
    month_english = now.strftime("%B")
    month_polish = MONTHS_POLISH[month_english]
    month_folder_name = f"{month_polish} {now.strftime('%Y')}".upper()
    month_folder_path = os.path.join(logs_dir, month_folder_name)

    os.makedirs(month_folder_path, exist_ok=True)

    for handler in logging.root.handlers[:]:
        handler.close()
        logging.root.removeHandler(handler)

    destination_path = os.path.join(month_folder_path, log_filename)
    shutil.move(full_log_path, destination_path)


def send_email_notification(to_email, subject, message_body, attachment_path=None):
    try:
        sender_email = ""
        sender_password = ""
        smtp_server = ""
        smtp_port = 465
        attachment_filename = f"import_{today}.log"

        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = to_email
        message["Subject"] = subject

        message.attach(MIMEText(message_body, "plain"))

        with open(attachment_path, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition", f"attachment; filename={attachment_filename}"
            )
        message.attach(part)

        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_email.split(", "), message.as_string())

            logger.info("E-mail zostal wyslany pomyslnie!")
    except Exception as e:
        logger.info(f"Wystapil blad podczas wysylania e-maila {e}")

def file_date_change(ftp_date, txtc_file_path):
    year = str(datetime.today().year)
    modification_time =  datetime.strptime(f"{ftp_date} {year}", '%b %d %H:%M %Y').timestamp()
    os.utime(txtc_file_path, (modification_time, modification_time))

def parse_ftp_date(ftp_date_str):
    parts = ftp_date_str.split()
    year = str(datetime.today().year)
    if len(parts) == 3:
        if ':' in parts[2]:
            return f"{parts[0]} {parts[1]} {year}"
        else:
            return ftp_date_str
    else:
        return None
    
if __name__ == "__main__":
    
    logger, full_log_path, logs_dir, log_filename = create_new_log()

    brands = []
    ftp_servers = []
    file_types = []

    local_folder = r"C:\import\import_zipy"
    output_folder = r"C:\import\import_rozpakowane"
    logger.info("--------------------------" + today + "--------------------------")

    for i, brand_info in enumerate(brands):
        brand = brand_info['brand']
        ftp_server = ftp_servers[i]
        file_extension = file_types[i]['type']

        logger.info(f"Przetwarzenie dla brandu: {brand}")
        logger.info(f"Laczenie z serwerem...")

        ftp = FTP(ftp_server['host'])
        ftp.login(user=ftp_server['user'], passwd=ftp_server['passwd'])

        file_info = []

        retries = 3
        for attempt in range(retries):
            ftp.cwd(ftp_server['remote_folder'])
            ftp.retrlines('LIST', file_info.append)

            if not file_info:
                logger.info("Lista plikow jest pusta. Ponawiam probe...")
                time.sleep(10)
            else:
                break

        if not file_info:
            logger.info("Nie udalo sie pobrac listy plikow.")

        matching_files = []
        file_dates = []
        file_dates_iter = iter(file_dates)

        for line in file_info:
            parts = line.split()
            ftp_date_str = " ".join(parts[5:8])
            ftp_date = parse_ftp_date(ftp_date_str)
            if ftp_date is None:
                continue
            file_name = parts[-1].strip()
            if file_name.startswith("FA"):
                if ftp_date == today:  
                    matching_files.append(file_name)
                    file_dates.append(ftp_date_str)

        if not matching_files:
            logger.info(f"Nie znaleziono plikow dla brandu {brand} z dzisiejsza data na serwerze {ftp_server['host']}.")
        else:
            for file in matching_files:
                counter = counter + 1
                logger.info(f"Pobieranie pliku: {file}")
                logger.info(f"counter: {counter}")
                local_file = os.path.join(local_folder, file)
                with open(local_file, 'wb') as f:
                    ftp.retrbinary(f'RETR {file}', f.write)
                logger.info(f"Plik {file} pobrano jako {local_file}")

                # rozpakowywanie zipa
                if local_file.endswith('.zip'):
                    logger.info(f"Rozpakowywanie pliku: {local_file}")
                    with zipfile.ZipFile(local_file, 'r') as zip_ref:
                        zip_ref.extractall(output_folder)
                    logger.info(f"Plik {local_file} zostal rozpakowany do {output_folder}")
                    os.remove(local_file)
                    logger.info(f"Plik {local_file} zostal usuniety.")

                    #zmiana .txt
                    for extracted_file in os.listdir(output_folder):
                        if extracted_file.endswith('.txt'):
                            txt_file_path = os.path.join(output_folder, extracted_file)
                            txtc_file_path = os.path.splitext(txt_file_path)[0] + file_extension
                            if os.path.exists(txtc_file_path):
                                logger.info(f"Plik {txtc_file_path} juz istnieje, pomijam i usuwam.")
                                os.remove(txt_file_path)
                                counter -= 1
                                continue
                            os.rename(txt_file_path, txtc_file_path)
                            logger.info(f"Zmieniono nazwe pliku na {txtc_file_path}")

                            #zmiana daty
                            date = next(file_dates_iter)
                            file_date_change(date, txtc_file_path)
                            logger.info(f"Ustawiono date modyfikacji: {date} dla {txtc_file_path}")
                        
                            #przeniesienie pliku
                            shutil.move(txtc_file_path, os.path.join(output_folder, os.path.basename(txtc_file_path)))
                            logger.info(f"Plik {txtc_file_path} zostal przeniesiony do {output_folder}")
        ftp.quit()
        logger.info(f"Polaczenie z serwerem zostalo zamkniete.\n")
    logger.info("Import ukonczony.")

    end_time = time.time()
    readable_end_time = datetime.fromtimestamp(end_time).strftime('%H:%M:%S')
    execution_time = round(end_time - start_time, 2)
    to_email = ''

    send_email_notification(
        to_email=to_email,
        subject=f"Import Danych {today}",
        message_body=f"Import danych w dniu [{today}] został wykonany. W załączniku znajduje się plik z logami.\nIlość pobranych plików: {counter}\nCzas wykonania: {execution_time}s\nCzas rozpoczęcia: {readable_start_time}\nCzas zakończenia: {readable_end_time}",
        attachment_path=full_log_path
    )

    move_log_to_monthly_folder(logs_dir, log_filename, full_log_path)
