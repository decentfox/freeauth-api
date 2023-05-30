select (
    update Application filter .id = <uuid>$id set {
        hashed_secret := <str>$hashed_secret
    }
) { secret := .hashed_secret };
