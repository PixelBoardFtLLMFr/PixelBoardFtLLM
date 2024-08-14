# Shorthand for debugging json_string_to_json_array when called from
# sanitize_eye.
define eye_str_to_arr
  break sanitize_eye
  break json_string_to_json_array
  disable 2
  break strip_json_array_string
  disable 3
end

# Local Variables:
# mode: gdb-script
# End:
