const hostname = "localhost:8000";

export const API_URL = `http://${hostname}/api`;

export const API = {
  login: `${API_URL}/login`,
  logout: `${API_URL}/logout`,
  user: `${API_URL}/user`,
  users: `${API_URL}/users`,
  groups: `${API_URL}/groups`,
  group: (groupId: string) => `${API_URL}/groups/${groupId}`,
  groupUsers: (groupId: string) => `${API_URL}/groups/${groupId}/users`,
  groupAddUser: (groupId: string) => `${API_URL}/groups/${groupId}/add_user`,
};

export const signup = async (
  fullname: string,
  email: string,
  password: string,
  confirmPassword: string
): Promise<Response | Error> => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) {
    throw new Error("Invalid email format");
  }

  if (password !== confirmPassword) {
    throw new Error("Passwords do not match");
  }

  const response = await fetch(`${API_URL}/signup`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      fullname,
      email,
      password
    }),
  });

  return response;
};

export const login = async (
    email: string,
    password: string
  ): Promise<Response | Error> => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      throw new Error("Invalid email format");
    }
  
    const response = await fetch(`${API_URL}/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        email,
        password,
      }),
    });
  
    return response;
  };