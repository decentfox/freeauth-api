delete freeauth::Application
filter .id in array_unpack(<array<uuid>>$ids) and not .is_protected
