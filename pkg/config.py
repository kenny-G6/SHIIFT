class GeneralConfig(object):

    SECRET_KEY="OJm5LZz2Rk1tYw"
    TECH_SUPPORT="090344559900"

class LiveConfig(GeneralConfig):
    SECRET_KEY="live-nB8N2P1-epu-lg"
    ADMIN_EMAIL="live@admin.com"
    SQLALCHEMY_DATABASE_URI='mysql+mysqlconnector://root@localhost/shiiftdb'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    COMMISSION_RATE = 0.15

class Testconfig(GeneralConfig):
    ADMIN_EMAIL="Test@admin.com"

