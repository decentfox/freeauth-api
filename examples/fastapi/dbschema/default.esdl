module default {
    type Movie {
        required title: str;
        required director: Person;
    }

    type Person {
        required name: str;
    }
}
