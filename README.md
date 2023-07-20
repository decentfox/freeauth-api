# freeAuth-api

## Development

### Setup environment

Install the EdgeDB CLI (required EdgeDB 3.0+), prep environment, install dependencies, and initial project:

```bash
make setup
```

During the first installation, you will enter an interactive session to initialize the EdgeDB project:

```bash
Specify the name of EdgeDB instance to use with this project [default: FreeAuth]: 
> FreeAuth
```

If you already have a FreeAuth instance in your local environment, you can choose to use the same FreeAuth instance in your project:

```bash
Do you want to use existing instance "FreeAuth" for the project? [y/n]
> y
```

### Run FreeAuth admin server in dev mode

```bash
make dev
```

### Configuring mail settings

After executing the `make setup` command, you will have a `.env` file under `freeauth-admin` folder.

You could override mail settings in the `.env` file, there are the available options:

 - MAIL_FROM_NAME: default `FreeAuth`
 - MAIL_FROM: default `None`
 - MAIL_USERNAME: default `None`
 - MAIL_PASSWORD: default `None`
 - MAIL_PORT: default `25`
 - MAIL_SERVER: default `localhost`
 - MAIL_STARTTLS: default `False`
 - MAIL_SSL_TLS: default `False`

Each is explained in https://sabuhish.github.io/fastapi-mail/getting-started/#connectionconfig-class

### Open the EdgeDB UI

```bash
edgedb ui
```

### Automatic API documents

 - Swagger UI: http://localhost:5001/docs
 - ReDoc: http://localhost:5001/redoc

### DB Migrations

1. Create a migration:

```bash
make db
```

2. Apply migrations:

```bash
make up
```

### Generate query APIs

```bash
make genqlapi
```

### Format and lint the code

Execute the following command to apply formatting:

```bash
make lint
```

### Run unit tests

Run all the tests with:

```bash
make test
```

Reset test DB before running tests (if any schema changes):

```bash
make testdb
```
