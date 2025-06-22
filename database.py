from sqlmodel import Session , create_engine , SQLModel

database_name = "Database.db"
database_url = f'sqlite:///{database_name}'

connect_args = {'check_same_threads':False}
engine = create_engine(database_url , connect_args=connect_args)

def create_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

