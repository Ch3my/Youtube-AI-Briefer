from datetime import datetime

def log_message(message):
    """
    Writes a timestamped message to log.txt, creating the file if it doesn't exist.
    
    Args:
    message (str): The message to be logged.
    """
    log_file = 'log.txt'
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"{timestamp} - {message}\n"
   
    # Open the file in append mode, creating it if it doesn't exist
    with open(log_file, 'a') as file:
        file.write(log_entry)
