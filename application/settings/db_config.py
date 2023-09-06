from application.shared.secrets import secrets
from sqlalchemy import create_engine


def init_connection_engine():
    engine = create_engine(
        f'mysql+pymysql://{secrets["db_user"]}:{secrets["db_pass"]}@{secrets["db_host"]}:{secrets["db_port"]}/{secrets["db_name"]}'
    )

    return engine
