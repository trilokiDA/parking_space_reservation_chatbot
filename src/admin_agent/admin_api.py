"""REST API for admin-agent communication."""
import logging
from typing import Optional
from flask import Flask, request, jsonify
from flask_cors import CORS
from threading import Thread
from .admin_agent import AdminAgent

logger = logging.getLogger(__name__)


class AdminAPI:
    """Flask REST API for admin communication."""

    def __init__(self, admin_agent: AdminAgent, host: str = "127.0.0.1", port: int = 5000):
        """Initialize the admin API.

        Args:
            admin_agent: AdminAgent instance
            host: API host
            port: API port
        """
        self.admin_agent = admin_agent
        self.host = host
        self.port = port
        self.app = Flask(__name__)
        CORS(self.app)  # Enable CORS for frontend access
        self._setup_routes()
        self.server_thread = None

    def _setup_routes(self):
        """Setup API routes."""

        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Health check endpoint."""
            return jsonify({"status": "healthy", "service": "admin-api"}), 200

        @self.app.route('/api/reservations/pending', methods=['GET'])
        def get_pending_reservations():
            """Get all pending reservation requests."""
            try:
                result = self.admin_agent.get_pending_requests()
                return jsonify({
                    "success": True,
                    "data": result,
                    "count": len(self.admin_agent.pending_requests)
                }), 200
            except Exception as e:
                logger.error(f"Error getting pending reservations: {e}")
                return jsonify({"success": False, "error": str(e)}), 500

        @self.app.route('/api/reservations/<int:reservation_id>', methods=['GET'])
        def get_reservation_details(reservation_id: int):
            """Get details of a specific reservation."""
            try:
                details = self.admin_agent.get_request_details(reservation_id)
                status = self.admin_agent.get_reservation_status(reservation_id)
                return jsonify({
                    "success": True,
                    "details": details,
                    "status": status
                }), 200
            except Exception as e:
                logger.error(f"Error getting reservation {reservation_id}: {e}")
                return jsonify({"success": False, "error": str(e)}), 500

        @self.app.route('/api/reservations/<int:reservation_id>/decide', methods=['POST'])
        def make_decision(reservation_id: int):
            """Admin decision on a reservation (approve/reject).

            Expected JSON body:
            {
                "decision": "approved" or "rejected",
                "notes": "optional admin notes"
            }
            """
            try:
                data = request.get_json()
                decision = data.get('decision')
                notes = data.get('notes', '')

                if not decision:
                    return jsonify({
                        "success": False,
                        "error": "Decision field is required"
                    }), 400

                result = self.admin_agent.process_admin_decision(
                    reservation_id=reservation_id,
                    decision=decision,
                    admin_notes=notes
                )

                if result.get('success'):
                    return jsonify(result), 200
                else:
                    return jsonify(result), 400

            except Exception as e:
                logger.error(f"Error processing decision for {reservation_id}: {e}")
                return jsonify({"success": False, "error": str(e)}), 500

        @self.app.route('/api/reservations/submit', methods=['POST'])
        def submit_reservation():
            """Submit a new reservation request from chatbot.

            Expected JSON body:
            {
                "reservation_id": 1,
                "first_name": "John",
                "last_name": "Doe",
                "car_number": "ABC123",
                "start_time": "2024-12-25 14:00",
                "end_time": "2024-12-25 18:00"
            }
            """
            try:
                data = request.get_json()
                reservation_id = data.get('reservation_id')

                if not reservation_id:
                    return jsonify({
                        "success": False,
                        "error": "reservation_id is required"
                    }), 400

                success = self.admin_agent.add_pending_request(
                    reservation_id=reservation_id,
                    request_data=data
                )

                if success:
                    return jsonify({
                        "success": True,
                        "message": f"Reservation {reservation_id} submitted for admin approval",
                        "reservation_id": reservation_id
                    }), 201
                else:
                    return jsonify({
                        "success": False,
                        "error": "Failed to submit reservation"
                    }), 500

            except Exception as e:
                logger.error(f"Error submitting reservation: {e}")
                return jsonify({"success": False, "error": str(e)}), 500

        @self.app.route('/api/admin/query', methods=['POST'])
        def admin_query():
            """Process admin natural language query.

            Expected JSON body:
            {
                "query": "Show me pending requests"
            }
            """
            try:
                data = request.get_json()
                query = data.get('query')

                if not query:
                    return jsonify({
                        "success": False,
                        "error": "Query field is required"
                    }), 400

                response = self.admin_agent.query_admin(query)

                return jsonify({
                    "success": True,
                    "response": response
                }), 200

            except Exception as e:
                logger.error(f"Error processing admin query: {e}")
                return jsonify({"success": False, "error": str(e)}), 500

        @self.app.route('/api/reservations/<int:reservation_id>/status', methods=['GET'])
        def check_status(reservation_id: int):
            """Check the status of a reservation request."""
            try:
                status = self.admin_agent.get_reservation_status(reservation_id)

                if status:
                    return jsonify({
                        "success": True,
                        "status": status
                    }), 200
                else:
                    return jsonify({
                        "success": False,
                        "error": f"Reservation {reservation_id} not found"
                    }), 404

            except Exception as e:
                logger.error(f"Error checking status for {reservation_id}: {e}")
                return jsonify({"success": False, "error": str(e)}), 500

    def start(self, threaded: bool = True):
        """Start the Flask API server.

        Args:
            threaded: Whether to run in a separate thread
        """
        if threaded:
            self.server_thread = Thread(
                target=self._run_server,
                daemon=True
            )
            self.server_thread.start()
            logger.info(f"Admin API started on http://{self.host}:{self.port} (threaded)")
        else:
            self._run_server()

    def _run_server(self):
        """Run the Flask server."""
        try:
            self.app.run(
                host=self.host,
                port=self.port,
                debug=False,
                use_reloader=False
            )
        except Exception as e:
            logger.error(f"Error running server: {e}")

    def stop(self):
        """Stop the API server."""
        # Flask doesn't have a built-in stop method
        # In production, use a proper WSGI server like Gunicorn
        logger.info("API server stopping...")
