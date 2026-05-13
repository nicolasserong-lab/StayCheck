from datetime import datetime
from app.extensions import db
import json

class Execution(db.Model):
    __tablename__ = 'executions'
    
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, nullable=False)
    checklist_id = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    
    # Nuevo: Para que el Admin vea solo sus reportes
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    status = db.Column(db.String(20), default="Iniciado")
    observations = db.Column(db.Text)
    fecha = db.Column(db.String(10), default=lambda: datetime.now().strftime("%Y-%m-%d"))
    hora = db.Column(db.String(8), default=lambda: datetime.now().strftime("%H:%M:%S"))
    hora_fin = db.Column(db.String(8))
    _responses = db.Column('responses', db.Text)

    @property
    def responses(self):
        if self._responses:
            return json.loads(self._responses)
        return {}

    @responses.setter
    def responses(self, value):
        self._responses = json.dumps(value)

def get_all_executions_by_admin(admin_id):
    return Execution.query.filter_by(admin_id=admin_id).all()

def get_execution_by_id(exec_id):
    return Execution.query.get(int(exec_id))

def add_execution(property_id, checklist_id, user_id, admin_id):
    execution = Execution(
        property_id=int(property_id),
        checklist_id=int(checklist_id),
        user_id=int(user_id),
        admin_id=int(admin_id)
    )
    db.session.add(execution)
    db.session.commit()
    return execution

def save_execution_responses(exec_id, responses, observations, status="Completado"):
    execution = Execution.query.get(int(exec_id))
    if execution:
        execution.responses = responses
        execution.observations = observations
        execution.status = status
        execution.hora_fin = datetime.now().strftime("%H:%M:%S")
        db.session.commit()
        return True
    return False
