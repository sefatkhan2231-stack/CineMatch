import { Clapperboard, Eye, EyeOff, LoaderCircle } from "lucide-react";
import { useState } from "react";
import { authApi, removeAccessToken, saveAccessToken } from "../services/api";

function Auth({ onLogin }) {
  const [mode, setMode] = useState("login");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const isRegister = mode === "register";

  function switchMode(nextMode) {
    setMode(nextMode);
    setError("");
    setSuccess("");
    setPassword("");
  }

  async function handleSubmit(event) {
    event.preventDefault();

    setError("");
    setSuccess("");

    if (password.length < 8) {
      setError("Password must contain at least 8 characters.");
      return;
    }

    setLoading(true);

    try {
      if (isRegister) {
        await authApi.register({
          username: username.trim(),
          email: email.trim(),
          password,
        });

        setSuccess("Account created successfully. You can now sign in.");
        setMode("login");
        setPassword("");
      } else {
        const data = await authApi.login({
          email: email.trim(),
          password,
        });

        saveAccessToken(data.access_token);

        const user = await authApi.me();

        onLogin(user);
      }
    } catch (err) {
      setError(err.message || "Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  if (!isRegister) {
    removeAccessToken();
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-brand">
          <span className="brand-icon">
            <Clapperboard size={25} />
          </span>
          <span>
            CINE<span className="brand-accent">MATCH</span>
          </span>
        </div>

        <div className="auth-heading">
          <span className="section-kicker">
            {isRegister ? "JOIN CINEMATCH" : "WELCOME BACK"}
          </span>

          <h1>
            {isRegister ? "Create your account." : "Your next favorite awaits."}
          </h1>

          <p>
            {isRegister
              ? "Create an account and start discovering movies."
              : "Sign in to explore your movie universe."}
          </p>
        </div>

        <div className="auth-tabs">
          <button
            type="button"
            className={!isRegister ? "active" : ""}
            onClick={() => switchMode("login")}
          >
            Login
          </button>

          <button
            type="button"
            className={isRegister ? "active" : ""}
            onClick={() => switchMode("register")}
          >
            Register
          </button>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          {isRegister && (
            <div className="auth-field">
              <label htmlFor="auth-username">Username</label>
              <input
                id="auth-username"
                type="text"
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                placeholder="Choose a username"
                minLength={3}
                maxLength={50}
                autoComplete="username"
                required
              />
            </div>
          )}

          <div className="auth-field">
            <label htmlFor="auth-email">Email address</label>
            <input
              id="auth-email"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="you@example.com"
              autoComplete="email"
              required
            />
          </div>

          <div className="auth-field">
            <label htmlFor="auth-password">Password</label>

            <div className="password-input">
              <input
                id="auth-password"
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="Enter your password"
                minLength={8}
                maxLength={128}
                autoComplete={isRegister ? "new-password" : "current-password"}
                required
              />

              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>

          {error && <div className="auth-message error">{error}</div>}

          {success && <div className="auth-message success">{success}</div>}

          <button className="auth-submit" type="submit" disabled={loading}>
            {loading ? (
              <>
                <LoaderCircle className="spinner" size={18} />
                Please wait...
              </>
            ) : isRegister ? (
              "Create account"
            ) : (
              "Sign in"
            )}
          </button>
        </form>

        <p className="auth-switch">
          {isRegister ? "Already have an account?" : "New to CineMatch?"}{" "}
          <button
            type="button"
            onClick={() => switchMode(isRegister ? "login" : "register")}
          >
            {isRegister ? "Sign in" : "Create account"}
          </button>
        </p>
      </div>
    </div>
  );
}

export default Auth;
