// Turn an API error into a sentence the user understands.
export function apiErrorMessage(error, fallback = "Something went wrong. Please try again.") {
  if (!error.response) return "Cannot reach the server. Is the backend running (python run.py)?";
  return error.response.data?.error || fallback;
}
