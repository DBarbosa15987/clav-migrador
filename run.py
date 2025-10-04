from webapp.app import app
from datetime import datetime
import os
import logging
from utils.path_utils import DUMP_DIR, LOG_DIR, FILES_DIR, UPLOAD_DIR, OUTPUT_DIR, ONTOLOGY_DIR

# Criação das diretorias caso não existam
os.makedirs(DUMP_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(FILES_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(ONTOLOGY_DIR, exist_ok=True)

now = datetime.now()
dateFormat = "%Y-%m-%d_%H-%M-%S"
timestamp = now.strftime(dateFormat)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d | %(name)s | %(levelname)s | %(message)s",
    datefmt='%Y-%m-%d %H:%M:%S',
    filename=os.path.join(LOG_DIR, f"clav_{timestamp}.log"),
    filemode="w",
)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
