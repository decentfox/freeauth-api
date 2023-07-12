# FreeAuth Admin FastAPI http server

## Development

### Setup environment

1. Install the EdgeDB CLI:

refer to https://www.edgedb.com/docs/intro/cli

#### Linux or macOS

```bash
curl https://sh.edgedb.com --proto '=https' -sSf1 | sh
```

2. Create a virtual environment and install the development dependencies:

```bash
make install
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

### Setup administrator account

```bash
poetry run freeauth-db admin setup
```

### Open the EdgeDB UI

```bash
edgedb ui -I FreeAuth
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
