import os
from chalice import Chalice, Response, CORSConfig
from chalicelib.core.database import create_db_and_tables, get_session
from chalicelib.services.vehicle_service import VehicleService
from chalicelib.services.seed_service import SeedService

from chalicelib.routes.auth_routes import auth_bp
from chalicelib.routes.vehicle_routes import vehicle_bp
from chalicelib.routes.alert_routes import alert_bp
from chalicelib.routes.trip_routes import trip_bp

app = Chalice(app_name="fms-backend")
app.debug = True

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(vehicle_bp)
app.register_blueprint(alert_bp)
app.register_blueprint(trip_bp)

@app.route("/", methods=["GET"], cors=True)
def index():
    return {"message": "FMS API is running."}

from chalicelib.services.auth_service import AuthService


def bootstrap():
    create_db_and_tables()
    with get_session() as session:
        AuthService.seed_test_users(session)
        VehicleService.seed_demo_vehicles_if_empty(session)
        SeedService.seed_all(session)


bootstrap()
