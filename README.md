# FreeAuth API

## Development

### Setup environment

1. Install the EdgeDB CLI:

```bash
curl https://sh.edgedb.com --proto '=https' -sSf1 | sh
```

2. Initialize the database:

```bash
edgedb project init
```

3. Create a virtual environment and install the development dependencies:

```bash
make install
```

### DB Migrations

1. Create a migration:

```bash
edgedb migration create
```

2. Apply migrations:

```bash
edgedb migrate
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
