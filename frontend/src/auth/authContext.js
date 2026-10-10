import { createContext, useContext } from "react";

// Shared "who is logged in" information, readable from any page with useAuth().
export const AuthContext = createContext(null);

export function useAuth() {
  return useContext(AuthContext);
}

// Each role's home page.
export const HOME_BY_ROLE = {
  admin: "/admin",
  faculty: "/faculty",
  student: "/student",
};
