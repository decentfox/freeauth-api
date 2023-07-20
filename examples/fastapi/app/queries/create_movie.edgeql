select (
    insert Movie {
        title := <str>$title,
        director := assert_single((
            select Person
            filter .name = <str>$director_name
        ))
    }
) {title, director: {name}};
