select (
    insert Person {
        name := <str>$name
    }
) {name};
