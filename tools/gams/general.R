save_rdf <- function(data, file_path) {
  save(data, file=file_path)
}

get_warnings <- function() {
  return(warnings())
}

load_object <- function(path, var_name) {
  load(path)

  return(get(var_name))
}

save_object <- function(obj, file_path) {
  save(obj, file = file_path)
}

save_wrapper <- function(func, file_path, ...) {
  ret <- func(...)
  save_object(ret, file_path = file_path)

  return(ret)
}