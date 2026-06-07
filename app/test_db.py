try:
    from app.database import engine
except ModuleNotFoundError:
    from database import engine


def run_connection_check() -> None:
    try:
        connection = engine.connect()
        print("Database Connected Successfully!")
        connection.close()

    except Exception as e:
        print("Connection Failed!")
        print(e)


if __name__ == "__main__":
    run_connection_check()
