export interface User {
  id: string;
  email: string;
  full_name: string;
  role: "admin" | "member" | "viewer";
  organization_id: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}
