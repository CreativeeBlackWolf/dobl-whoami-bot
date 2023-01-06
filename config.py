import configparser


class Config:

    def __init__(self, filename: str):
        self.config = configparser.ConfigParser()
        self.config.read(filename)

        self.Bot = self.Bot(
            token=self.config.get('bot', 'token'),
            prefix=self.config.get('bot', 'prefix', fallback="."),
            admins=self.config.get('bot', 'admins', fallback=[])
        )

        self.Map = self.Map(
            path=self.config.get('map', 'path')
        )

    class Bot:
        def __init__(self, token: str, prefix: str, admins: list[str]):
            self.token: str = token
            self.prefix: str = prefix
            self.admins: list[str] = admins

            if not self.token:
                raise ValueError("Token must be specified in configuration file.")

    class Map:
        def __init__(self, path: str):
            self.path: str = path

            if not self.path:
                raise ValueError("Path must be specified in configuration file.")
