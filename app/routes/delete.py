import os
from app.routes import app, login_required, log_request

@app.route('/delete/<filename>')
@login_required
@log_request
def delete_file(filename: str):
    if os.path.exists(f'/app/storage/{filename}'):
        os.remove(f'/app/storage/{filename}')
        return "File deleted", 200
    else:
        return "File does not exist", 404