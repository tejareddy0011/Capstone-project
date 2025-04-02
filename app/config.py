# config.py
import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = 'fjalruweoruweoriueorwoflweyroi'  # replace with your own key
    SQLALCHEMY_DATABASE_URI = 'sqlite:///job_portal.sqlite'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
