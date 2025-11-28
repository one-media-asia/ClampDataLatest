from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Clamp(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    clamp_type = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    date_ordered = db.Column(db.Date, nullable=False)

    def __repr__(self):
        return f'<Clamp {self.id} - {self.customer_name} - {self.clamp_type}>'