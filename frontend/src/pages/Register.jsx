import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { UserPlus, Loader2, AlertCircle, ShieldCheck, MailCheck } from "lucide-react";
import api from "../utils/api";

const Register = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [formData, setFormData] = useState({
    username: "",
    email: "",
    password: "",
    confirm_password: "",
  });
  const [step, setStep] = useState('form');
  const [otp, setOtp] = useState("");
  const [registeredEmail, setRegisteredEmail] = useState("");

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    // Minor validation before sending
    if (formData.password.length < 8) {
      setError("Password must be at least 8 characters long.");
      setLoading(false);
      return;
    }

    if (formData.password !== formData.confirm_password) {
      setError("Passwords do not match.");
      setLoading(false);
      return;
    }

    try {
      const response = await api.post("/auth/register", formData);
      if (response.data.status === "pending" || response.status === 201 || response.data.ok) {
         setRegisteredEmail(formData.email);
         setStep('otp');
         setError(null);
      }
    } catch (err) {
      if (err.response?.data?.detail) {
        const detail = err.response.data.detail;
        if (typeof detail === "string") {
          setError(detail);
        } else if (Array.isArray(detail)) {
          setError(detail.map((e) => e.msg).join(", "));
        }
      } else {
        setError("Network error. Could not connect to the server.");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await api.post("/auth/verify-email", {
        email: registeredEmail,
        otp: otp
      });
      if (response.data.ok) {
        // Verification success! Redirect to login
        navigate("/login", { state: { message: "Account verified! Please sign in." } });
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Invalid or expired verification code.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center items-center p-4">
      {step === 'form' && (
      <div className="w-full max-w-md bg-white rounded-2xl shadow-xl border border-gray-100 p-8 animate-in fade-in zoom-in duration-300">
        <div className="text-center mb-8">
          <div className="mx-auto w-12 h-12 bg-blue-600 rounded-xl flex items-center justify-center mb-4 shadow-sm">
            <UserPlus className="w-6 h-6 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900 tracking-tight">
            Create an Account
          </h1>
          <p className="text-sm text-gray-500 mt-2">
            Join today to curate your personalized news feed
          </p>
        </div>

        {error && (
          <div className="mb-6 p-4 rounded-lg bg-red-50 border border-red-100 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 mt-0.5 flex-shrink-0" />
            <p className="text-sm text-red-800 font-medium">{error}</p>
          </div>
        )}

        <form onSubmit={handleRegister} className="space-y-5">
          <div>
            <label
              htmlFor="username"
              className="block text-sm font-semibold text-gray-700 mb-2"
            >
              Username
            </label>
            <input
              id="username"
              name="username"
              type="text"
              required
              placeholder="e.g. newsjunkie99"
              value={formData.username}
              onChange={handleChange}
              className="w-full px-4 py-3 rounded-xl border border-gray-200 bg-gray-50 text-gray-900 
                focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent 
                transition-all duration-200 shadow-sm"
            />
          </div>

          <div>
            <label
              htmlFor="email"
              className="block text-sm font-semibold text-gray-700 mb-2"
            >
              Email Address
            </label>
            <input
              id="email"
              name="email"
              type="email"
              required
              placeholder="you@example.com"
              value={formData.email}
              onChange={handleChange}
              className="w-full px-4 py-3 rounded-xl border border-gray-200 bg-gray-50 text-gray-900 
                focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent 
                transition-all duration-200 shadow-sm"
            />
          </div>

          <div>
            <label
              htmlFor="password"
              className="block text-sm font-semibold text-gray-700 mb-2"
            >
              Password
            </label>
            <input
              id="password"
              name="password"
              type="password"
              required
              placeholder="••••••••"
              value={formData.password}
              onChange={handleChange}
              className="w-full px-4 py-3 rounded-xl border border-gray-200 bg-gray-50 text-gray-900 
                focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent 
                transition-all duration-200 shadow-sm"
            />
          </div>

          <div>
            <label
              htmlFor="confirm_password"
              className="block text-sm font-semibold text-gray-700 mb-2"
            >
              Confirm Password
            </label>
            <input
              id="confirm_password"
              name="confirm_password"
              type="password"
              required
              placeholder="••••••••"
              value={formData.confirm_password}
              onChange={handleChange}
              className={`w-full px-4 py-3 rounded-xl border bg-gray-50 text-gray-900 focus:bg-white focus:outline-none focus:ring-2 focus:border-transparent transition-all duration-200 shadow-sm ${
                formData.confirm_password && formData.password !== formData.confirm_password
                  ? 'border-red-400 focus:ring-red-500 bg-red-50'
                  : 'border-gray-200 focus:ring-blue-500'
              }`}
            />
            {formData.confirm_password && formData.password !== formData.confirm_password && (
              <p className="text-xs text-red-600 mt-2 font-medium">Passwords do not match</p>
            )}
          </div>

          <button
            type="submit"
            disabled={loading || (formData.confirm_password && formData.password !== formData.confirm_password)}
            className="w-full bg-blue-600 text-white font-semibold rounded-xl py-3 px-4 
              hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
              transition-all duration-200 shadow-md flex items-center justify-center gap-2
              disabled:opacity-70 disabled:cursor-not-allowed mt-2"
          >
            {loading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              "Sign Up"
            )}
          </button>
        </form>

        <div className="mt-8 text-center animate-in fade-in zoom-in duration-300">
          <p className="text-sm text-gray-600">
            Already have an account?{" "}
            <Link
              to="/login"
              className="text-blue-600 font-semibold hover:text-blue-700 hover:underline transition-all"
            >
              Log in instead
            </Link>
          </p>
        </div>
      </div>
      )}

      {step === 'otp' && (
        <div className="w-full max-w-md bg-white rounded-2xl shadow-xl border border-gray-100 p-8 animate-in fade-in zoom-in duration-300">
          <div className="text-center mb-8">
            <div className="mx-auto w-12 h-12 bg-green-600 rounded-xl flex items-center justify-center mb-4 shadow-sm">
              <MailCheck className="w-6 h-6 text-white" />
            </div>
            <h1 className="text-2xl font-bold text-gray-900 tracking-tight">
              Verify your email
            </h1>
            <p className="text-sm text-gray-500 mt-2">
              We've sent a 6-digit verification code to <br/>
              <span className="font-bold text-gray-800">{registeredEmail}</span>
            </p>
          </div>

          {error && (
            <div className="mb-6 p-4 rounded-lg bg-red-50 border border-red-100 flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 mt-0.5 flex-shrink-0" />
              <p className="text-sm text-red-800 font-medium">{error}</p>
            </div>
          )}

          <form onSubmit={handleVerify} className="space-y-6">
            <div>
              <label htmlFor="otp" className="sr-only">Verification Code</label>
              <input
                id="otp"
                type="text"
                required
                maxLength={6}
                placeholder="000000"
                value={otp}
                onChange={(e) => setOtp(e.target.value.replace(/\D/g, ''))} // only numbers
                className="w-full px-4 py-4 rounded-xl border border-gray-300 bg-gray-50 text-gray-900 
                  text-center text-3xl tracking-[0.5em] font-mono leading-none
                  focus:bg-white focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent 
                  transition-all duration-200 shadow-sm"
              />
            </div>
            
            <button
              type="submit"
              disabled={loading || otp.length !== 6}
              className="w-full bg-green-600 text-white font-semibold rounded-xl py-3 px-4 
                hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2
                transition-all duration-200 shadow-md flex items-center justify-center gap-2
                disabled:opacity-70 disabled:cursor-not-allowed mt-2"
            >
              {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : (
                <>
                  <ShieldCheck className="w-5 h-5" />
                  Verify Account
                </>
              )}
            </button>
          </form>
        </div>
      )}
    </div>
  );
};

export default Register;
