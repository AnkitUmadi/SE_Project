import { createContext, useContext } from "react";

// Lets any page show a short message, e.g. toast("Student added").
export const ToastContext = createContext(() => {});

export function useToast() {
  return useContext(ToastContext);
}

// Turn an API error into a sentence for the user.
export function apiErrorMessage(error, fallback = "Something went wrong. Please try again.") {
  if (!error || !error.response) return "Cannot reach the server. Is the backend running?";
  return error.response.data?.error || fallback;
}
