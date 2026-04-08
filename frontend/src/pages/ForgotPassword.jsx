import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Mail, Key, Lock, Loader2, AlertCircle, CheckCircle2, ChevronLeft } from "lucide-react";
import api from "../utils/api";

const ForgotPassword = () => {
  const navigate = useNavigate();
  const [step, setStep] = useState(1); // 1: Request OTP, 2: Reset Password
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  const [email, setEmail] = useState("");
  const [otp, setOtp] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const handleRequestOTP = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await api.post("/auth/forgot-password", { email });
      if (response.data.ok) {
        setStep(2);
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to send reset code. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleResetPassword = async (e) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await api.post("/auth/reset-password", {
        email,
        otp,
        new_password: newPassword,
      });

      if (response.data.ok) {
        setSuccess(true);
        setTimeout(() => {
          navigate("/login");
        }, 3000);
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to reset password. Check your code.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-center items-center p-4">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-xl border border-slate-100 p-8">
        
        {/* Step 1: Request Reset Code */}
        {step === 1 && !success && (
          <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="text-center mb-8">
              <div className="mx-auto w-12 h-12 bg-blue-600 rounded-xl flex items-center justify-center mb-4 shadow-sm">
                <Key className="w-6 h-6 text-white" />
              </div>
              <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
                Forgot Password?
              </h1>
              <p className="text-sm text-slate-500 mt-2">
                Enter your email address and we'll send you a 6-digit code to reset your password.
              </p>
            </div>

            {error && (
              <div className="mb-6 p-4 rounded-lg bg-red-50 border border-red-100 flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-red-600 mt-0.5 flex-shrink-0" />
                <p className="text-sm text-red-800 font-medium">{error}</p>
              </div>
            )}

            <form onSubmit={handleRequestOTP} className="space-y-5">
              <div>
                <label htmlFor="email" className="block text-sm font-semibold text-slate-700 mb-2">
                  Email Address
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                  <input
                    id="email"
                    type="email"
                    required
                    placeholder="you@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full pl-10 pr-4 py-3 rounded-xl border border-slate-200 bg-slate-50 text-slate-900 
                      focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent 
                      transition-all duration-200"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-blue-600 text-white font-semibold rounded-xl py-3 px-4 
                  hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
                  transition-all duration-200 shadow-md flex items-center justify-center gap-2
                  disabled:opacity-70 disabled:cursor-not-allowed"
              >
                {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : "Send Reset Link"}
              </button>
            </form>

            <div className="mt-8 text-center">
              <Link
                to="/login"
                className="text-sm font-semibold text-slate-500 hover:text-blue-600 flex items-center justify-center gap-1 transition-colors"
              >
                <ChevronLeft className="w-4 h-4" />
                Back to Login
              </Link>
            </div>
          </div>
        )}

        {/* Step 2: Reset Password */}
        {step === 2 && !success && (
          <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="text-center mb-8">
              <div className="mx-auto w-12 h-12 bg-blue-600 rounded-xl flex items-center justify-center mb-4 shadow-sm">
                <Lock className="w-6 h-6 text-white" />
              </div>
              <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
                Reset Password
              </h1>
              <p className="text-sm text-slate-500 mt-2">
                Verification code sent to <span className="font-semibold text-slate-900">{email}</span>
              </p>
            </div>

            {error && (
              <div className="mb-6 p-4 rounded-lg bg-red-50 border border-red-100 flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-red-600 mt-0.5 flex-shrink-0" />
                <p className="text-sm text-red-800 font-medium">{error}</p>
              </div>
            )}

            <form onSubmit={handleResetPassword} className="space-y-5">
              <div>
                <label htmlFor="otp" className="block text-sm font-semibold text-slate-700 mb-2">
                  6-Digit Code
                </label>
                <input
                  id="otp"
                  type="text"
                  required
                  placeholder="000000"
                  maxLength={6}
                  value={otp}
                  onChange={(e) => setOtp(e.target.value.replace(/\D/g, ""))}
                  className="w-full px-4 py-3 rounded-xl border border-slate-200 bg-slate-50 text-slate-900 
                    text-center text-2xl tracking-[0.5em] font-mono
                    focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent 
                    transition-all duration-200"
                />
              </div>

              <div>
                <label htmlFor="newPassword" className="block text-sm font-semibold text-slate-700 mb-2">
                  New Password
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                  <input
                    id="newPassword"
                    type="password"
                    required
                    placeholder="••••••••"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    className="w-full pl-10 pr-4 py-3 rounded-xl border border-slate-200 bg-slate-50 text-slate-900 
                      focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent 
                      transition-all duration-200"
                  />
                </div>
              </div>

              <div>
                <label htmlFor="confirmPassword" className="block text-sm font-semibold text-slate-700 mb-2">
                  Confirm New Password
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                  <input
                    id="confirmPassword"
                    type="password"
                    required
                    placeholder="••••••••"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className={`w-full pl-10 pr-4 py-3 rounded-xl border text-slate-900 focus:bg-white focus:outline-none focus:ring-2 transition-all duration-200 ${
                      confirmPassword && newPassword !== confirmPassword
                        ? "border-red-400 focus:ring-red-500 bg-red-50"
                        : "border-slate-200 focus:ring-blue-500 bg-slate-50"
                    }`}
                  />
                </div>
                {confirmPassword && newPassword !== confirmPassword && (
                  <p className="text-xs text-red-600 mt-2 font-medium">Passwords do not match</p>
                )}
              </div>

              <button
                type="submit"
                disabled={loading || (confirmPassword && newPassword !== confirmPassword)}
                className="w-full bg-blue-600 text-white font-semibold rounded-xl py-3 px-4 
                  hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
                  transition-all duration-200 shadow-md flex items-center justify-center gap-2
                  disabled:opacity-70 disabled:cursor-not-allowed"
              >
                {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : "Reset Password"}
              </button>

              <button
                type="button"
                onClick={() => setStep(1)}
                className="w-full text-sm font-semibold text-slate-500 hover:text-blue-600 transition-colors py-1"
              >
                Resend code
              </button>
            </form>
          </div>
        )}

        {/* Success State */}
        {success && (
          <div className="text-center animate-in fade-in zoom-in duration-500 py-4">
            <div className="mx-auto w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-6">
              <CheckCircle2 className="w-10 h-10 text-green-600" />
            </div>
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight mb-2">
              Password Reset!
            </h1>
            <p className="text-slate-500 mb-8">
              Your password has been changed successfully. Redirecting you to the login page...
            </p>
            <div className="w-full bg-slate-100 h-1 rounded-full overflow-hidden">
              <div className="bg-green-600 h-full animate-progress-fast" />
            </div>
          </div>
        )}

      </div>
    </div>
  );
};

export default ForgotPassword;
