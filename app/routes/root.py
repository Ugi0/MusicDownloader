from app.routes import app, log_request

@app.route('/', methods=["GET"])
@log_request
def root_get():
    return "Not allowed", 418