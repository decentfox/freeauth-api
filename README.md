<img src="logo.png"/>

<p>
    <em>Make authentication and authorization easy and free.</em>
</p>

## Documentation

 * [English](https://freeauth.decentfox.com/)
 * [简体中文](https://zh.freeauth.decentfox.com/)

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

Note: Instance name must follow the pattern defined by the regular expression: `^[a-zA-Z_0-9]+(-[a-zA-Z_0-9]+)*$`.

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

You could overwrite mail-related settings in the `.env` file, which includes:

 - MAIL_FROM_NAME: default `FreeAuth`
 - MAIL_FROM: default `None`
 - MAIL_USERNAME: default `None`
 - MAIL_PASSWORD: default `None`
 - MAIL_PORT: default `25`
 - MAIL_SERVER: default `localhost`
 - MAIL_STARTTLS: default `False`
 - MAIL_SSL_TLS: default `False`

Each is explained in https://sabuhish.github.io/fastapi-mail/getting-started/#connectionconfig-class

### Configuring SMS settings

We support the following SMS providers:

 - [Aliyun](https://cn.aliyun.com/product/sms)
 - [Tencent Cloud](https://cloud.tencent.com/document/product/382)

You could overwrite SMS-related settings in the `.env` file, which includes:

 - SMS_PROVIDER: default `None`, the name of the SMS provider, which can be `tencent-cloud` or `aliyun`.
 - SMS_SECRET_ID: default `None`
 - SMS_SECRET_KEY: default `None`
 - SMS_REGION: default `None`, for `tencent-cloud` only, the region where TencentCloud SMS service is located, see [available regions](https://cloud.tencent.com/document/api/382/52071#.E5.9C.B0.E5.9F.9F.E5.88.97.E8.A1.A8).
 - SMS_APP_ID: default `None`, for `tencent-cloud` only, the `SDKAppID` after adding an application in the TencentCloud console.
 - SMS_AUTH_CODE_TPL_ID: default `None`, the template code for auth code.

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
