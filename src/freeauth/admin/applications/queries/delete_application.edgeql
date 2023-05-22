delete Application
filter .id in array_unpack(<array<uuid>>$ids) AND NOT .is_protected
