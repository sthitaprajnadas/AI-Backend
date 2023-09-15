import crypt
import enum
import json
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class ModelType(enum.Enum):
    Regression = "regression"
    Classification = "classification"

class InsightType(enum.Enum):
    Report = "report"
    Data_Band = "data_band"
    Model_Band = "model_band"
    Variable_Ranking = "variable_ranking"
    Confusion_Matrix = "confusion_matrix"
    Correlation_Matrix = "correlation_matrix"
    Misclassification_Matrix = "misclassification_matrix"

class InsightSource(enum.Enum):
    td_cm = "td_cm"
    sd_cm = "sd_cm"
    td = "td"
    bias = "bias"

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))
    auth_token = db.Column(db.String(1000))

    def __init__(self, id, name, auth_token):
        self.id = id
        self.name = name
        self.auth_toke = auth_token

    @classmethod
    def seed(cls, fake):
        customer = Customer(
            name = fake.name(),
            auth_token = cls.encrypt_password(fake.password()),
        )
        customer.save()

    @staticmethod
    def encrypt_password(password):
        return crypt.generate_password_hash(password).decode('utf-8')

    def save(self):
        db.session.add(self)
        db.session.commit()

class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    permissions = db.Column(db.Text)
    name = db.Column(db.String(1000))

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    name = db.Column(db.String(1000))

class Model(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
    name = db.Column(db.String(1000))
    type = db.Column(db.Enum(ModelType))

class Version(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    model_id = db.Column(db.Integer, db.ForeignKey('model.id'))
    number = db.Column(db.String(100))
    timestamp = db.Column(db.TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    def get_insights(self):
        insights = Insights.query.filter_by(version_id=self.id).all()
        insights_data = [{
            'type': insight.type.value,
            'source': insight.source.value,
            'value': json.loads(insight.value)
        } for insight in insights]
        return insights_data


class Insights(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    version_id = db.Column(db.Integer, db.ForeignKey('version.id'))
    type = db.Column(db.Enum(InsightType))
    source = db.Column(db.Enum(InsightSource))
    value = db.Column(db.Text)
# Model	id	Customer_id	Name	Type (Classification/Regression)

class Feature(db.Model):
    __tablename__ = 'features'

    id = db.Column(db.Integer, primary_key=True)
    version_id = db.Column(db.Integer, db.ForeignKey('versions.id'))
    name = db.Column(db.String(255))
    type = db.Column(db.String(255))
    metadata_json = db.Column(db.JSON)

    def __init__(self, version_id, name, type, metadata_json):
        self.version_id = version_id
        self.name = name
        self.type = type
        self.metadata_json = metadata_json