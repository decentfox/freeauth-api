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

3. Set environment variables

Add `export EDGEDB_INSTANCE=FreeAuth` to the end of `.venv/bin/activate` file.

4. Initial FreeAuth DB

```bash
source .venv/bin/activate
poetry run freeauth-db install
```

### Run FreeAuth admin server

1. Active venv

```bash
poetry shell
```

2. Run FreeAuth admin server in dev mode

```bash
make dev
```

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
