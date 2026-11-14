import { ROLES } from "./constants";

export const getHomePath = (role) => {
  switch (role) {
    case ROLES.CUSTOMER:
      return "/restaurants";
    case ROLES.OWNER:
      return "/owner/dashboard";
    case ROLES.DELIVERY:
      return "/delivery/dashboard";
    default:
      return "/login";
  }
};
