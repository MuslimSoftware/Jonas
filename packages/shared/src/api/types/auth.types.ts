// REQUEST TYPES
interface BaseRequest {
  signal?: AbortSignal;
}

export interface OTPRequest extends BaseRequest {
  email: string;
}

export interface ValidateOTPRequest extends BaseRequest {
  email: string;
  otp: string;
}

export interface AuthRequest extends BaseRequest {
  token: string;
}

export interface RefreshTokenRequest extends BaseRequest {
  refreshToken: string;
}

// RESPONSE TYPES
export interface RequestOTPResponse {
  expires_in: number;
}

export interface ValidateOTPResponse {
  token: string; // Should this contain both access and refresh tokens?
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
} 